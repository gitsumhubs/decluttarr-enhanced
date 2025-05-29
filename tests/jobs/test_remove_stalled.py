from unittest.mock import AsyncMock
import pytest
from src.jobs.remove_stalled import RemoveStalled

# Test to check if items with the specific error message are included in affected items with parameterized data
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "queue_data, expected_download_ids",
    [
        (
            [
                {"downloadId": "1", "status": "warning", "errorMessage": "The download is stalled with no connections"},  # Valid item
                {"downloadId": "2", "status": "completed", "errorMessage": "The download is stalled with no connections"},  # Wrong status
                {"downloadId": "3", "status": "warning", "errorMessage": "Some other error"}  # Incorrect errorMessage
            ],
            ["1"]  # Only the item with "warning" status and the correct errorMessage should be affected
        ),
        (
            [
                {"downloadId": "1", "status": "warning", "errorMessage": "Some other error"},  # Incorrect errorMessage
                {"downloadId": "2", "status": "completed", "errorMessage": "The download is stalled with no connections"},  # Wrong status
                {"downloadId": "3", "status": "warning", "errorMessage": "The download is stalled with no connections"}  # Correct item
            ],
            ["3"]  # Only the item with "warning" status and the correct errorMessage should be affected
        ),
        (
            [
                {"downloadId": "1", "status": "warning", "errorMessage": "The download is stalled with no connections"},  # Valid item
                {"downloadId": "2", "status": "warning", "errorMessage": "The download is stalled with no connections"}  # Another valid item
            ],
            ["1", "2"]  # Both items match the condition
        ),
        (
            [
                {"downloadId": "1", "status": "completed", "errorMessage": "The download is stalled with no connections"},  # Wrong status
                {"downloadId": "2", "status": "warning", "errorMessage": "Some other error"}  # Incorrect errorMessage
            ],
            []  # No items match the condition
        )
    ]
)
async def test_find_affected_items(queue_data, expected_download_ids):
    # Arrange
    removal_job = RemoveStalled(arr=AsyncMock(), settings=AsyncMock(),job_name="test")
    removal_job.queue = queue_data

    # Act
    affected_items = await removal_job._find_affected_items()   # pylint: disable=W0212

    # Assert
    assert isinstance(affected_items, list)

    # Assert that the affected items match the expected download IDs
    affected_download_ids = [item["downloadId"] for item in affected_items]
    assert sorted(affected_download_ids) == sorted(expected_download_ids), \
        f"Expected affected items with downloadIds {expected_download_ids}, got {affected_download_ids}"
