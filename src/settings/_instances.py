import requests
from packaging import version

from src.utils.log_setup import logger
from src.settings._constants import (
    ApiEndpoints,
    MinVersions,
    FullQueueParameter,
    DetailItemKey,
    DetailItemSearchCommand,
)
from src.settings._config_as_yaml import get_config_as_yaml
from src.utils.common import make_request, wait_and_exit


class Tracker:
    def __init__(self):
        self.protected = []
        self.private = []
        self.defective = {}
        self.download_progress = {}
        self.deleted = []
        self.extension_checked = []

    async def refresh_private_and_protected(self, settings):
        protected_downloads = []
        private_downloads = []

        for qbit in settings.download_clients.qbittorrent:
            protected, private = await qbit.get_protected_and_private()
            protected_downloads.extend(protected)
            private_downloads.extend(private)

        self.protected = protected_downloads
        self.private = private_downloads


class ArrError(Exception):
    pass


class Instances:
    """Represents all Arr instances."""

    def __init__(self, config, settings):
        self.arrs = ArrInstances(config, settings)
        if not self.arrs:
            logger.error("No valid Arr instances found in the config.")
            wait_and_exit()

    def get_by_arr_type(self, arr_type):
        """Return a list of arr instances matching the given arr_type."""
        return [arr for arr in self.arrs if arr.arr_type == arr_type]

    def config_as_yaml(self, hide_internal_attr=True):
        """Logs all configured Arr instances while masking sensitive attributes."""
        internal_attributes={
                        "settings",
                        "api_url",
                        "min_version",
                        "arr_type",
                        "full_queue_parameter",
                        "monitored_item",
                        "detail_item_key",
                        "detail_item_id_key",
                        "detail_item_ids_key",
                        "detail_item_search_command",
                    }     

        outputs = []
        for arr_type in ["sonarr", "radarr", "readarr", "lidarr", "whisparr"]:
            arrs = self.get_by_arr_type(arr_type)
            if arrs:
                output = get_config_as_yaml(
                    {arr_type.capitalize(): arrs},
                    sensitive_attributes={"api_key"},
                    internal_attributes=internal_attributes,
                    hide_internal_attr=hide_internal_attr,
                )
                outputs.append(output)

        return "\n".join(outputs)



    def check_any_arrs(self):
        """Check if there are any ARR instances."""
        if not self.arrs:
            logger.warning("No ARR instances found.")
            wait_and_exit()


class ArrInstances(list):
    """Represents all Arr clients (Sonarr, Radarr, etc.)."""

    def __init__(self, config, settings):
        super().__init__()
        self._load_clients(config, settings)

    def _load_clients(self, config, settings):
        instances_config = config.get("instances", {})

        if not isinstance(instances_config, dict):
            logger.error("Invalid format for 'instances'. Expected a dictionary.")
            return

        for arr_type, clients in instances_config.items():
            if not isinstance(clients, list):
                logger.error(f"Invalid config format for {arr_type}. Expected a list.")
                continue

            for client_config in clients:
                try:
                    self.append(
                        ArrInstance(
                            settings,
                            arr_type=arr_type,
                            base_url=client_config["base_url"],
                            api_key=client_config["api_key"],
                        )
                    )
                except KeyError as e:
                    logger.error(
                        f"Missing required key {e} in {arr_type} client config."
                    )


