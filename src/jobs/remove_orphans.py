from src.jobs.removal_job import RemovalJob


class RemoveOrphans(RemovalJob):
    queue_scope = "orphans"
    blocklist = False

    async def _find_affected_items(self):
        return self.queue
