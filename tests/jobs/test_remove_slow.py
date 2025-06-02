from unittest.mock import MagicMock, AsyncMock
import pytest

from tests.jobs.utils import shared_fix_affected_items
from src.jobs.remove_slow import RemoveSlow


# pylint: disable=W0212
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("item", "expected_result"),
    [
        (
            # Valid: has downloadId, size, sizeleft, and status = "downloading"
            {
                "downloadId": "abc",
                "size": 1000,
                "sizeleft": 500,
                "status": "downloading",
                "protocol": "torrent",
                "download_client": AsyncMock(),
                "download_client_type": "qBittorrent",
            },
            True,
        ),
        (
            # Invalid: missing one
            {
                "downloadId": "abc",
                "size": 1000,
                "sizeleft": 500,
                "status": "downloading",
                "protocol": "torrent",
                "download_client": AsyncMock(),
            },
            False,
        ),
        (
            # Invalid: missing multiple
            {
                "size": 1000,
                "sizeleft": 500,
            },
            False,
        ),
    ],
)
async def test_check_required_keys(item, expected_result):
    removal_job = shared_fix_affected_items(RemoveSlow)
    result = removal_job._check_required_keys(item)
    assert result == expected_result


@pytest.mark.parametrize(
    ("item", "expected_result"),
    [
        ({"protocol": "usenet"}, True),
        ({"protocol": "torrent"}, False),
        ({}, False),
    ],
)
def test_is_usenet(item, expected_result):
    removal_job = shared_fix_affected_items(RemoveSlow)
    result = removal_job._is_usenet(item)
    assert result == expected_result


@pytest.mark.parametrize(
    ("item", "expected_result"),
    [
        ({"status": "downloading", "size": 1000, "sizeleft": 0}, True),
        ({"status": "completed", "size": 1000, "sizeleft": 0}, False),
        ({"status": "downloading", "size": 0, "sizeleft": 0}, False),
    ],
)
def test_is_completed_but_stuck(item, expected_result):
    removal_job = shared_fix_affected_items(RemoveSlow)
    result = removal_job._is_completed_but_stuck(item)
    assert result == expected_result


@pytest.mark.parametrize(
    ("speed", "expected_result"),
    [
        (None, False),  # speed is None -> not slow
        (0, True),  # speed less than min_speed -> slow (assuming min_speed > 0)
        (5, True),  # speed less than min_speed
        (10, False),  # speed equal or above min_speed (assuming min_speed=10)
        (15, False),  # speed above min_speed
    ],
)
def test_is_slow(speed, expected_result):
    removal_job = shared_fix_affected_items(RemoveSlow)
    removal_job.job.min_speed = 10
    result = removal_job._is_slow(speed)
    assert result == expected_result


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "client_type, expected_progress",
    [
        ("something_else", 100),
        (
            "qbittorrent",
            800,
        ),  # qbit is more updated, has progressed from 100 to 800 since arr refreshed last
    ],
)
async def test_get_download_progress(client_type, expected_progress):
    mock_client = AsyncMock()
    mock_client.fetch_download_progress.return_value = 800

    item = {
        "download_client_type": client_type,
        "download_client": mock_client,
        "size": 1000,
        "sizeleft": 900,
    }

    removal_job = shared_fix_affected_items(RemoveSlow)
    result = await removal_job._get_download_progress(item, "some_id")

    assert result == expected_progress


