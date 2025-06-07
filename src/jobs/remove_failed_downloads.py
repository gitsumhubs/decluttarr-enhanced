from src.jobs.removal_job import RemovalJob


class RemoveFailedDownloads(RemovalJob):
    queue_scope = "normal"
    blocklist = False

    async def _find_affected_items(self):
        return self.queue_manager.filter_queue(self.queue, ["failed"])
