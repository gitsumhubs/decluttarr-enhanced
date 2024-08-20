from src.jobs.removal_job import RemovalJob

class RemoveUnmonitored(RemovalJob):
    queue_scope = "normal"
    blocklist = False

    async def _find_affected_items(self):
        queue = await self.queue_manager.get_queue_items(queue_scope="normal")

        # First pass: Check if items are monitored
        monitored_download_ids = []
        for item in queue:
            detail_item_id = item["detail_item_id"]
            if await self.arr.is_monitored(detail_item_id):
                monitored_download_ids.append(item["downloadId"])

        # Second pass: Append queue items none that depends on download id is monitored
        affected_items = []
        for queue_item in queue:
            if queue_item["downloadId"] not in monitored_download_ids:
                affected_items.append(
                    queue_item
                )  # One downloadID may be shared by multiple queue_items. Only removes it if ALL queueitems are unmonitored
        return affected_items