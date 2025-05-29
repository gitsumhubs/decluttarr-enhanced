import pytest

# Assuming your method is part of a class called QueueManager
from src.utils.queue_manager import QueueManager
from unittest.mock import Mock

# ---------- Fixtures ----------
@pytest.fixture(name="mock_queue_manager")
def mock_queue_manager():
    mock_arr = Mock()
    mock_settings = Mock()
    return QueueManager(arr=mock_arr, settings=mock_settings)

# ---------- Tests ----------
def test_format_queue_empty(mock_queue_manager):
    result = mock_queue_manager.format_queue([])
    assert result == "empty"

def test_format_queue_single_item(mock_queue_manager):
    queue_items = [
        {
            "downloadId": "abc123",
            "title": "Example Download Title",
            "protocol": "torrent",
            "status": "queued",
            "id": 1,
        }
    ]
    expected = [{
        "downloadId": "abc123",
        "downloadTitle": "Example Download Title",
        "protocol": ["torrent"],
        "status": ["queued"],
        "IDs": [1],
    }]
    assert mock_queue_manager.format_queue(queue_items) == expected

def test_format_queue_multiple_same_download_id(mock_queue_manager):
    queue_items = [
        {
            "downloadId": "xyz789",
            "title": "Example Download Title",
            "protocol": "usenet",
            "status": "downloading",
            "id": 1,
        },
        {
            "downloadId": "xyz789",
            "title": "Example Download Title",
            "protocol": "usenet",
            "status": "downloading",
            "id": 2,
        }
    ]
    expected = [{
        "downloadId": "xyz789",
        "downloadTitle": "Example Download Title",
        "protocol": ["usenet"],
        "status": ["downloading"],
        "IDs": [1, 2],
    }]
    assert mock_queue_manager.format_queue(queue_items) == expected

def test_format_queue_multiple_different_download_ids(mock_queue_manager):
    queue_items = [
        {
            "downloadId": "aaa111",
            "title": "Example Download Title A",
            "protocol": "torrent",
            "status": "queued",
            "id": 10,
        },
        {
            "downloadId": "bbb222",
            "title": "Example Download Title B",
            "protocol": "usenet",
            "status": "completed",
            "id": 20,
        }
    ]
    expected = [
        {
            "downloadId": "aaa111",
            "downloadTitle": "Example Download Title A",
            "protocol": ["torrent"],
            "status": ["queued"],
            "IDs": [10],
        },
        {
            "downloadId": "bbb222",
            "downloadTitle": "Example Download Title B",
            "protocol": ["usenet"],
            "status": ["completed"],
            "IDs": [20],
        }
    ]
    assert mock_queue_manager.format_queue(queue_items) == expected
