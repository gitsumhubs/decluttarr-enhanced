import logging
from src.utils.log_setup import logger
from src.utils.common import make_request


class QueueManager:
    def __init__(self, arr, settings):
        self.arr = arr
        self.settings = settings

    async def get_queue_items(self, queue_scope):
        """
        Retrieves queue items based on the scope.
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
            raise ValueError(f"Invalid queue_scope: {queue_scope}")
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("queue_manager.py/get_queue_items/queue (%s): %s", queue_scope, self.format_queue(queue_items))
        return queue_items

    async def _get_queue(self, full_queue=False):
        # Step 1: Refresh the queue (now internal)
        await self._refresh_queue()

        # Step 2: Get the total number of records
        record_count = await self._get_total_records(full_queue)

        # Step 3: Get all records using `arr.full_queue_parameter`
        queue = await self._get_arr_records(full_queue, record_count)

        # Step 4: Filter the queue based on delayed items and ignored download clients
        queue = self._filter_out_ignored_statuses(queue)
        queue = self._filter_out_ignored_download_clients(queue)
        queue = self._add_detail_item_key(queue)
        return queue

    def _add_detail_item_key(self, queue):
        """Normalizes episodeID, bookID, etc so it can just be called by 'detail_item_id'"""
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

    def _filter_out_ignored_statuses(self, queue, ignored_statuses=("delay","downloadClientUnavailable")):
        """
        All matching items are removed from the queue. However, logging of ignored items
        is limited to one per (download title, protocol, indexer) combination to reduce log noise
        (since one download may be behind in multiple queue items)

        Args:
            queue (list[dict]): The queue to filter.
            ignored_statuses (tuple[str]): Status values to ignore.

        Returns:
            list[dict]: Filtered queue.
        """
        if queue is None:
            return queue

        seen_combinations = set()
        filtered_queue = []

        for item in queue:
            status = item.get("status")
            title = item.get("title")
            protocol = item.get("protocol", "No protocol")
            indexer = item.get("indexer", "No indexer")
            combination = (title, protocol, indexer)

            if status in ignored_statuses:
                if combination not in seen_combinations:
                    seen_combinations.add(combination)
                    logger.debug(f"queue_manager.py/_filter_out_ignored_statuses: Ignored queue item: {title} (Status: {status}, Protocol: {protocol}, Indexer: {indexer})")
                continue

            filtered_queue.append(item)

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

    def format_queue(self, queue_items):
        if not queue_items:
            return "empty"
        return self.group_by_download_id(queue_items)

    def group_by_download_id(self, queue_items):
        # Groups queue items by download ID and returns a dict where download ID is the key,
        # and the value is a dict with a list of IDs and other selected metadata.
        retain_keys = [
            "detail_item_id",
            "title",
            "size",
            "sizeleft",
            "downloadClient",
            "protocol",
            "status",
            "trackedDownloadState",
            "statusMessages",
            "removal_messages",
        ]

        grouped_dict = {}

        for queue_item in queue_items:
            download_id = queue_item.get("downloadId")
            item_id = queue_item.get("id")

            if download_id in grouped_dict:
                grouped_dict[download_id]["queue_ids"].append(item_id)
            else:
                grouped_dict[download_id] = {
                    "queue_ids": [item_id],
                    **{
                        key: queue_item[key]
                        for key in retain_keys
                        if key in queue_item
                    },
                }

        return grouped_dict