@pytest.mark.parametrize(
    "download_id, tracker_data, current_progress, expected",
    [
        (
            "id1",
            {"id1": 10_000_000},  # previous_progress = 10 MB
            16_000_000,  # current_progress = 16 MB
            (10_000_000, 6_000_000, 100),  # 6 MB in 1 min => 100 MB/h
        ),  # increment case
        ("id2", {}, 800, (None, None, None)),  # no previous_progress
    ],
)
def test_compute_increment_and_speed(
    download_id, tracker_data, current_progress, expected
):
    removal_job = shared_fix_affected_items(RemoveSlow)
    removal_job.arr.tracker.download_progress = tracker_data
    removal_job.settings.general.timer = 1  # 1 minute interval

    result = removal_job._compute_increment_and_speed(download_id, current_progress)
    assert result == expected


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "item, previous_progress, mock_progress, expected_increment, expected_speed",
    [
        (
            {"downloadId": "id1"},
            1_000_000,
            1_600_000,
            600_000,
            10.0,
        ),
        (
            {"downloadId": "id2"},
            None,
            800_000,
            None,
            None,
        ),
    ],
)
async def test_get_progress_stats(
    item, previous_progress, mock_progress, expected_increment, expected_speed
):
    """
    Test `_get_progress_stats` to ensure it correctly returns the current progress,
    previous progress, increment, and calculated speed. It also verifies that the
    download progress is updated in the tracker after execution.

    - If a previous progress value exists in the tracker, the increment and speed
    are calculated.
    - If no previous value exists, increment and speed should be None.
    """
    removal_job = shared_fix_affected_items(RemoveSlow)

    # Ensure tracker dict is initialized properly
    removal_job.arr.tracker.download_progress = {}

    download_id = item["downloadId"]
    if previous_progress is not None:
        removal_job.arr.tracker.download_progress[download_id] = previous_progress

    # Mock _get_download_progress to return a high fixed value
    removal_job._get_download_progress = AsyncMock(return_value=mock_progress)
    removal_job.settings.general.timer = 1  # 1-minute interval

    result = await removal_job._get_progress_stats(item)

    expected = (
        mock_progress,
        previous_progress,
        expected_increment,
        expected_speed,
    )
    assert result == expected
    assert removal_job.arr.tracker.download_progress[download_id] == mock_progress


@pytest.mark.parametrize(
    "download_client_type, bandwidth_usage, expected",
    [
        ("qbittorrent", 0.81, True),  # above threshold 0.8
        ("qbittorrent", 0.8, False),  # equal to threshold 0.8
        ("qbittorrent", 0.79, False),  # below threshold 0.8
        ("other_client", 0.9, False),  # different client type
    ],
)
def test_high_bandwidth_usage(download_client_type, bandwidth_usage, expected):
    """
    Test RemoveSlow._high_bandwidth_usage method.

    Checks if the method correctly identifies high bandwidth usage
    only when the download client type is 'qbittorrent' and the
    bandwidth usage exceeds the defined threshold (0.8).
    For other client types or bandwidth usage below or equal to threshold,
    it should return False.
    """

    class DummyClient:
        def __init__(self, usage):
            self.bandwidth_usage = usage

    download_client = DummyClient(bandwidth_usage)
    result = RemoveSlow._high_bandwidth_usage(download_client, download_client_type)
    assert result == expected


@pytest.mark.asyncio
async def test_add_download_client_to_queue_items_simple():
    """
    Test that 'add_download_client_to_queue_items' correctly adds
    the download client object and its type to each queue item,
    based on the client's name retrieved from settings.
    """
    removal_job = shared_fix_affected_items(RemoveSlow)
    client_name = "MyQbitInstance"
    download_client_type = "qbittorrent"
    removal_job.queue = [{"downloadClient": client_name}]

    dummy_client = MagicMock(name="QBClient")
    removal_job.settings.download_clients = MagicMock()
    removal_job.settings.download_clients.get_download_client_by_name = MagicMock(
        return_value=(dummy_client, download_client_type)
    )

    await removal_job.add_download_client_to_queue_items()

    item = removal_job.queue[0]
    assert item["download_client"] == dummy_client
    assert item["download_client_type"] == download_client_type



