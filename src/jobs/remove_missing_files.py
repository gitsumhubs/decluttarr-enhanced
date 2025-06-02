from src.jobs.removal_job import RemovalJob


class RemoveMissingFiles(RemovalJob):
    queue_scope = "normal"
    blocklist = False

    async def _find_affected_items(self):
        affected_items = []

        for item in self.queue:
            if self._is_failed_torrent(item) or self._no_elibible_import(item):
                affected_items.append(item)
        return affected_items

    @staticmethod
    def _is_failed_torrent(item) -> bool:
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

    @staticmethod
    def _no_elibible_import(item) -> bool:
        if "status" in item and item["status"] == "completed" and "statusMessages" in item:
            for status_message in item["statusMessages"]:
                if "messages" in status_message:
                    for message in status_message["messages"]:
                        if message.startswith("No files found are eligible for import in"):
                            return True
        return False
