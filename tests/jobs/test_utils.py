# test_utils.py
from unittest.mock import AsyncMock, patch


def mock_class_init(cls, *args, **kwargs):
    """Mock the __init__ method of a class to bypass constructor logic."""
    with patch.object(cls, "__init__", lambda x, *args, **kwargs: None):
        return cls(*args, **kwargs)


def removal_job_fix(cls, queue_data=None, settings=None):
    """
    Mock the initialization of Jobs and the queue_manager attribute.

    Args:
        cls: The class to instantiate (e.g., RemoveOrphans).
        queue_data: The mock data for the get_queue_items method (default: None).
        settings: The mock data for the settings (default: None).

    Returns:
        instance: An instance of the class with a mocked queue_manager.

    """
    # Mock the initialization of the class (no need to pass arr, settings, job_name)
    instance = mock_class_init(cls, arr=None, settings=settings, job_name="Test Job")

    # Mock the queue_manager and its get_queue_items method
    instance.queue_manager = AsyncMock()
    instance.queue_manager.get_queue_items.return_value = queue_data

    return instance
