from src.jobs.removal_job import RemovalJob


class RemoveMetadataMissing(RemovalJob):
    queue_scope = "normal"
    blocklist = True

    async def _find_affected_items(self):
        affected_items = []

        for item in self.queue:
            if "errorMessage" in item and "status" in item:
                if (
                    item["status"] == "queued"
                    and item["errorMessage"] == "qBittorrent is downloading metadata"
                ):
                    affected_items.append(item)
        return affected_items
