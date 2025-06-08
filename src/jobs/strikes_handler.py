import logging
from src.utils.log_setup import logger


class StrikesHandler:
    def __init__(self, job_name, arr, max_strikes):
        self.job_name = job_name
        self.tracker = arr.tracker
        self.max_strikes = max_strikes
        self.tracker.defective.setdefault(job_name, {})

    def check_permitted_strikes(self, affected_downloads):
        recovered, paused = self._recover_downloads(affected_downloads)
        affected_downloads = self._apply_strikes_and_filter(affected_downloads)
        if logger.isEnabledFor(logging.DEBUG):
            self.log_change(recovered, paused, affected_downloads)
        return affected_downloads

    def log_change(self, recovered, paused, affected_items):
        tracker = self.tracker.defective[self.job_name]

        added = []
        incremented = []

        for d_id, entry in tracker.items():
            strikes = entry["strikes"]
            if strikes == 1:
                added.append(d_id)
            elif strikes > 1:
                incremented.append(f"{d_id} ({strikes}x)")

        removed = list(affected_items.keys())
        logger.debug(
            "Strike status changed | Added: %s | Incremented: %s | Recovered: %s | Tracking Paused: %s | Removed: %s",
            added or "None",
            incremented or "None",
            recovered or "None",
            paused or "None",
            removed or "None",
        )
        return added, incremented, recovered, removed

    def _recover_downloads(self, affected_downloads):
        """
        Identifies downloads that were previously tracked and are now no longer affected as recovered.
        If a download is marked as tracking_paused, they are not recovered (will be recovered later potentially)
        """
        recovered = []
        paused = []
        job_tracker = self.tracker.defective[self.job_name]
        affected_ids = dict(affected_downloads)

        for d_id, entry in list(job_tracker.items()):
            if d_id not in affected_ids:
                if entry.get("tracking_paused", False):
                    logger.debug(
                        "strikes_handler.py/_recover_downloads: %s tracking is paused for this entry: %s (%s)",
                        self.job_name,
                        entry["title"],
                        d_id,
                    )
                    paused.append(d_id)
                else:
                    logger.info(
                        ">>> Download no longer marked as %s: %s",
                        self.job_name,
                        entry["title"],
                    )
                    recovered.append(d_id)
                    del job_tracker[d_id]

        return recovered, paused

    def _apply_strikes_and_filter(self, affected_downloads):
        for d_id, affected_download in list(affected_downloads.items()):
            title = affected_download["title"]
            strikes = self._increment_strike(d_id, title)
            strikes_left = self.max_strikes - strikes
            self._log_strike_status(title, strikes, strikes_left)
            if strikes_left >= 0:
                del affected_downloads[d_id]

        return affected_downloads

    def _increment_strike(self, d_id, title):
        entry = self.tracker.defective[self.job_name].setdefault(
            d_id,
            {"title": title, "strikes": 0},
        )
        entry["strikes"] += 1
        return entry["strikes"]

    def _log_strike_status(self, title, strikes, strikes_left):
        if strikes_left >= 0:
            logger.info(
                ">>> Job '%s' detected download (%s/%s strikes): %s",
                self.job_name,
                strikes,
                self.max_strikes,
                title,
            )
        elif strikes_left == -1:
            # this is when the strikes are exceeded; a removal warning will be shown later, thus moving to verbose level
            logger.verbose(
                ">>> Job '%s' detected download (%s/%s strikes): %s",
                self.job_name,
                strikes,
                self.max_strikes,
                title,
            )
        elif strikes_left <= -2:  # noqa: PLR2004
            logger.info(
                ">>> Job '%s' detected download (%s/%s strikes): %s",
                self.job_name,
                strikes,
                self.max_strikes,
                title,
            )
            logger.info(
                '>>> 💡 Tip: Since this download should already have been removed in a previous iteration but keeps coming back, this indicates the blocking of the torrent does not work correctly. Consider turning on the option "Reject Blocklisted Torrent Hashes While Grabbing" on the indexer in the *arr app: %s',
                title,
            )
