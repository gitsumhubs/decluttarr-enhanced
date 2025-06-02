from src.jobs.removal_job import RemovalJob


class RemoveMetadataMissing(RemovalJob):
    queue_scope = "normal"
    blocklist = True

    async def _find_affected_items(self):
        conditions = [("queued", "qBittorrent is downloading metadata")]
        return self.queue_manager.filter_queue_by_status_and_error_message(self.queue, conditions)
