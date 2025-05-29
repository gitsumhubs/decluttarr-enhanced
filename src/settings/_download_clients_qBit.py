from packaging import version
from src.utils.common import make_request, wait_and_exit
from src.settings._constants import ApiEndpoints, MinVersions
from src.utils.log_setup import logger


class QbitError(Exception):
    pass

class QbitClients(list):
    """Represents all qBittorrent clients"""

    def __init__(self, config, settings):
        super().__init__()
        self._set_qbit_clients(config, settings)

    def _set_qbit_clients(self, config, settings):
        qbit_config = config.get("download_clients", {}).get("qbittorrent", [])

        if not isinstance(qbit_config, list):
            logger.error(
                "Invalid config format for qbittorrent clients. Expected a list."
            )
            return

        for client_config in qbit_config:
            try:
                self.append(QbitClient(settings, **client_config))
            except TypeError as e:
                logger.error(f"Error parsing qbittorrent client config: {e}")



class QbitClient:
    """Represents a single qBittorrent client."""

    cookie: str = None
    version: str = None

    def __init__(
        self,
        settings,
        base_url: str = None,
        username: str = None,
        password: str = None,
        name: str = None
    ):
        self.settings = settings
        if not base_url:
            logger.error("Skipping qBittorrent client entry: 'base_url' is required.")
            raise ValueError("qBittorrent client must have a 'base_url'.")

        self.base_url = base_url.rstrip("/")
        self.api_url = self.base_url + getattr(ApiEndpoints, "qbittorrent")
        self.min_version = getattr(MinVersions, "qbittorrent")
        self.username = username
        self.password = password
        self.name = name
        if not self.name:
            logger.verbose("No name provided for qbittorrent client, assuming 'qBitorrent'. If the name used in your *arr is different, please correct either the name in your *arr, or set the name in your config")
            self.name = "qBittorrent"

        self._remove_none_attributes()

    def _remove_none_attributes(self):
        """Removes attributes that are None to keep the object clean."""
        for attr in list(vars(self)):
            if getattr(self, attr) is None:
                delattr(self, attr)


    async def refresh_cookie(self):
        """Refresh the qBittorrent session cookie."""
        try:
            logger.debug("_download_clients_qBit.py/refresh_cookie: Refreshing qBit cookie")
            endpoint = f"{self.api_url}/auth/login"
            data = {"username": getattr(self, 'username', ''), "password": getattr(self, 'password', '')}
            headers = {"content-type": "application/x-www-form-urlencoded"}
            response = await make_request(
                "post", endpoint, self.settings, data=data, headers=headers, ignore_test_run=True
            )

            if response.text == "Fails.":
                raise ConnectionError("Login failed.")

            self.cookie = {"SID": response.cookies["SID"]}
        except Exception as e:
            logger.error(f"Error refreshing qBit cookie: {e}")
            self.cookie = {}
            raise QbitError(e) from e



    async def fetch_version(self):
        """Fetch the current qBittorrent version."""
        logger.debug("_download_clients_qBit.py/fetch_version: Getting qBit Version")
        endpoint = f"{self.api_url}/app/version"
        response = await make_request("get", endpoint, self.settings, cookies=self.cookie)
        self.version = response.text[1:]  # Remove the '_v' prefix
        logger.debug(f"_download_clients_qBit.py/fetch_version: qBit version={self.version}")


    async def validate_version(self):
        """Check if the qBittorrent version meets minimum and recommended requirements."""
        min_version = self.settings.min_versions.qbittorrent

        if version.parse(self.version) < version.parse(min_version):
            logger.error(
                f"Please update qBittorrent to at least version {min_version}. Current version: {self.version}"
            )
            raise QbitError(
                f"qBittorrent version {self.version} is too old. Please update."
            )
        if version.parse(self.version) < version.parse("5.0.0"):
            logger.info(
                f"[Tip!] Consider upgrading to qBittorrent v5.0.0 or newer to reduce network overhead."
            )

    async def create_tag(self, tag: str):
        """Ensure a tag exists in qBittorrent; create it if it doesn't."""
        logger.debug("_download_clients_qBit.py/create_tag: Checking if tag '{tag}' exists (and creating it if not)")
        url = f"{self.api_url}/torrents/tags"
        response = await make_request("get", url, self.settings, cookies=self.cookie)
        current_tags = response.json()

        if tag not in current_tags:
            logger.verbose(f"Creating tag: {tag}")
            data = {"tags": tag}
            await make_request(
                "post",
                self.api_url + "/torrents/createTags",
                self.settings,
                data=data,
                cookies=self.cookie,
            )

    async def create_required_tags(self):
        """Ensure protection and obsolete tags exist in qBittorrent if needed."""
        await self.create_tag(self.settings.general.protected_tag)

        if (
            self.settings.general.public_tracker_handling == "tag_as_obsolete"
            or self.settings.general.private_tracker_handling == "tag_as_obsolete"
        ):
            await self.create_tag(self.settings.general.obsolete_tag)

    async def set_unwanted_folder(self):
        """Set the 'unwanted folder' setting in qBittorrent if needed."""
        if self.settings.jobs.remove_bad_files:
            logger.debug("_download_clients_qBit.py/set_unwanted_folder: Checking preferences and setting use_unwanted_folder if not already set")
            endpoint = f"{self.api_url}/app/preferences"
            response = await make_request(
                "get", endpoint, self.settings, cookies=self.cookie
            )
            qbit_settings = response.json()

            if not qbit_settings.get("use_unwanted_folder"):
                logger.info(
                    "Enabling 'Keep unselected files in .unwanted folder' in qBittorrent."
                )
                data = {"json": '{"use_unwanted_folder": true}'}
                await make_request(
                    "post",
                    self.api_url + "/app/setPreferences",
                    self.settings,
                    data=data,
                    cookies=self.cookie,
                )


    async def check_qbit_reachability(self):
        """Check if the qBittorrent URL is reachable."""
        try:
            logger.debug("_download_clients_qBit.py/check_qbit_reachability: Checking if qbit is reachable")
            endpoint = f"{self.api_url}/auth/login"
            data = {"username": getattr(self, 'username', ''), "password": getattr(self, 'password', '')}
            headers = {"content-type": "application/x-www-form-urlencoded"}
            await make_request(
                "post", endpoint, self.settings, data=data, headers=headers, log_error=False, ignore_test_run=True
            )

        except Exception as e:
            tip = "💡 Tip: Did you specify the URL (and username/password if required) correctly?"
            logger.error(f"-- | qBittorrent\n❗️ {e}\n{tip}\n")
            wait_and_exit()


    async def check_qbit_connected(self):
        """Check if the qBittorrent is connected to internet."""
        logger.debug("_download_clients_qBit.py/check_qbit_reachability: Checking if qbit is connected to the internet")
        qbit_connection_status = ((
            await make_request(
                "get",
                self.api_url + "/sync/maindata",
                self.settings,
                cookies=self.cookie,
            )
        ).json())["server_state"]["connection_status"]
        if qbit_connection_status == "disconnected":
            return False
        else:
            return True



    async def setup(self):
        """Perform the qBittorrent setup by calling relevant managers."""
        # Check reachabilty
        await self.check_qbit_reachability()

        # Refresh the qBittorrent cookie first
        await self.refresh_cookie()

        try:
            # Fetch version and validate it
            await self.fetch_version()
            await self.validate_version()
            logger.info(f"OK | qBittorrent ({self.base_url})")
        except QbitError as e:
            logger.error(f"qBittorrent version check failed: {e}")
            wait_and_exit()  # Exit if version check fails

        # Continue with other setup tasks regardless of version check result
        await self.create_required_tags()
        await self.set_unwanted_folder()


    async def get_protected_and_private(self):
        """Fetches torrents from qBittorrent and checks for protected and private status."""
        protected_downloads = []
        private_downloads = []

        # Fetch all torrents
        logger.debug("_download_clients_qBit/get_protected_and_private: Checking if torrents have protected tag")
        qbit_items = await self.get_qbit_items()

        for qbit_item in qbit_items:
            # Fetch protected torrents (by tag)
            if self.settings.general.protected_tag in qbit_item.get("tags", []):
                protected_downloads.append(qbit_item["hash"].upper())

            # Fetch private torrents
            if not (self.settings.general.private_tracker_handling == "remove" or self.settings.general.public_tracker_handling == "remove"):
                if version.parse(self.version) >= version.parse("5.0.0"):
                    if qbit_item.get("private"):
                        private_downloads.append(qbit_item["hash"].upper())
                else:
                    logger.debug("_download_clients_qBit/get_protected_and_private: Checking if torrents are private (only done for old qbit versions)")
                    qbit_item_props = await make_request(
                        "get",
                        self.api_url + "/torrents/properties",
                        self.settings,
                        params={"hash": qbit_item["hash"]},
                        cookies=self.cookie,
                    )
                    if not qbit_item_props:
                        logger.error(
                            "Torrent %s not found on qBittorrent - potentially removed while checking if private. "
                            "Consider upgrading qBit to v5.0.4 or newer to avoid this problem.",
                            qbit_item["hash"],
                        )
                        continue
                    if qbit_item_props.get("is_private", False):
                        private_downloads.append(qbit_item["hash"].upper())
                    qbit_item["private"] = qbit_item_props.get("is_private", None)

        return protected_downloads, private_downloads

    async def set_tag(self, tags, hashes):
        """
        Sets tags to one or more torrents in qBittorrent.

        Args:
            tags (list): A list of tag names to be added.
            hashes (list): A list of torrent hashes to which the tags should be applied.
        """
        # Ensure hashes are provided as a string separated by '|'
        hashes_str = "|".join(hashes)

        # Ensure tags are provided as a string separated by ',' (comma)
        tags_str = ",".join(tags)

        logger.debug("_download_clients_qBit/set_tag: Setting tag(s) {tags_str} to {hashes_str}")

        # Prepare the data for the request
        data = {
            "hashes": hashes_str,
            "tags": tags_str
        }

        # Perform the request to add the tag(s) to the torrents
        await make_request(
            "post",
            self.api_url + "/torrents/addTags",
            self.settings,
            data=data,
            cookies=self.cookie, 
        )


    async def get_download_progress(self, download_id):
        items = await self.get_qbit_items(download_id)
        return items[0]["completed"]


    async def get_qbit_items(self, hashes=None):
        params = None
        if hashes:
            if isinstance(hashes, str):
                hashes = [hashes]
            params = {"hashes": "|".join(hashes).lower()}  # Join and make lowercase

        response = await make_request(
            method="get",
            endpoint=self.api_url + "/torrents/info",
            settings=self.settings,
            params=params,
            cookies=self.cookie,
        )
        return response.json()


    async def get_torrent_files(self, download_id):
        # this may not work if the wrong qbit
        logger.debug("_download_clients_qBit/get_torrent_files: Getting torrent files")
        response = await make_request(
            method="get",
            endpoint=self.api_url + "/torrents/files",
            settings=self.settings,
            params={"hash": download_id.lower()},
            cookies=self.cookie,
        )
        return response.json()

    async def set_torrent_file_priority(self, download_id, file_id, priority = 0):
        logger.debug("_download_clients_qBit/set_torrent_file_priority: Setting download priority for torrent file")
        data={
            "hash": download_id.lower(),
            "id": file_id,
            "priority": priority,
        }
        await make_request(
            "post",
            self.api_url + "/torrents/filePrio",
            self.settings,
            data=data,
            cookies=self.cookie,
        )

