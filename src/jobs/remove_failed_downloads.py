from src.jobs.removal_job import RemovalJob

class RemoveFailedDownloads(RemovalJob):
    queue_scope = "normal"
    blocklist = False

    async def _find_affected_items(self):
        affected_items = []

        for item in self.queue:
            if "status" in item:
                if item["status"] == "failed":
                    affected_items.append(item)
        return affected_items


