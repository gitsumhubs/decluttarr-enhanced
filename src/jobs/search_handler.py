from datetime import datetime, timedelta, timezone

import dateutil.parser

from src.utils.log_setup import logger
from src.utils.queue_manager import QueueManager
from src.utils.wanted_manager import WantedManager


class SearchHandler:
    def __init__(self, arr, settings):
        self.arr = arr
        self.settings = settings
        self.job = None
        self.wanted_manager = WantedManager(self.arr, self.settings)

    async def handle_search(self, search_type):
        logger.debug(f"search_handler.py: Running '{search_type}' search")
        self._initialize_job(search_type)

        wanted_items = await self._get_initial_wanted_items(search_type)
        if not wanted_items:
            return

        queue = await QueueManager(self.arr, self.settings).get_queue_items(
            queue_scope="normal",
        )
        wanted_items = self._filter_wanted_items(wanted_items, queue)
        if not wanted_items:
            return

        await self._log_items(wanted_items, search_type)
        await self._trigger_search(wanted_items)

    def _initialize_job(self, search_type):
        logger.verbose("")
        if search_type == "missing":
            logger.verbose(f"Searching for missing content on {self.arr.name}:")
            self.job = self.settings.jobs.search_missing_content
        elif search_type == "cutoff":
            logger.verbose(f"Searching for unmet cutoff content on {self.arr.name}:")
            self.job = self.settings.jobs.search_unmet_cutoff_content
        else:
            error = f"Unknown search type: {search_type}"
            raise ValueError(error)

    def _get_initial_wanted_items(self, search_type):
        wanted = self.wanted_manager.get_wanted_items(search_type)
        if not wanted:
            logger.verbose(f">>> No {search_type} items, thus not triggering a search.")
        return wanted

    def _filter_wanted_items(self, items, queue):
        items = self._filter_already_downloading(items, queue)
        if not items:
            logger.verbose(">>> All items already downloading, nothing to search for.")
            return []

        items = self._filter_recent_searches(items)
        if not items:
            logger.verbose(
                ">>> All items recently searched for, thus not triggering another search.",
            )
            return []

        return items[: self.job.max_concurrent_searches]

    def _filter_already_downloading(self, wanted_items, queue):
        queue_ids = {q[self.arr.detail_item_id_key] for q in queue}
        return [item for item in wanted_items if item["id"] not in queue_ids]

    async def _trigger_search(self, items):
        if not self.settings.general.test_run:
            ids = [item["id"] for item in items]
            await self.wanted_manager.search_items(ids)

    def _filter_recent_searches(self, items):
        now = datetime.now(timezone.utc)
        result = []

        for item in items:
            last = item.get("lastSearchTime")
            if not last:
                item["lastSearchDateFormatted"] = "Never"
                item["daysSinceLastSearch"] = None
                result.append(item)
                continue

            last_time = dateutil.parser.isoparse(last)
            days_ago = (now - last_time).days

            if last_time + timedelta(days=self.job.min_days_between_searches) < now:
                item["lastSearchDateFormatted"] = last_time.strftime("%Y-%m-%d")
                item["daysSinceLastSearch"] = days_ago
                result.append(item)

        return result

    async def _log_items(self, items, search_type):
        logger.verbose(f">>> Running a scan for {len(items)} {search_type} items:")
        for item in items:
            if self.arr.arr_type in ["radarr", "readarr", "lidarr"]:
                title = item.get("title", "Unknown")
                logger.verbose(f">>> - {title}")

            elif self.arr.arr_type == "sonarr":
                series = await self.arr.get_series()
                series_title = next(
                    (s["title"] for s in series if s["id"] == item.get("seriesId")),
                    "Unknown",
                )
                episode = item.get("episodeNumber", "00")
                season = item.get("seasonNumber", "00")
                season_numbering = f"S{int(season):02}/E{int(episode):02}"
                logger.verbose(f">>> - {series_title} ({season_numbering})")

    async def _get_series_dict(self):
        series = await self.arr.rest_get("series")
        return {s["id"]: s for s in series}