@pytest.mark.asyncio
async def test_update_bandwidth_usage_calls_once_per_client():
    """
    Test that 'update_bandwidth_usage' calls 'set_bandwidth_usage' exactly once
    per unique download client of type 'qbittorrent' in the queue,
    and does not call it for other client types.
    """
    removal_job = shared_fix_affected_items(RemoveSlow)

    # Create two dummy clients
    qb_client1 = MagicMock(name="QBClient1")
    qb_client1.set_bandwidth_usage = AsyncMock()
    qb_client2 = MagicMock(name="QBClient2")
    qb_client2.set_bandwidth_usage = AsyncMock()
    other_client = MagicMock(name="OtherClient")
    other_client.set_bandwidth_usage = AsyncMock()

    removal_job.queue = [
        {"download_client": qb_client1, "download_client_type": "qbittorrent"},
        {
            "download_client": qb_client1,
            "download_client_type": "qbittorrent",
        },  # duplicate client
        {"download_client": qb_client2, "download_client_type": "qbittorrent"},
        {"download_client": other_client, "download_client_type": "other"},
    ]

    await removal_job.update_bandwidth_usage()

    # Verify set_bandwidth_usage called once per unique qbittorrent client
    qb_client1.set_bandwidth_usage.assert_awaited_once()
    qb_client2.set_bandwidth_usage.assert_awaited_once()
    # Verify other client method was not called
    other_client.set_bandwidth_usage.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "queue_item, should_be_affected",
    [
        # Keys not present -> skip
        ({"downloadClient": "client1"}, False),

        # Already checked downloadId -> skip (simulate by repeating downloadId)
        ({"downloadId": "checked_before", "download_client": MagicMock(), "download_client_type": "qbittorrent"}, False),

        # Is Usenet -> skip
        ({"downloadId": "usenet", "download_client": MagicMock(), "download_client_type": "qbittorrent"}, False),

        # Completed but stuck -> skip
        ({"downloadId": "stuck", "download_client": MagicMock(), "download_client_type": "qbittorrent"}, False),

        # High bandwidth usage -> skip
        ({"downloadId": "highbw", "download_client": MagicMock(), "download_client_type": "qbittorrent"}, False),

        # Not slow -> skip
        ({"downloadId": "notslow", "download_client": MagicMock(), "download_client_type": "qbittorrent"}, False),

        # None of above, should be affected
        ({"downloadId": "good", "title": "Good Item", "download_client": MagicMock(), "download_client_type": "qbittorrent"}, True),
    ],
)
async def test_find_affected_items_simple(queue_item, should_be_affected):
    # Add minimum fields required
    queue_item["title"] = queue_item.get("downloadId", "dummy")
    removal_job = shared_fix_affected_items(RemoveSlow, queue_data=[queue_item])

    # Setup queue differently based on test case
    if queue_item.get("downloadId") == "dup":
        # Add duplicate entries to test skipping by checked_ids
        removal_job.queue = [queue_item, queue_item]
    else:
        removal_job.queue = [queue_item]

    # Mock methods
    removal_job._check_required_keys = MagicMock(return_value="downloadId" in queue_item)
    removal_job._is_usenet = MagicMock(return_value=queue_item.get("downloadId") == "usenet")
    removal_job._is_completed_but_stuck = MagicMock(return_value=queue_item.get("downloadId") == "stuck")
    removal_job._high_bandwidth_usage = MagicMock(return_value=queue_item.get("downloadId") == "highbw")
    removal_job._get_progress_stats = AsyncMock(return_value=(1000, 900, 100, 10))  # arbitrary numbers
    removal_job._is_slow = MagicMock(return_value=queue_item.get("downloadId") == "good")

    # Mock add_download_client_to_queue_items and update_bandwidth_usage as no-ops
    removal_job.add_download_client_to_queue_items = AsyncMock()
    removal_job.update_bandwidth_usage = AsyncMock()

    # Run the method under test
    affected_items = await removal_job._find_affected_items()

    if should_be_affected:
        assert affected_items, f"Item {queue_item.get('downloadId')} should be affected"
        assert affected_items[0]["downloadId"] == queue_item["downloadId"]
    else:
        assert not affected_items, f"Item {queue_item.get('downloadId')} should NOT be affected"
