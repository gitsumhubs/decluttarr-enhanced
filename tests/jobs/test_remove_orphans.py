import pytest
from src.jobs.remove_orphans import RemoveOrphans
from tests.jobs.test_utils import removal_job_fix

@pytest.fixture(name="queue_data")
def fixture_queue_data():
    return [
        {
            "downloadId": "AABBCC",
            "id": 1,
            "title": "My Series A - Season 1",
            "size": 1000,
            "sizeleft": 500,
            "downloadClient": "qBittorrent",
            "protocol": "torrent",
            "status": "paused",
            "trackedDownloadState": "downloading",
            "statusMessages": [],
        },
        {
            "downloadId": "112233",
            "id": 2,
            "title": "My Series B - Season 1",
            "size": 1000,
            "sizeleft": 500,
            "downloadClient": "qBittorrent",
            "protocol": "torrent",
            "status": "paused",
            "trackedDownloadState": "downloading",
            "statusMessages": [],
        }
    ]

@pytest.mark.asyncio
async def test_find_affected_items_returns_queue(queue_data):
    # Fix
    removal_job = removal_job_fix(RemoveOrphans, queue_data=queue_data)
    removal_job.queue = queue_data

    # Act
    affected_items = await removal_job._find_affected_items()   # pylint: disable=W0212

    # Assert
    assert isinstance(affected_items, list)
    assert len(affected_items) == 2
    assert affected_items[0]["downloadId"] == "AABBCC"
    assert affected_items[1]["downloadId"] == "112233"
