from unittest.mock import AsyncMock, patch

import pytest

from src.jobs.removal_handler import RemovalHandler

# ---------- Fixtures ----------


@pytest.fixture(name="mock_logger")
def fixture_mock_logger():
    with patch("src.jobs.removal_handler.logger") as mock:
        yield mock


@pytest.fixture(name="settings")
def fixture_settings():
    settings = AsyncMock()
    settings.general.test_run = False
    settings.general.obsolete_tag = "obsolete_tag"
    settings.download_clients.qbittorrent = [AsyncMock()]
    return settings


@pytest.fixture(name="arr")
def fixture_arr():
    arr = AsyncMock()
    arr.api_url = "https://mock-api-url"
    arr.api_key = "mock_api_key"
    arr.tracker = AsyncMock()
    arr.tracker.deleted = []
    arr.get_download_client_implementation.return_value = "QBittorrent"
    return arr


@pytest.fixture(name="affected_downloads")
def fixture_affected_downloads():
    return {
        "AABBCC": [
            {
                "id": 1,
                "downloadId": "AABBCC",
                "title": "My Series A - Season 1",
                "size": 1000,
                "sizeleft": 500,
                "downloadClient": "qBittorrent",
                "protocol": "torrent",
                "status": "paused",
                "trackedDownloadState": "downloading",
                "statusMessages": [],
            },
        ],
    }


# ---------- Parametrized Test ----------

@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("protocol", "qb_config", "client_impl", "is_private", "pub_handling", "priv_handling", "expected"),
    [
        ("emule",   [AsyncMock()], "MyDonkey",     None,  "remove", "remove", "remove"),
        ("torrent", [],            "QBittorrent",  None,  "remove", "remove", "remove"),
        ("torrent", [AsyncMock()], "OtherClient",  None,  "remove", "remove", "remove"),

        ("torrent", [AsyncMock()], "QBittorrent",  True,  "remove", "remove", "remove"),
        ("torrent", [AsyncMock()], "QBittorrent",  True,  "remove", "tag_as_obsolete", "tag_as_obsolete"),
        ("torrent", [AsyncMock()], "QBittorrent",  True,  "remove", "skip", "skip"),

        ("torrent", [AsyncMock()], "QBittorrent",  False, "remove", "remove", "remove"),
        ("torrent", [AsyncMock()], "QBittorrent",  False, "tag_as_obsolete", "remove", "tag_as_obsolete"),
        ("torrent", [AsyncMock()], "QBittorrent",  False, "skip", "remove", "skip"),
    ],
)
async def test_remove_downloads(
    protocol,
    qb_config,
    client_impl,
    is_private,
    pub_handling,
    priv_handling,
    expected,
    arr,
    settings,
    affected_downloads,
):
    # ---------- Arrange ----------
    download_id = "AABBCC"
    item = affected_downloads[download_id][0]

    item["protocol"] = protocol
    item["downloadClient"] = "qBittorrent"

    settings.download_clients.qbittorrent = qb_config
    settings.general.public_tracker_handling = pub_handling
    settings.general.private_tracker_handling = priv_handling

    arr.get_download_client_implementation.return_value = client_impl
    arr.tracker.private = [download_id] if is_private else []
    arr.tracker.deleted = []

    handler = RemovalHandler(arr=arr, settings=settings, job_name="Test Job")

    # ---------- Act ----------
    await handler.remove_downloads(affected_downloads, blocklist=True)
    observed = await handler._get_handling_method(download_id, item)

    # ---------- Assert ----------
    assert observed == expected

    if expected == "remove":
        arr.remove_queue_item.assert_awaited_once_with(
            queue_id=item["id"], blocklist=True,
        )
        assert download_id in arr.tracker.deleted

    elif expected == "tag_as_obsolete":
        if qb_config:
            qb_config[0].set_tag.assert_awaited_once_with(
                tags=[settings.general.obsolete_tag],
                hashes=[download_id],
            )
        assert download_id in arr.tracker.deleted

    elif expected == "skip":
        assert download_id not in affected_downloads
        assert download_id not in arr.tracker.deleted

    if expected != "tag_as_obsolete" and qb_config:
        qb_config[0].set_tag.assert_not_awaited()
