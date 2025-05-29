from unittest.mock import AsyncMock, MagicMock
import pytest
from src.jobs.remove_unmonitored import RemoveUnmonitored

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "queue_data, monitored_ids, expected_download_ids",
    [
        # All items monitored -> no affected items
        (
            [
                {"downloadId": "1", "detail_item_id": 101},
                {"downloadId": "2", "detail_item_id": 102}
            ],
            {101: True, 102: True},
            []
        ),
        # All items unmonitored -> all affected
        (
            [
                {"downloadId": "1", "detail_item_id": 101},
                {"downloadId": "2", "detail_item_id": 102}
            ],
            {101: False, 102: False},
            ["1", "2"]
        ),
        # One monitored, one not
        (
            [
                {"downloadId": "1", "detail_item_id": 101},
                {"downloadId": "2", "detail_item_id": 102}
            ],
            {101: True, 102: False},
            ["2"]
        ),
        # Shared downloadId, only one monitored -> not affected
        (
            [
                {"downloadId": "1", "detail_item_id": 101},
                {"downloadId": "1", "detail_item_id": 102}
            ],
            {101: False, 102: True},
            []
        ),
        # Shared downloadId, none monitored -> affected
        (
            [
                {"downloadId": "1", "detail_item_id": 101},
                {"downloadId": "1", "detail_item_id": 102}
            ],
            {101: False, 102: False},
            ["1", "1"]
        ),
    ]
)
async def test_find_affected_items(queue_data, monitored_ids, expected_download_ids):
    # Arrange
    arr = MagicMock()
    arr.is_monitored = AsyncMock(side_effect=lambda id_: monitored_ids[id_])
    
    removal_job = RemoveUnmonitored(arr=arr, settings=MagicMock(), job_name="test")
    removal_job.queue = queue_data

    # Act
    affected_items = await removal_job._find_affected_items()  # pylint: disable=W0212

    # Assert
    affected_download_ids = [item["downloadId"] for item in affected_items]
    assert affected_download_ids == expected_download_ids, \
        f"Expected downloadIds {expected_download_ids}, got {affected_download_ids}"