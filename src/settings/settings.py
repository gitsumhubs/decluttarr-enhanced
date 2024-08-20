from src.utils.log_setup import configure_logging
from src.settings._constants import Envs, MinVersions, Paths
# from src.settings._migrate_legacy import migrate_legacy
from src.settings._general import General
from src.settings._jobs import Jobs
from src.settings._download_clients import DownloadClients
from src.settings._instances import Instances
from src.settings._user_config import get_user_config

class Settings:
    
    min_versions = MinVersions()
    paths = Paths()

    def __init__(self):
        self.envs = Envs()
        config = get_user_config(self)
        self.general = General(config)
        self.jobs = Jobs(config)
        self.download_clients = DownloadClients(config, self)
        self.instances = Instances(config, self)
        configure_logging(self)


    def __repr__(self):
        sections = [
            ("ENVIRONMENT SETTINGS", "envs"),
            ("GENERAL SETTINGS", "general"),
            ("ACTIVE JOBS", "jobs"),
            ("JOB SETTINGS", "jobs"),
            ("INSTANCE SETTINGS", "instances"),
            ("DOWNLOAD CLIENT SETTINGS", "download_clients"),
        ]   
        messages = []
        messages.append("🛠️  Decluttarr - Settings 🛠️")
        messages.append("-"*80)
        messages.append("")
        for title, attr_name in sections:
            section = getattr(self, attr_name, None)
            section_content = section.config_as_yaml()   
            if title == "ACTIVE JOBS":
                messages.append(self._format_section_title(title))
                messages.append(self.jobs.list_job_status() + "\n")
            elif section_content != "{}\n":
                messages.append(self._format_section_title(title))
                messages.append(section_content + "\n")
        return "\n".join(messages)


    def _format_section_title(self, name, border_length=50, symbol="="):
        """Format section title with centered name and hash borders."""
        padding = max(border_length - len(name) - 2, 0)  # 4 for spaces
        left_hashes = right_hashes = padding // 2
        if padding % 2 != 0:
            right_hashes += 1
        return f"{symbol * left_hashes} {name} {symbol * right_hashes}\n"




