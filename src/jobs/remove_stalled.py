"""Removes stalled downloads."""

from src.jobs.removal_job import RemovalJob


class RemoveStalled(RemovalJob):
    queue_scope = "normal"
    blocklist = True

    async def _find_affected_items(self):
        queue = await self.queue_manager.get_queue_items(queue_scope="normal")
        return [item for item in queue if "errorMessage" in item and "status" in item and (item["status"] == "warning" and item["errorMessage"] == "The download is stalled with no connections")]



