from src.jobs.removal_job import RemovalJob

class RemoveOrphans(RemovalJob):
    queue_scope = "full"
    blocklist = False

    async def _find_affected_items(self):
        affected_items = await self.queue_manager.get_queue_items(queue_scope="orphans")
        return affected_items


