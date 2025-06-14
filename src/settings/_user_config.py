import os
from pathlib import Path
import yaml

from src.utils.log_setup import logger

CONFIG_MAPPING = {
    "general": [
        "LOG_LEVEL",
        "TEST_RUN",
        "TIMER",
        "SSL_VERIFICATION",
        "IGNORED_DOWNLOAD_CLIENTS",
    ],
    "job_defaults": [
        "MAX_STRIKES",
        "MIN_DAYS_BETWEEN_SEARCHES",
        "MAX_CONCURRENT_SEARCHES",
    ],
    "jobs": [
        "REMOVE_BAD_FILES",
        "REMOVE_FAILED_DOWNLOADS",
        "REMOVE_FAILED_IMPORTS",
        "REMOVE_METADATA_MISSING",
        "REMOVE_MISSING_FILES",
        "REMOVE_ORPHANS",
        "REMOVE_SLOW",
        "REMOVE_STALLED",
        "REMOVE_UNMONITORED",
        "SEARCH_UNMET_CUTOFF_CONTENT",
        "SEARCH_MISSING_CONTENT",
    ],
    "instances": ["SONARR", "RADARR", "READARR", "LIDARR", "WHISPARR"],
    "download_clients": ["QBITTORRENT"],
}


def get_user_config(settings):
    """
    Check if data is read from environment variables, or from yaml file.

    Reads from environment variables if in docker, unless in docker-compose "USE_CONFIG_YAML" is set to true.
    Then the config file is read.
    """
    config = {}
    if _config_file_exists(settings):
        config = _load_from_yaml_file(settings)
        settings.envs.use_config_yaml = True
    elif settings.envs.in_docker:
        config = _load_from_env()
    # Ensure all top-level keys exist, even if empty
    for section in CONFIG_MAPPING:
        if config.get(section) is None:
            config[section] = {}
    return config


def _load_from_env() -> dict:
    """
    Load and parse config from environment variables defined in CONFIG_MAPPING.

    Tries uppercase and lowercase keys, parses values as YAML,
    and lowercases dictionary keys in the result.

    Returns:
        dict: Config sections with parsed env var values.
    """
    config = {}

    for section, keys in CONFIG_MAPPING.items():
        section_config = {}

        for key in keys:
            raw_value = os.getenv(key) or os.getenv(key.lower())
            if raw_value is None:
                continue

            try:
                parsed_value = yaml.safe_load(raw_value)
                parsed_value = _lowercase(parsed_value)
            except yaml.YAMLError as e:
                logger.error(
                    f"Failed to parse environment variable {key} as YAML:\n{e}",
                )
                parsed_value = {}
            section_config[key.lower()] = parsed_value

        config[section] = section_config

    return config


def _lowercase(data):
    """Translate received keys (for instance setting-keys of jobs) to lower case."""
    if isinstance(data, dict):
        return {str(k).lower(): _lowercase(v) for k, v in data.items()}
    if isinstance(data, list):
        return [_lowercase(item) for item in data]
    # Leave strings and other types unchanged
    return data


def _config_file_exists(settings):
    config_path = settings.paths.config_file
    return Path(config_path).exists()


def _load_from_yaml_file(settings):
    """Read config from YAML file and returns a dict."""
    config_path = settings.paths.config_file
    try:
        with Path(config_path).open(encoding="utf-8") as file:
            return yaml.safe_load(file) or {}
    except yaml.YAMLError as e:
        logger.error("Error reading YAML file: %s", e)
        return {}
