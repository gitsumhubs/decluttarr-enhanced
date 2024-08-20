from src.settings._config_as_yaml import get_config_as_yaml
from src.settings._download_clients_qBit import QbitClients

class DownloadClients:
    """Represents all download clients."""
    qbittorrent = None
    download_client_types = [
        "qbittorrent",
    ]
    def __init__(self, config, settings):
        self._set_qbit_clients(config, settings)
        self.check_unique_download_client_types()

    def _set_qbit_clients(self, config, settings):
        download_clients = config.get("download_clients", {})
        if isinstance(download_clients, dict):
            self.qbittorrent = QbitClients(config, settings)
            if not self.qbittorrent: # Unsets settings in general section needed for qbit (if no qbit is defined)
                for key in [
                    "private_tracker_handling",
                    "public_tracker_handling",
                    "obsolete_tag",
                    "protected_tag",
                ]:
                    setattr(settings.general, key, None)

    def config_as_yaml(self):
        """Logs all download clients."""
        return get_config_as_yaml(
            {"qbittorrent": self.qbittorrent},
            sensitive_attributes={"username", "password", "cookie"},
            internal_attributes={ "api_url", "cookie", "settings", "min_version"},
            hide_internal_attr=True
        )


    def check_unique_download_client_types(self):
        """Ensures that all download client names are unique.
            This is important since downloadClient in arr goes by name, and 
            this is needed to link it to the right IP set up in the yaml config 
            (which may be different to the one donfigured in arr)"""

        seen = set()
        for download_client_type in self.download_client_types:
            download_clients = getattr(self, download_client_type, [])

            # Check each client in the list
            for client in download_clients:
                name = getattr(client, "name", None)
                if name is None:
                    raise ValueError(f'{download_client_type} client does not have a name ({client.base_url}).\nMake sure that the name corresponds with the name set in your *arr app for that download client.')

                if name.lower() in seen:
                    raise ValueError(f"Download client names must be unique. Duplicate name found: '{name}'\nMake sure that the name corresponds with the name set in your *arr app for that download client.")
                else:
                    seen.add(name.lower())

    def get_download_client_by_name(self, name: str):
        """Retrieve the download client and its type by its name."""
        name_lower = name.lower()
        for download_client_type in self.download_client_types:
            download_clients = getattr(self, download_client_type, [])

            # Check each client in the list
            for client in download_clients:
                if client.name.lower() == name_lower:
                    return client, download_client_type

        return None, None
