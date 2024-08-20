from src.jobs.removal_job import RemovalJob

class RemoveMissingFiles(RemovalJob):
    queue_scope = "normal"
    blocklist = False

    async def _find_affected_items(self):
        queue = await self.queue_manager.get_queue_items(queue_scope="normal")
        affected_items = []

        for item in queue:
            if self._is_failed_torrent(item) or self._is_bad_nzb(item):
                affected_items.append(item)

        return affected_items

    def _is_failed_torrent(self, item):
        return (
            "status" in item
            and item["status"] == "warning"
            and "errorMessage" in item
            and item["errorMessage"] in [
                "DownloadClientQbittorrentTorrentStateMissingFiles",
                "The download is missing files",
                "qBittorrent is reporting missing files",
            ]
        )

    def _is_bad_nzb(self, item):
        if "status" in item and item["status"] == "completed" and "statusMessages" in item:
            for status_message in item["statusMessages"]:
                if "messages" in status_message:
                    for message in status_message["messages"]:
                        if message.startswith("No files found are eligible for import in"):
                            return True
        return False
