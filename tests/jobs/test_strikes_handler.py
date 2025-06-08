from unittest.mock import MagicMock, patch

import pytest
from src.jobs.strikes_handler import StrikesHandler

# pylint: disable=W0212
@pytest.mark.parametrize(
    ("before_recovery", "expected_remaining_in_tracker"),
    [
        ([], []),  # nothing active → all removed
        (["HASH1", "HASH2"], ["HASH1", "HASH2"]),  # both active → none removed
        (["HASH2"], ["HASH2"]),  # only HASH2 active → HASH1 removed
    ],
)
def test_recover_downloads(before_recovery, expected_remaining_in_tracker):
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
    affected_downloads = [(hash_id, {"title": "dummy"}) for hash_id in before_recovery]

    # Act
    handler._recover_downloads(affected_downloads)  # pylint: disable=W0212

    # Assert
    assert sorted(tracker.defective["remove_stalled"].keys()) == sorted(
        expected_remaining_in_tracker
    )

def test_recover_downloads2_no_patch():
    """Test if recovery correctly skips those items where tracking is paused."""
    handler = StrikesHandler(
        job_name="remove_stalled", arr=MagicMock(), max_strikes=3
    )
    handler.tracker = MagicMock()
    handler.tracker.defective = {
        "remove_stalled": {
            "id1": {"title": "Title1", "tracking_paused": False},
            "id2": {"title": "Title2", "tracking_paused": True},
            "id3": {"title": "Title3"},  # no paused flag = False
        }
    }

    affected_downloads = {"id3": {}}

    recovered, paused = handler._recover_downloads(affected_downloads)

    assert recovered == ["id1"]
    assert paused == ["id2"]


@pytest.mark.parametrize(
    ("strikes_before_increment", "max_strikes", "expected_in_affected_downloads"),
    [
        (1, 3, False),  # Below limit   → should not be affected
        (2, 3, False),  # Below limit   → should not be affected
        (3, 3, True),  # At limit, will be pushed over limit   → should be affected
        (4, 3, True),  # Over limit    → should be affected
    ],
)
def test_apply_strikes_and_filter(
    strikes_before_increment, max_strikes, expected_in_affected_downloads
):
    job_name = "remove_stalled"
    tracker = MagicMock()
    tracker.defective = {
        job_name: {"HASH1": {"title": "dummy", "strikes": strikes_before_increment}}
    }

    arr = MagicMock()
    arr.tracker = tracker

    handler = StrikesHandler(job_name=job_name, arr=arr, max_strikes=max_strikes)

    affected_downloads = {
        "HASH1": {"title": "dummy"},
    }

    result = handler._apply_strikes_and_filter(
        affected_downloads
    )
    if expected_in_affected_downloads:
        assert "HASH1" in result
    else:
        assert "HASH1" not in result


def test_log_change_logs_expected_strike_changes():
    handler = StrikesHandler(job_name="remove_stalled", arr=MagicMock(), max_strikes=3)
    handler.tracker = MagicMock()
    handler.tracker.defective = {
        "remove_stalled": {
            "hash_new": {"title": "A", "strikes": 1},  # should show in added
            "hash_inc": {"title": "B", "strikes": 2},  # should show in incremented
            "hash_paused": {"title": "C", "strikes": 2},  # should show in paused
        }
    }
    recovered = ["hash_old"]
    paused = ["hash_paused"]
    affected = {"hash_gone": {"title": "Gone"}}

    with patch("src.jobs.strikes_handler.logger") as mock_logger:
        handler.log_change(recovered, paused, affected)

        mock_logger.debug.assert_called_once()
        args, _ = mock_logger.debug.call_args

        log_msg = args[0]
        # Check keywords in the message string
        for keyword in ["Added", "Incremented", "Recovered", "Removed", "Paused"]:
            assert keyword in log_msg

        # Check keys in the entire call arguments (as string)
        for key in ["hash_new", "hash_inc", "hash_old", "hash_gone", "hash_paused"]:
            assert key in str(args)


@pytest.mark.parametrize(
    "max_strikes, initial_strikes, expected_removed_after_two_runs",
    [
        # max_strikes = 3
        (3, 0, False),  # 0 → 1 → 2
        (3, 1, False),  # 1 → 2 → 3
        (3, 2, True),  # 2 → 3 → 4
        (3, 3, True),  # 3 → 4 → 5
        # max_strikes = 2
        (2, 0, False),  # 0 → 1 → 2
        (2, 1, True),  # 1 → 2 → 3
        (2, 2, True),  # 2 → 3 → 4
        (2, 3, True),  # 3 → 4 → 5
    ],
)
def test_strikes_handler_overall(
    max_strikes, initial_strikes, expected_removed_after_two_runs
):
    """
    Verify that incrementing of strikes works and that
    based on its initial strikes and the max_strikes limit
    removal happens
    Note: The logging output does not show the strike where the removal will be triggered (ie., 4/3 if max strikes = 3)
    Reason: This is on verbose-level, as instead the removal handler then shows another info-level log
    """
    job_name = "remove_stalled"
    d_id = "some_hash"

    tracker_mock = MagicMock()
    tracker_mock.defective = {
        job_name: {d_id: {"title": "Some Title", "strikes": initial_strikes}}
    }

    arr = MagicMock()
    arr.tracker = tracker_mock

    affected_downloads = {d_id: {"title": "Some Title"}}

    handler = StrikesHandler(job_name=job_name, arr=arr, max_strikes=max_strikes)
    handler.check_permitted_strikes(affected_downloads.copy())
    handler = StrikesHandler(job_name=job_name, arr=arr, max_strikes=max_strikes)
    result = handler.check_permitted_strikes(affected_downloads.copy())

    assert (d_id in result) == expected_removed_after_two_runs, (
        f"Expected removed={expected_removed_after_two_runs} for "
        f"initial_strikes={initial_strikes}, max_strikes={max_strikes}, but got {d_id in result}"
    )
