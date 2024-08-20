from src.jobs.removal_job import RemovalJob
from src.utils.log_setup import logger


class RemoveSlow(RemovalJob):
    queue_scope = "normal"
    blocklist = True

    async def _find_affected_items(self):
        queue = await self.queue_manager.get_queue_items(queue_scope=self.queue_scope)
        affected_items = []
        checked_ids = set()

        for item in queue:
            if not self._is_valid_item(item):
                continue

            download_id = item["downloadId"]

            if download_id in checked_ids:
                continue  # One downloadId may occur in multiple items - only check once for all of them per iteration
            checked_ids.add(download_id)

            if self._is_usenet(item):
                continue  # No need to check for speed for usenet, since there users pay for speed

            if self._is_completed_but_stuck(item):
                logger.info(
                    f">>> '{self.job_name}' detected download marked as slow as well as completed. Files most likely in process of being moved. Not removing: {item['title']}"
                )
                continue

            downloaded, previous, increment, speed = await self._get_progress_stats(
                item
            )
            if self._is_slow(speed):
                affected_items.append(item)
                logger.debug(
                    f'remove_slow/slow speed detected: {item["title"]} '
                    f"(Speed: {speed} KB/s, KB now: {downloaded}, KB previous: {previous}, "
                    f"Diff: {increment}, In Minutes: {self.settings.general.timer})"
                )

        return affected_items

    def _is_valid_item(self, item):
        required_keys = {"downloadId", "size", "sizeleft", "status", "protocol"}  
        return required_keys.issubset(item)

    def _is_usenet(self, item):
        return item.get("protocol") == "usenet"

    def _is_completed_but_stuck(self, item):
        return (
            item["status"] == "downloading"
            and item["size"] > 0
            and item["sizeleft"] == 0
        )

    def _is_slow(self, speed):
        return (
            speed is not None
            and speed < self.job.min_speed
        )

    async def _get_progress_stats(self, item):
        download_id = item["downloadId"]

        download_progress = self._get_download_progress(item, download_id)
        previous_progress, increment, speed = self._compute_increment_and_speed(
            download_id, download_progress
        )

        self.arr.tracker.download_progress[download_id] = download_progress
        return download_progress, previous_progress, increment, speed

    def _get_download_progress(self, item, download_id):
        download_client_name = item.get("downloadClient")
        if download_client_name:
            download_client, download_client_type = self.settings.download_clients.get_download_client_by_name(download_client_name)
            if download_client_type == "qbitorrent":
                progress = self._try_get_qbit_progress(download_client, download_id)
                if progress is not None:
                    return progress
        return self._fallback_progress(item)

    def _try_get_qbit_progress(self, qbit, download_id):
        try:
            return qbit.get_download_progress(download_id)
        except Exception:
            return None

    def _fallback_progress(self, item):
        logger.debug(
            "get_progress_stats: Using imprecise method to determine download increments because either a different download client than qBitorrent is used, or the download client name in the config does not match with what is configured in your *arr download client settings"
        )
        return item["size"] - item["sizeleft"]

    def _compute_increment_and_speed(self, download_id, current_progress):
        previous_progress = self.arr.tracker.download_progress.get(download_id)
        if previous_progress is not None:
            increment = current_progress - previous_progress
            speed = round(increment / 1000 / (self.settings.general.timer * 60), 1)
        else:
            increment = speed = None
        return previous_progress, increment, speed
