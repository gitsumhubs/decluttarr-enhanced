import pytest

from src.jobs.remove_failed_downloads import RemoveFailedDownloads
from tests.jobs.test_utils import removal_job_fix


# Test to check if items with "failed" status are included in affected items with parameterized data
@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("queue_data", "expected_download_ids"),
    [
        (
            [
                {"downloadId": "1", "status": "failed"},  # Item with failed status
                {"downloadId": "2", "status": "completed"},  # Item with completed status
                {"downloadId": "3"},  # No status field
            ],
            ["1"],  # Only the failed item should be affected
        ),
        (
            [
                {"downloadId": "1", "status": "completed"},  # Item with completed status
                {"downloadId": "2", "status": "completed"},
                {"downloadId": "3", "status": "completed"},
            ],
            [],  # No failed items, so no affected items
        ),
        (
            [
                {"downloadId": "1", "status": "failed"},  # Item with failed status
                {"downloadId": "2", "status": "failed"},
            ],
            ["1", "2"],  # Both failed items should be affected
        ),
    ],
)
async def test_find_affected_items(queue_data, expected_download_ids):
    # Arrange
    removal_job = removal_job_fix(RemoveFailedDownloads, queue_data=queue_data)

    # Act
    affected_items = await removal_job._find_affected_items()   # pylint: disable=W0212

    # Assert
    assert isinstance(affected_items, list)

    # Assert that the affected items match the expected download IDs
    affected_download_ids = [item["downloadId"] for item in affected_items]
    assert sorted(affected_download_ids) == sorted(expected_download_ids), \
        f"Expected affected items with downloadIds {expected_download_ids}, got {affected_download_ids}"
