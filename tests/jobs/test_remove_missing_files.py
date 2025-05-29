import pytest
from unittest.mock import MagicMock
from src.jobs.remove_missing_files import RemoveMissingFiles

@pytest.mark.asyncio
@pytest.mark.parametrize(
    "queue_data, expected_download_ids",
    [
        (
            [  # valid failed torrent (warning + matching errorMessage)
                {"downloadId": "1", "status": "warning", "errorMessage": "DownloadClientQbittorrentTorrentStateMissingFiles"},
                {"downloadId": "2", "status": "warning", "errorMessage": "The download is missing files"},
                {"downloadId": "3", "status": "warning", "errorMessage": "qBittorrent is reporting missing files"},
            ],
            ["1", "2", "3"]
        ),
        (
            [  # wrong status for errorMessage, should be ignored
                {"downloadId": "1", "status": "failed", "errorMessage": "The download is missing files"},
            ],
            []
        ),
        (
            [  # valid "completed" with matching statusMessage
                {
                    "downloadId": "1",
                    "status": "completed",
                    "statusMessages": [
                        {"messages": ["No files found are eligible for import in /some/path"]}
                    ],
                },
                {
                    "downloadId": "2",
                    "status": "completed",
                    "statusMessages": [
                        {"messages": ["Everything looks good!"]}
                    ],
                },
            ],
            ["1"]
        ),
        (
            [  # No statusMessages key or irrelevant messages
                {"downloadId": "1", "status": "completed"},
                {
                    "downloadId": "2",
                    "status": "completed",
                    "statusMessages": [{"messages": ["Other message"]}]
                },
            ],
            []
        ),
        (
            [  # Mixed: one matching warning + one matching statusMessage
                {"downloadId": "1", "status": "warning", "errorMessage": "The download is missing files"},
                {
                    "downloadId": "2",
                    "status": "completed",
                    "statusMessages": [{"messages": ["No files found are eligible for import in foo"]}]
                },
                {"downloadId": "3", "status": "completed"},
            ],
            ["1", "2"]
        ),
    ]
)
async def test_find_affected_items(queue_data, expected_download_ids):
    # Arrange
    removal_job = RemoveMissingFiles(arr=MagicMock(), settings=MagicMock(),job_name="test")
    removal_job.queue = queue_data

    # Act
    affected_items = await removal_job._find_affected_items()  # pylint: disable=W0212

    # Assert
    assert isinstance(affected_items, list)
    affected_download_ids = [item["downloadId"] for item in affected_items]
    assert sorted(affected_download_ids) == sorted(expected_download_ids), \
        f"Expected affected items with downloadIds {expected_download_ids}, got {affected_download_ids}"
