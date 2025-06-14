"""Removes stalled downloads."""

from src.jobs.removal_job import RemovalJob


class RemoveStalled(RemovalJob):
    queue_scope = "normal"
    blocklist = True

    async def _find_affected_items(self):
        conditions = [("warning", "The download is stalled with no connections")]
        return self.queue_manager.filter_queue(self.queue, conditions)
