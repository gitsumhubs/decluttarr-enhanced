from unittest.mock import MagicMock
import pytest

from tests.jobs.utils import shared_fix_affected_items, shared_test_affected_items
from src.jobs.remove_slow import RemoveSlow


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
            },
            True,
        ),
        (
            # Invalid: missing sizeleft
            {
                "downloadId": "abc",
                "size": 1000,
                "status": "downloading",
                "protocol": "torrent",
            },
            False,
        ),
        (
            # Invalid: missing size
            {
                "downloadId": "abc",
                "sizeleft": 500,
                "status": "downloading",
                "protocol": "torrent",
            },
            False,
        ),
        (
            # Invalid: missing status
            {"downloadId": "abc", "size": 1000, "sizeleft": 500, "protocol": "torrent"},
            False,
        ),
        (
            # Invalid: missing protocol
            {
                "downloadId": "abc",
                "size": 1000,
                "sizeleft": 500,
                "status": "downloading",
            },
            False,
        ),
    ],
)
async def test_is_valid_item(item, expected_result):
    # Arrange
    removal_job = shared_fix_affected_items(RemoveSlow)

    # Act
    result = removal_job._is_valid_item(item)  # pylint: disable=W0212

    # Assert
    assert result == expected_result


@pytest.fixture(name="queue_data")
def fixture_queue_data():
    return [
        {
            "downloadId": "usenet",
            "progress_previous": 800,  # previous progress
            "progress_now": 800,  # current progress
            "total_size": 1000,
            "protocol": "usenet",  # should be ignored
        },
        {
            "downloadId": "importing",
            "progress_previous": 0,
            "progress_now": 1000,
            "total_size": 1000,
            "protocol": "torrent",
        },
        {
            "downloadId": "stuck",
            "progress_previous": 200,
            "progress_now": 200,
            "total_size": 1000,
            "protocol": "torrent",
        },
        {
            "downloadId": "slow",
            "progress_previous": 100,
            "progress_now": 150,
            "total_size": 1000,
            "protocol": "torrent",
        },
        {
            "downloadId": "medium",
            "progress_previous": 500,
            "progress_now": 900,
            "total_size": 1000,
            "protocol": "torrent",
        },
        {
            "downloadId": "fast",
            "progress_previous": 100,
            "progress_now": 900,
            "total_size": 1000,
            "protocol": "torrent",
        },
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("min_speed", "expected_download_ids"),
    [
        (0, []),  # No min download speed; all torrents pass
        (500, ["stuck"]),  # Only stuck and slow are included
        (1000, ["stuck", "slow"]),  # Same as above
        (10000, ["stuck", "slow", "medium"]),  # Only stuck and slow are below 5.0
        (1000000, ["stuck", "slow", "medium", "fast"]),  # Fast torrent included (but not importing)
    ],
)
async def test_find_affected_items_with_varied_speeds(
    queue_data, min_speed, expected_download_ids,
):
    # Arrange
    removal_job = shared_fix_affected_items(RemoveSlow, queue_data)

    # Job-specific arrangements
    removal_job.job = MagicMock()
    removal_job.job.min_speed = min_speed
    removal_job.settings = MagicMock()
    removal_job.settings.general.timer = 1

    removal_job._is_valid_item = MagicMock(return_value=True)  # Mock the _is_valid_item method to always return True # pylint: disable=W0212

    # Inject size and sizeleft into each item in the queue
    for item in queue_data:
        item["size"] = item["total_size"] * 1000000  # Inject total size as 'size'
        item["sizeleft"] = item["size"] - item["progress_now"] * 1000000  # Calculate sizeleft
        item["status"] = "downloading"
        item["title"] = item["downloadId"]

    # Mock the download progress in `arr.tracker.download_progress`
    removal_job.arr.tracker.download_progress = {
        item["downloadId"]: item["progress_previous"] * 1000000
        for item in queue_data
    }

    # Act
    await shared_test_affected_items(removal_job, expected_download_ids)
