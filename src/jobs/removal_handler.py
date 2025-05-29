from src.utils.log_setup import logger

class RemovalHandler:
    def __init__(self, arr, settings, job_name):
        self.arr = arr
        self.settings = settings
        self.job_name = job_name

    async def remove_downloads(self, affected_downloads, blocklist):
        for download_id in list(affected_downloads.keys()):
            logger.debug(
                "removal_handler.py/remove_downloads/arr.tracker.deleted IN: %s",
                str(self.arr.tracker.deleted),
            )

            queue_item = affected_downloads[download_id][0]
            handling_method = await self._get_handling_method(download_id, queue_item)

            if download_id in self.arr.tracker.deleted or handling_method == "skip":
                del affected_downloads[download_id]
                continue

            if handling_method == "remove":
                await self._remove_download(queue_item, blocklist)
            elif handling_method == "tag_as_obsolete":
                await self._tag_as_obsolete(queue_item, download_id)

            # Print out detailed removal messages (if any)
            if "removal_messages" in queue_item:
                for msg in queue_item["removal_messages"]:
                    logger.info(msg)

            self.arr.tracker.deleted.append(download_id)

            logger.debug(
                "removal_handler.py/remove_downloads/arr.tracker.deleted OUT: %s",
                str(self.arr.tracker.deleted),
            )


    async def _remove_download(self, queue_item, blocklist):
        queue_id = queue_item["id"]
        logger.info(f">>> Job '{self.job_name}' triggered removal: {queue_item['title']}")
        await self.arr.remove_queue_item(queue_id=queue_id, blocklist=blocklist)

    async def _tag_as_obsolete(self, queue_item, download_id):
        logger.info(f">>> Job'{self.job_name}' triggered obsolete-tagging: {queue_item['title']}")
        for qbit in self.settings.download_clients.qbittorrent:
            await qbit.set_tag(tags=[self.settings.general.obsolete_tag], hashes=[download_id])


    async def _get_handling_method(self, download_id, queue_item):
        if queue_item['protocol'] != 'torrent':
            return "remove" # handling is only implemented for torrent

        client_implemenation = await self.arr.get_download_client_implementation(queue_item['downloadClient'])
        if client_implemenation != "QBittorrent":
            return "remove" # handling is only implemented for qbit

        if len(self.settings.download_clients.qbittorrent) == 0:
            return "remove" # qbit not configured, thus can't tag

        if download_id in self.arr.tracker.private:
            return self.settings.general.private_tracker_handling

        return self.settings.general.public_tracker_handling
