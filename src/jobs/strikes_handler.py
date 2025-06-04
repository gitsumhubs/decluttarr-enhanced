from src.utils.log_setup import logger


class StrikesHandler:
    def __init__(self, job_name, arr, max_strikes):
        self.job_name = job_name
        self.tracker = arr.tracker
        self.max_strikes = max_strikes
        self.tracker.defective.setdefault(job_name, {})

    def check_permitted_strikes(self, affected_downloads):
        recovered = self._recover_downloads(affected_downloads)
        affected_downloads = self._apply_strikes_and_filter(affected_downloads)
        self.log_change(recovered, affected_downloads)
        return affected_downloads

    def log_change(self, recovered, affected):
        tracker = self.tracker.defective[self.job_name]

        added = []
        incremented = []

        for d_id, entry in tracker.items():
            if entry["strikes"] == 1:
                added.append(d_id)
            elif entry["strikes"] > 1:
                incremented.append(d_id)

        removed = [d_id for d_id in affected]
        logger.debug(
            "Strike status changed | Added: %s | Incremented: %s | Recovered: %s | Removed: %s",
            added or "None",
            incremented or "None",
            recovered or "None",
            removed or "None",
        )

    def _recover_downloads(self, affected_downloads):
        recovered = [
            d_id
            for d_id in self.tracker.defective[self.job_name]
            if d_id not in dict(affected_downloads)
        ]
        for d_id in recovered:
            logger.info(
                ">>> Download no longer marked as %s: %s",
                self.job_name,
                self.tracker.defective[self.job_name][d_id]["title"],
            )
            del self.tracker.defective[self.job_name][d_id]
        return recovered

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
