from src.jobs.removal_job import RemovalJob


class RemoveUnmonitored(RemovalJob):
    queue_scope = "normal"
    blocklist = False

    async def _find_affected_items(self):
        queue = await self.queue_manager.get_queue_items(queue_scope="normal")

        # First pass: Check if items are monitored
        monitored_download_ids = []
        for item in queue:
            if await self.arr.is_monitored(item["detail_item_id"]):
                monitored_download_ids.append(item["downloadId"])  # noqa: PERF401  - Can't make this a list comprehension due to the 'await'

        # Second pass: Append queue items none that depends on download id is monitored
        return [queue_item for queue_item in queue if queue_item["downloadId"] not in monitored_download_ids]  # One downloadID may be shared by multiple queue_items. Only removes it if ALL queue_items are unmonitored
