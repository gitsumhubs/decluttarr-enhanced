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

        # Check if the item's status is completed and the tracked status is warning
        if item["status"] != "completed" or item["trackedDownloadStatus"] != "warning":
            return False

        # Check if the tracked download state is one of the allowed states
        # If all checks pass, the item is valid
        return not (item["trackedDownloadState"] not in {"importPending", "importFailed", "importBlocked"})

    def _prepare_removal_messages(self, item, patterns) -> list[str]:
        """Prepare removal messages, adding the tracked download state and matching messages."""
        messages = self._get_matching_messages(item["statusMessages"], patterns)
        if not messages:
            return []

        return [f">>>>> Tracked Download State: {item['trackedDownloadState']}", *messages]

    @staticmethod
    def _get_matching_messages(status_messages, patterns) -> list:
        """Extract messages matching the provided patterns (or all messages if no pattern)."""
        matched_messages = []

        if not patterns:
            # No patterns provided, include all messages
            for status_message in status_messages:
                matched_messages.extend(f">>>>> - {msg}" for msg in status_message.get("messages", []))
        else:
            # Patterns provided, match only those messages that fit the patterns
            matched_messages.extend(
                f">>>>> - {msg}"
                for status_message in status_messages
                for msg in status_message.get("messages", [])
                if any(fnmatch.fnmatch(msg, pattern) for pattern in patterns)
            )

        return matched_messages
