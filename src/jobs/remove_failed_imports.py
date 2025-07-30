import fnmatch

from src.jobs.removal_job import RemovalJob


class RemoveFailedImports(RemovalJob):
    queue_scope = "normal"
    blocklist = True

    async def _find_affected_items(self):
        affected_items = []
        patterns = self.job.message_patterns

        for item in self.queue:
            if not self._is_valid_item(item):
                continue

            removal_messages = self._prepare_removal_messages(item, patterns)
            if removal_messages:
                item["removal_messages"] = removal_messages
                affected_items.append(item)

        return affected_items

    @staticmethod
    def _is_valid_item(item) -> bool:
        """Check if item has the necessary fields and is in a valid state."""
        # Required fields that must be present in the item
        required_fields = {"status", "trackedDownloadStatus", "trackedDownloadState", "statusMessages"}

        # Check if all required fields are present
        if not all(field in item for field in required_fields):
            return False

        # Enhanced detection: Check for both original conditions and qBittorrent error states
        # Original: completed status with warning tracked status
        original_condition = (
            item["status"] == "completed" and 
            item["trackedDownloadStatus"] == "warning" and
            item["trackedDownloadState"] in {"importPending", "importFailed", "importBlocked"}
        )
        
        # Enhanced: warning status with downloading state (catches "qBittorrent is reporting an error")
        enhanced_condition = (
            item["status"] == "warning" and 
            item["trackedDownloadState"] == "downloading"
        )
        
        return original_condition or enhanced_condition

    def _prepare_removal_messages(self, item, patterns) -> list[str]:
        """Prepare removal messages, adding the tracked download state and matching messages."""
        messages = self._get_matching_messages(item["statusMessages"], patterns)
        if not messages:
            return []

        removal_messages = [
            f"↳ Tracked Download State: {item['trackedDownloadState']}",
            f"↳ Status Messages:",
            *[f" - {msg}" for msg in messages]
        ]
        return removal_messages


    @staticmethod
    def _get_matching_messages(status_messages, patterns) -> list[str]:
        """Extract unique messages matching the provided patterns (or all messages if no pattern)."""
        messages = [
            msg
            for status_message in status_messages
            for msg in status_message.get("messages", [])
            if not patterns or any(fnmatch.fnmatch(msg, pattern) for pattern in patterns)
        ]
        return list(dict.fromkeys(messages))
