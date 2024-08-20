from src.jobs.removal_job import RemovalJob

class RemoveFailedDownloads(RemovalJob):
    queue_scope = "normal"
    blocklist = False

    async def _find_affected_items(self):
        queue = await self.queue_manager.get_queue_items(queue_scope="normal")
        affected_items = []

        for item in queue:
            if "status" in item:
                if item["status"] == "failed":
                    affected_items.append(item)
        return affected_items


