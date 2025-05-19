from abc import ABC, abstractmethod
from src.utils.queue_manager import QueueManager
from src.utils.log_setup import logger
from src.jobs.strikes_handler import StrikesHandler
from src.jobs.removal_handler import RemovalHandler


class RemovalJob(ABC):
    job_name = None
    blocklist = True
    queue_scope = None
    affected_items = None
    affected_downloads = None
    job = None
    max_strikes = None

    # Default class attributes (can be overridden in subclasses)
    def __init__(self, arr, settings, job_name):
        self.arr = arr
        self.settings = settings
        self.job_name = job_name
        self.job = getattr(self.settings.jobs, self.job_name)
        self.queue_manager = QueueManager(self.arr, self.settings)
        self.strikes_handler = StrikesHandler( job_name=self.job_name, arr=self.arr, max_strikes=self.max_strikes, )


    async def run(self):
        if not self.job.enabled:
            return 0
        if await self.is_queue_empty(self.job_name, self.queue_scope):
            if self.max_strikes:
                self.strikes_handler.all_recovered()
            return 0
        self.affected_items = await self._find_affected_items()
        self.affected_downloads = self.queue_manager.group_by_download_id(self.affected_items)

        # -- Checks --
        self._ignore_protected()

        self.max_strikes = getattr(self.job, "max_strikes", None)
        if self.max_strikes:
            self.affected_downloads = self.strikes_handler.check_permitted_strikes(self.affected_downloads)

        # -- Removal --
        await RemovalHandler(
                arr=self.arr,
                settings=self.settings,
                job_name=self.job_name,
            ).remove_downloads(self.affected_downloads, self.blocklist)

        return len(self.affected_downloads)



    async def is_queue_empty(self, job_name, queue_scope="normal"):
        # Check if queue empty
        queue_items = await self.queue_manager.get_queue_items(queue_scope)
        logger.debug(
            f"{job_name}/queue IN: %s",
            self.queue_manager.format_queue(queue_items),
        )
        # Early exit if no queue
        if not queue_items:
            return True
        return False


    def _ignore_protected(self):
        """
        Filters out downloads that are in the protected tracker.
        Directly updates self.affected_downloads.
        """
        self.affected_downloads = {
            download_id: queue_items
            for download_id, queue_items in self.affected_downloads.items()
            if download_id not in self.arr.tracker.protected
        }

    @abstractmethod  # Imlemented on level of each removal job
    async def _find_affected_items(self):
        pass