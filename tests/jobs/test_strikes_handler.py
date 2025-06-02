from unittest.mock import MagicMock

import pytest

from src.jobs.strikes_handler import StrikesHandler


@pytest.mark.parametrize(
    ("current_hashes", "expected_remaining_in_tracker"),
    [
        ([], []),  # nothing active → all removed
        (["HASH1", "HASH2"], ["HASH1", "HASH2"]),  # both active → none removed
        (["HASH2"], ["HASH2"]),  # only HASH2 active → HASH1 removed
    ],
)
def test_recover_downloads(current_hashes, expected_remaining_in_tracker):
    """Test if tracker correctly removes items (if recovered) and adds new ones."""
    # Fix
    tracker = MagicMock()
    tracker.defective = {
        "remove_stalled": {
            "HASH1": {"title": "Movie-with-one-strike", "strikes": 1},
            "HASH2": {"title": "Movie-with-three-strikes", "strikes": 3},
        },
    }
    arr = MagicMock()
    arr.tracker = tracker
    handler = StrikesHandler(job_name="remove_stalled", arr=arr, max_strikes=3)
    affected_downloads = [(hash_id, {"title": "dummy"}) for hash_id in current_hashes]

    # Act
    handler._recover_downloads(affected_downloads)  # pylint: disable=W0212

    # Assert
    assert sorted(tracker.defective["remove_stalled"].keys()) == sorted(expected_remaining_in_tracker)


# ---------- Test ----------

@pytest.mark.parametrize(
    ("strikes_before_increment", "max_strikes", "expected_in_affected_downloads"),
    [
        (1, 3, False),  # Below limit   → should not be affected
        (2, 3, False),  # Below limit   → should not be affected
        (3, 3, True),   # At limit, will be pushed over limit      → should not be affected
        (4, 3, True),   # Over limit    → should be affected
    ],
)
def test_apply_strikes_and_filter(strikes_before_increment, max_strikes, expected_in_affected_downloads):
    job_name = "remove_stalled"
    tracker = MagicMock()
    tracker.defective = {job_name: {"HASH1": {"title": "dummy", "strikes": strikes_before_increment}}}

    arr = MagicMock()
    arr.tracker = tracker

    handler = StrikesHandler(job_name=job_name, arr=arr, max_strikes=max_strikes)

    affected_downloads = {
        "HASH1": {"title": "dummy"},
    }

    result = handler._apply_strikes_and_filter(affected_downloads)  # pylint: disable=W0212
    if expected_in_affected_downloads:
        assert "HASH1" in result
    else:
        assert "HASH1" not in result
