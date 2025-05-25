from src.utils.common import make_request
from src.utils.log_setup import logger


class QueueManager:
    def __init__(self, arr, settings):
        self.arr = arr
        self.settings = settings

    async def get_queue_items(self, queue_scope):
        """
        Retrieve queue items based on the scope.

        queue_scope:
            "normal" = normal queue
            "orphans" = orphaned queue items (in full queue but not in normal queue)
            "full" = full queue
        """
        if queue_scope == "normal":
            queue_items = await self._get_queue(full_queue=False)
        elif queue_scope == "orphans":
            full_queue = await self._get_queue(full_queue=True)
            queue = await self._get_queue(full_queue=False)
            queue_items = [fq for fq in full_queue if fq not in queue]
        elif queue_scope == "full":
            queue_items = await self._get_queue(full_queue=True)
        else:
            error = f"Invalid queue_scope: {queue_scope}"
            raise ValueError(error)
        return queue_items

    async def _get_queue(self, *, full_queue=False):
        # Step 1: Refresh the queue (now internal)
        await self._refresh_queue()

        # Step 2: Get the total number of records
        record_count = await self._get_total_records(full_queue)

        # Step 3: Get all records using `arr.full_queue_parameter`
        queue = await self._get_arr_records(full_queue, record_count)

        # Step 4: Filter the queue based on delayed items and ignored download clients
        queue = self._ignore_delayed_queue_items(queue)
        queue = self._filter_out_ignored_download_clients(queue)
        return self._add_detail_item_key(queue)

    def _add_detail_item_key(self, queue):
        """Normalize episodeID, bookID, etc. so it can just be called by 'detail_item_id'."""
        for items in queue:
            items["detail_item_id"] = items.get(self.arr.detail_item_id_key)
        return queue

    async def _refresh_queue(self):
        # Refresh the queue by making the POST request using an external make_request function
        await make_request(
            method="POST",
            endpoint=f"{self.arr.api_url}/command",
            settings=self.settings,
            json={"name": "RefreshMonitoredDownloads"},
            headers={"X-Api-Key": self.arr.api_key},
        )

    async def _get_total_records(self, full_queue):
        # Get the total number of records from the queue using `arr.full_queue_parameter`
        params = {self.arr.full_queue_parameter: full_queue}
        response = (
            await make_request(
                method="GET",
                endpoint=f"{self.arr.api_url}/queue",
                settings=self.settings,
                params=params,
                headers={"X-Api-Key": self.arr.api_key},
            )
        ).json()
        return response["totalRecords"]

    async def _get_arr_records(self, full_queue, record_count):
        # Get all records based on the count (with pagination) using `arr.full_queue_parameter`
        if record_count == 0:
            return []

        params = {"page": "1", "pageSize": record_count}
        if full_queue:
            params |= {self.arr.full_queue_parameter: full_queue}

        records = (
            await make_request(
                method="GET",
                endpoint=f"{self.arr.api_url}/queue",
                settings=self.settings,
                params=params,
                headers={"X-Api-Key": self.arr.api_key},
            )
        ).json()
        return records["records"]

    @staticmethod
    def _ignore_delayed_queue_items(queue) -> list | None:
        # Ignores delayed queue items
        if queue is None:
            return None
        seen_combinations = set()
        filtered_queue = []
        for queue_item in queue:
            indexer = queue_item.get("indexer", "No indexer")
            protocol = queue_item.get("protocol", "No protocol")
            combination = (queue_item["title"], protocol, indexer)
            if queue_item["status"] == "delay":
                if combination not in seen_combinations:
                    seen_combinations.add(combination)
                    logger.debug(
                        ">>> Delayed queue item ignored: %s (Protocol: %s, Indexer: %s)",
                        queue_item["title"],
                        protocol,
                        indexer,
                    )
            else:
                filtered_queue.append(queue_item)
        return filtered_queue

    def _filter_out_ignored_download_clients(self, queue):
        # Filters out ignored download clients
        if queue is None:
            return queue
        filtered_queue = []

        for queue_item in queue:
            download_client = queue_item.get("downloadClient", "Unknown client")
            if download_client in self.settings.general.ignored_download_clients:
                logger.debug(
                    ">>> Queue item ignored due to ignored download client: %s (Download Client: %s)",
                    queue_item["title"],
                    download_client,
                )
            else:
                filtered_queue.append(queue_item)

        return filtered_queue

    @staticmethod
    def format_queue(queue_items) -> list | str:
        if not queue_items:
            return "empty"

        formatted_dict = {}

        for queue_item in queue_items:
            download_id = queue_item.get("downloadId")
            item_id = queue_item.get("id")

            if download_id in formatted_dict:
                formatted_dict[download_id]["IDs"].append(item_id)
            else:
                formatted_dict[download_id] = {
                    "downloadId": download_id,
                    "downloadTitle": queue_item.get("title"),
                    "IDs": [item_id],
                    "protocol": [queue_item.get("protocol")],
                    "status": [queue_item.get("status")],
                }

        return list(formatted_dict.values())

    @staticmethod
    def group_by_download_id(queue_items) -> dict:
        # Groups queue items by download ID and returns a dict where download ID is the key, and value is the list of queue items belonging to that downloadID
        # Queue item is limited to certain keys
        retain_keys = {
            "id": None,
            "detail_item_id": None,
            "title": "Unknown",
            "size": 0,
            "sizeleft": 0,
            "downloadClient": "Unknown",
            "protocol": "Unknown",
            "status": "Unknown",
            "trackedDownloadState": "Unknown",
            "statusMessages": [],
            "removal_messages": [],
        }

        grouped_dict = {}

        for queue_item in queue_items:
            download_id = queue_item["downloadId"]
            if download_id not in grouped_dict:
                grouped_dict[download_id] = []

            # Filter and add default values if keys are missing
            filtered_item = {
                key: queue_item.get(key, retain_keys.get(key))
                for key in retain_keys
            }

            grouped_dict[download_id].append(filtered_item)

        return grouped_dict