class ArrInstance:
    """Represents an individual Arr instance (Sonarr, Radarr, etc.)."""

    version: str = None
    name: str = None
    tracker = Tracker()

    def __init__(self, settings, arr_type: str, base_url: str, api_key: str):
        if not base_url:
            logger.error(f"Skipping {arr_type} client entry: 'base_url' is required.")
            raise ValueError(f"{arr_type} client must have a 'base_url'.")

        if not api_key:
            logger.error(f"Skipping {arr_type} client entry: 'api_key' is required.")
            raise ValueError(f"{arr_type} client must have an 'api_key'.")

        self.settings = settings
        self.arr_type = arr_type
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.api_url = self.base_url + getattr(ApiEndpoints, arr_type)
        self.min_version = getattr(MinVersions, arr_type)
        self.full_queue_parameter = getattr(FullQueueParameter, arr_type)
        self.detail_item_key = getattr(DetailItemKey, arr_type)
        self.detail_item_id_key = self.detail_item_key + "Id"
        self.detail_item_ids_key = self.detail_item_key + "Ids"
        self.detail_item_search_command = getattr(DetailItemSearchCommand, arr_type) 
        
    async def _check_ui_language(self):
        """Check if the UI language is set to English."""
        endpoint = self.api_url + "/config/ui"
        headers = {"X-Api-Key": self.api_key}
        response = await make_request("get", endpoint, self.settings, headers=headers)
        ui_language = (response.json())["uiLanguage"]
        if ui_language > 1:  # Not English
            logger.error("!! %s Error: !!", self.name)
            logger.error(
                f"> Decluttarr only works correctly if UI language is set to English (under Settings/UI in {self.name})"
            )
            logger.error(
                "> Details: https://github.com/ManiMatter/decluttarr/issues/132)"
            )
            raise ArrError("Not English")

    def _check_min_version(self, status):
        """Check if ARR instance meets minimum version requirements."""
        self.version = status["version"]
        min_version = getattr(self.settings.min_versions, self.arr_type)

        if min_version:
            if version.parse(self.version) < version.parse(min_version):
                logger.error("!! %s Error: !!", self.name)
                logger.error(
                    f"> Please update {self.name} ({self.base_url}) to at least version {min_version}. Current version: {self.version}"
                )
                raise ArrError("Not meeting minimum version requirements")

    def _check_arr_type(self, status):
        """Check if the ARR instance is of the correct type."""
        actual_arr_type = status["appName"]
        if actual_arr_type.lower() != self.arr_type:
            logger.error("!! %s Error: !!", self.name)
            logger.error(
                f"> Your {self.name} ({self.base_url}) points to a {actual_arr_type} instance, rather than {self.arr_type}. Did you specify the wrong IP?"
            )
            raise ArrError("Wrong Arr Type")

    async def _check_reachability(self):
        """Check if ARR instance is reachable."""
        try:
            endpoint = self.api_url + "/system/status"
            headers = {"X-Api-Key": self.api_key}
            response = await make_request(
                "get", endpoint, self.settings, headers=headers, log_error=False
            )
            status = response.json()
            return status
        except Exception as e:
            if isinstance(e, requests.exceptions.HTTPError):
                response = getattr(e, "response", None)
                if response is not None and response.status_code == 401:
                    tip = "💡 Tip: Have you configured the API_KEY correctly?"
                else:
                    tip = f"💡 Tip: HTTP error occurred. Status: {getattr(response, 'status_code', 'unknown')}"
            elif isinstance(e, requests.exceptions.RequestException):
                tip = "💡 Tip: Have you configured the URL correctly?"
            else:
                tip = ""

            logger.error(f"-- | {self.arr_type} ({self.base_url})\n❗️ {e}\n{tip}\n")
            raise ArrError(e) from e

    async def setup(self):
        """Checks on specific ARR instance"""
        try:
            status = await self._check_reachability()
            self.name = status.get("instanceName", self.arr_type)
            self._check_arr_type(status)
            self._check_min_version(status)
            await self._check_ui_language()

            # Display result
            logger.info(f"OK | {self.name} ({self.base_url})")
            logger.debug(f"Current version of {self.name}: {self.version}")

        except Exception as e:
            if not isinstance(e, ArrError):
                logger.error(f"Unhandled error: {e}", exc_info=True)
            wait_and_exit()

    async def get_download_client_implementation(self, download_client_name):
        """Fetch download client information and return the implementation value."""
        endpoint = self.api_url + "/downloadclient"
        headers = {"X-Api-Key": self.api_key}

        # Fetch the download client list from the API
        response = await make_request("get", endpoint, self.settings, headers=headers)

        # Check if the response is a list
        download_clients = response.json()

        # Find the client where the name matches client_name
        for client in download_clients:
            if client.get("name") == download_client_name:
                # Return the implementation value if found
                return client.get("implementation", None)
        return None

    async def remove_queue_item(self, queue_id, blocklist=False):
        """
        Remove a specific queue item from the queue by its qeue id.
        Sends a delete request to the API to remove the item.

        Args:
            queue_id (str): The quueue ID of the queue item to be removed.
            blocklist (bool): Whether to add the item to the blocklist. Default is False.

        Returns:
            bool: Returns True if the removal was successful, False otherwise.
        """
        endpoint = f"{self.api_url}/queue/{queue_id}"
        headers = {"X-Api-Key": self.api_key}
        json_payload = {"removeFromClient": True, "blocklist": blocklist}

        # Send the request to remove the download from the queue
        response = await make_request(
            "delete", endpoint, self.settings, headers=headers, json=json_payload
        )

        # If the response is successful, return True, else return False
        if response.status_code == 200:
            return True
        else:
            return False

    async def is_monitored(self, detail_id):
        """Check if detail item (like a book, series, etc) is monitored."""
        endpoint = f"{self.api_url}/{self.detail_item_key}/{detail_id}"
        headers = {"X-Api-Key": self.api_key}

        response = await make_request("get", endpoint, self.settings, headers=headers)
        return response.json()["monitored"]

    async def get_series(self):
        """Fetch download client information and return the implementation value."""
        endpoint = self.api_url + "/series"
        headers = {"X-Api-Key": self.api_key}
        response = await make_request("get", endpoint, self.settings, headers=headers)
        return response.json()
