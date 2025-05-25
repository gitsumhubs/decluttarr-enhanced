from src.utils.common import make_request


class WantedManager:
    def __init__(self, arr, settings):
        self.arr = arr
        self.settings = settings

    async def get_wanted_items(self, missing_or_cutoff):
        """
        Retrieve wanted items.

        missing_or_cutoff: Drives whether missing or cutoff items are retrieved
        """
        record_count = await self._get_total_records(missing_or_cutoff)
        return await self._get_arr_records(missing_or_cutoff, record_count)

    async def _get_total_records(self, missing_or_cutoff):
        # Get the total number of records from wanted
        response = (
            await make_request(
                method="GET",
                endpoint=f"{self.arr.api_url}/wanted/{missing_or_cutoff}",
                settings=self.settings,
                headers={"X-Api-Key": self.arr.api_key},
            )
        ).json()
        return response["totalRecords"]

    async def _get_arr_records(self, missing_or_cutoff, record_count):
        # Get all records based on the count (with pagination)
        if record_count == 0:
            return []

        sort_key = f"{self.arr.detail_item_key}s.lastSearchTime"
        params = {"page": "1", "pageSize": record_count, "sortKey": sort_key}

        records = (
            await make_request(
                method="GET",
                endpoint=f"{self.arr.api_url}/wanted/{missing_or_cutoff}",
                settings=self.settings,
                params=params,
                headers={"X-Api-Key": self.arr.api_key},
            )
        ).json()
        return records["records"]

    async def search_items(self, detail_ids):
        """Search items by detail IDs."""
        if isinstance(detail_ids, str):
            detail_ids = [detail_ids]

        json = {
            "name": self.arr.detail_item_search_command,
            self.arr.detail_item_ids_key: detail_ids,
        }
        await make_request(
            method="POST",
            endpoint=f"{self.arr.api_url}/command",
            settings=self.settings,
            json=json,
            headers={"X-Api-Key": self.arr.api_key},
        )
