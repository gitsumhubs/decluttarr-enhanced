from unittest.mock import AsyncMock, MagicMock

import pytest

from src.jobs.remove_unmonitored import RemoveUnmonitored
from tests.jobs.test_utils import removal_job_fix


@pytest.fixture(name="arr")
def fixture_arr():
    mock = MagicMock()
    mock.is_monitored = AsyncMock()
    return mock


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("queue_data", "monitored_ids", "expected_download_ids"),
    [
        # All items monitored -> no affected items
        (
            [
                {"downloadId": "1", "detail_item_id": 101},
                {"downloadId": "2", "detail_item_id": 102},
            ],
            {101: True, 102: True},
            [],
        ),
        # All items unmonitored -> all affected
        (
            [
                {"downloadId": "1", "detail_item_id": 101},
                {"downloadId": "2", "detail_item_id": 102},
            ],
            {101: False, 102: False},
            ["1", "2"],
        ),
        # One monitored, one not
        (
            [
                {"downloadId": "1", "detail_item_id": 101},
                {"downloadId": "2", "detail_item_id": 102},
            ],
            {101: True, 102: False},
            ["2"],
        ),
        # Shared downloadId, only one monitored -> not affected
        (
            [
                {"downloadId": "1", "detail_item_id": 101},
                {"downloadId": "1", "detail_item_id": 102},
            ],
            {101: False, 102: True},
            [],
        ),
        # Shared downloadId, none monitored -> affected
        (
            [
                {"downloadId": "1", "detail_item_id": 101},
                {"downloadId": "1", "detail_item_id": 102},
            ],
            {101: False, 102: False},
            ["1", "1"],
        ),
    ],
)
async def test_find_affected_items(queue_data, monitored_ids, expected_download_ids, arr):
    # Patch arr mock with side_effect
    async def mock_is_monitored(detail_item_id):
        return monitored_ids[detail_item_id]

    arr.is_monitored = AsyncMock(side_effect=mock_is_monitored)
    # Arrange
    removal_job = removal_job_fix(RemoveUnmonitored, queue_data=queue_data)
    removal_job.arr = arr  # Inject the mocked arr object

    # Act
    affected_items = await removal_job._find_affected_items()  # pylint: disable=W0212

    # Assert
    affected_download_ids = [item["downloadId"] for item in affected_items]
    assert affected_download_ids == expected_download_ids, \
        f"Expected downloadIds {expected_download_ids}, got {affected_download_ids}"
