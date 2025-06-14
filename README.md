_Like this app? Thanks for giving it a_ ⭐️

# **Decluttarr**

Looking to **upgrade from V1 to V2**? Look [here](#upgrading-from-v1-to-v2)
Note: Decluttarr 

## Table of contents
- [Overview](#overview)
- [Dependencies & Hints & FAQ](#dependencies--hints--faq)
- [Getting started](#getting-started)
  - [Running locally](#running-locally)
  - [Running in docker](#running-in-docker)
    - [Docker-compose with config file (recommended)](#docker-docker-compose-together-with-configyaml)
    - [Docker-compose only](#docker-specifying-all-settings-in-docker-compose)
- [Upgrading from V1 to V2](#upgrading-from-v1-to-v2)
- [Explanation of the settings](#explanation-of-the-settings)
  - [General](#general-settings)
    - [LOG_LEVEL](#log_level)
    - [TEST_RUN](#test_run)
    - [TIMER](#timer)
    - [SSL_VERIFICATION](#ssl_verification)
    - [IGNORE_DOWNLOAD_CLIENTS](#ignore_download_clients)
    - [PRIVATE_TRACKER_HANDLING / PUBLIC_TRACKER_HANDLING](#private_tracker_handling--public_tracker_handling)
    - [OBSOLETE_TAG](#obsolete_tag)
    - [PROTECTED_TAG](#protected_tag)
  - [Job Defaults](#job-defaults)
    - [max_strikes](#max_strikes)
    - [MIN_DAYS_BETWEEN_SEARCHES](#min_days_between_searches)
    - [MAX_CONCURRENT_SEARCHES](#max_concurrent_searches)
  - [Jobs](#jobs)
    - [REMOVE_BAD_FILES](#remove_bad_files)
    - [REMOVE_FAILED_DOWNLOADS](#remove_failed_downloads)
    - [REMOVE_FAILED_IMPORTS](#remove_failed_imports)
    - [REMOVE_METADATA_MISSING](#remove_metadata_missing)
    - [REMOVE_MISSING_FILES](#remove_missing_files)
    - [REMOVE_ORPHANS](#remove_orphans)
    - [REMOVE_SLOW](#remove_slow)
    - [REMOVE_STALLED](#remove_stalled)
    - [REMOVE_UNMONITORED](#remove_unmonitored)
    - [SEARCH_CUTOFF_UNMET_CONTENT](#search_unmet_cutoff_content)
    - [SEARCH_MISSING_CONTENT](#search_missing_content)
  - [Instances](#arr-instances)
    - [SONARR](#sonarr)
    - [RADARR](#radarr)
    - [READARR](#readarr)
    - [LIDARR](#lidarr)
    - [WHISPARR](#whisparr)
  - [Downloaders](#download-clients)
    - [QBITTORRENT](#qbittorrent)
- [Disclaimer](#disclaimer)

## Overview

Decluttarr is a helper tool that works with the *arr-application suite, and automates the clean-up for their download queues, keeping them free of stalled / redundant downloads. 

It supports [Radarr](https://github.com/Radarr/Radarr/), [Sonarr](https://github.com/Sonarr/Sonarr/), [Readarr](https://github.com/Readarr/Readarr/), [Lidarr](https://github.com/Lidarr/Lidarr/), and [Whisparr](https://github.com/Whisparr/Whisparr/).

Feature overview:

-   Preventing download of bad files and removing torrents with less than 100% availability (remove_bad_files)
-   Removing downloads that failed to download (remove_failed_downloads)
-   Removing downloads that failed to import (remove_failed_imports)
-   Removing downloads that are stuck downloading metadata (remove_metadata_missing)
-   Removing downloads that are missing files (remove_missing_files)
-   Removing downloads belonging to movies/series/albums/etc that have been deleted since the download was started (remove_orphans)
-   Removing downloads that are repeatedly have been found to be slow (remove_slow)
-   Removing downloads that are stalled (remove_stalled)
-   Removing downloads belonging to movies/series/albums etc. that have been marked as "unmonitored" (remove_unmonitored)
-   Periodically searching for better content on movies/series/albums etc. where cutoff has not been reached yet (search_cutoff_unmet_content)
-   Periodically searching for missing content that has not yet been found (search_missing_content)


Key behaviors:
-   Can handle torrents of private trackers and public trackers in different ways (they can be removed, be skipped entirely, or be tagged as 'obsolete', so that other programs can remove them once the seed targets have been reached)
-   If a job removes a download, it will automatically trigger a search for a new download, and remove the (partial) files downloaded thus far
-   Certain jobs add removed downloads automatically to the blocklists of the arr-applications, to prevent the same download from being grabbed again
-   If certain downloads should not be touched by decluttarr, they can be tagged with a protection-tag in Qbit 
-   You can test decluttarr, which shows you what decluttarr would do, without it actually doing it (test_run)
-   Decluttarr supports multiple instances (for instance, multiple Sonarr instances) as well as multiple qBittorrent instances

How to run this:
-   There are two ways how to run decluttarr. 
-   Either, decluttarr is run as local script (run main.py) and settings are maintained in a config.yaml
-   Alternatively, decluttarr is run as docker image. Here, either all settings can either be configured via docker-compose, or alternatively also the config.yaml is used
-   Check out [Getting started](#getting-started)


## Dependencies & Hints & FAQ

-   Use Sonarr v4 & Radarr v5, else certain features may not work correctly
-   qBittorrent is recommended but not required. If you don't use qBittorrent, you will experience the following limitations:
    -   When detecting slow downloads, the speeds provided by the \*arr apps will be used, which is less accurate than what qBittorrent returns when queried directly
    -   The feature that allows to protect downloads from removal (protected_tag) does not work
    -   The feature that distinguishes private and private trackers (private_tracker_handling, public_tracker_handling) does not work
    -   Removal of bad files and <100% availability (remove_bad_files) does not work 
-   If you see strange errors such as "found 10 / 3 times", consider turning on the setting "Reject Blocklisted Torrent Hashes While Grabbing". On nightly Radarr/Sonarr/Readarr/Lidarr/Whisparr, the option is located under settings/indexers in the advanced options of each indexer, on Prowlarr it is under settings/apps and then the advanced settings of the respective app
-   If you use qBittorrent and none of your torrents get removed and the verbose logs tell that all torrents are protected by the protected_tag even if they are not, you may be using a qBittorrent version that has problems with API calls, and you may want to consider switching to a different qBit image (see https://github.com/ManiMatter/decluttarr/issues/56)
-   Currently, “\*Arr” apps are only supported in English. Refer to issue https://github.com/ManiMatter/decluttarr/issues/132 for more details
-   If you experience yaml issues, please check the closed issues. There are different notations, and it may very well be that the issue you found has already been solved in one of the issues. Once you figured your problem, feel free to post your yaml to help others here: https://github.com/ManiMatter/decluttarr/issues/173


## Getting started

You can run decluttarr either as local python script, or as a docker container.

### Running locally

1. Clone the repository with `git clone -b latest https://github.com/ManiMatter/decluttarr.git`
Note: Do provide the `-b latest` in the clone command, else you will be pulling the dev branch which is not what you are after.
2. Rename the `config_example.yaml` inside the config folder to `config.yaml`
3. Tweak `config.yaml` to your needs
4. Install the libraries listed in the docker/requirements.txt (pip install -r requirements.txt)
5. Run the script with `python3 main.py`

Note: To turn a job on, it is enough to have it listed.
To deactivate, simply uncomment.

```
jobs:
  remove_bad_files:  # This is turned on
# remove_bad_files:  # This is turned off  

## Note that this is different from docker-compose (where both examples above would be turned off; in docker, "true" or additional options are required as value next to the key)
```



### Running in docker

In docker, there are two ways how you can run decluttarr.
The [recommended approach](#docker-docker-compose-together-with-configyaml) is to use a config.yaml file (similar to running the script [locally](#running-locally)).
Alternatively, you can put all settings [directly in your docker-compose](#docker-specifying-all-settings-in-docker-compose), which may bloat it a bit.


#### Docker: Docker-compose together with Config.yaml
1. Use the following input for your `docker-compose.yml`
2. Download the config_example.yaml from the config folder (on GitHub) and put it into your mounted folder
3. Rename it to config.yaml and adjust the settings to your needs
4. Run `docker-compose up -d` in the directory where the file is located to create the docker container

Note: Always pull the "**latest**" version. The "dev" version is for testing only, and should only be pulled when contributing code or supporting with bug fixes

```yaml
version: "3.3"
services:
  decluttarr:
    image: ghcr.io/manimatter/decluttarr:latest
    container_name: decluttarr
    restart: always
    environment:
      TZ: Europe/Zurich
      PUID: 1000
      PGID: 1000
    volumes:
      - $DOCKERDIR/appdata/decluttarr/config.yaml:/app/config/config.yaml
      # - $DOCKERDIR/appdata/decluttarr/logs:/app/logs # Uncomment to get logs in text file, too
```


#### Docker: Specifying all settings in docker-compose

As noted above, the [recommended approach for docker](#docker-docker-compose-together-with-configyaml) setups is usage of a config.yaml, as the below approach may bloat your docker-compose and may cause you some headache to adhere to all required notation rules of compose 

If you want to have everything in docker compose:
1. Use the following input for your `docker-compose.yml`
2. Tweak the settings to your needs
3. Remove the things that are commented out (if you don't need them), or uncomment them
4. If you face problems with yaml formats etc., please first check the open and closed issues on GitHub, before opening new ones
5. Run `docker-compose up -d` in the directory where the file is located to create the docker container

Note: Always pull the "**latest**" version. The "dev" version is for testing only, and should only be pulled when contributing code or supporting with bug fixes
```yaml
version: "3.3"
services:
  decluttarr:
    image: ghcr.io/manimatter/decluttarr:latest
    container_name: decluttarr
    restart: always
    environment:
      TZ: Europe/Zurich
      PUID: 1000
      PGID: 1000

      LOG_LEVEL: INFO
      TEST_RUN: True
      TIMER: 10
      # IGNORED_DOWNLOAD_CLIENTS: >
      #   - emulerr
      # SSL_VERIFICATION: true
      # PRIVATE_TRACKER_HANDLING: "obsolete_tag"
      # PUBLIC_TRACKER_HANDLING: "remove"
      # OBSOLETE_TAG: "Obsolete"
      # PROTECTED_TAG: "Keep"

      # # --- Optional: Job Defaults ---
      # You can use these to set those parameters across all jobs. If you don't specify it here, the defaults set by system will be used
      # If you set job-specific parameters (further down below), they will override these settings.
      # max_strikes: 3
      # MIN_DAYS_BETWEEN_SEARCHES: 7
      # MAX_CONCURRENT_SEARCHES: 3

      # # --- Jobs (short notation) ---
      # If you want to go with the most basic settings, you can just turn them all on:
      REMOVE_BAD_FILES: True
      REMOVE_FAILED_DOWNLOADS: True
      REMOVE_FAILED_IMPORTS: True
      REMOVE_METADATA_MISSING: True
      REMOVE_MISSING_FILES: True
      REMOVE_ORPHANS: True
      REMOVE_SLOW: True
      REMOVE_STALLED: True
      REMOVE_UNMONITORED: True
      SEARCH_BETTER_CONTENT: True
      SEARCH_MISSING_CONTENT: True

      # # --- OR: Jobs (with job-specific settings) ---
      # Alternatively, you can use the below notation, which for certain jobs allows you to set additional parameters
      # As written above, these can also be set as Job Defaults so you don't have to specify them as granular as below.
      # REMOVE_BAD_FILES: |
      #   keep_archives: True
      # REMOVE_FAILED_DOWNLOADS: True
      # REMOVE_FAILED_IMPORTS: |
      #   message_patterns:
      #     - "Not a Custom Format upgrade for existing*"
      #     - "Not an upgrade for existing*"
      #     - "*Found potentially dangerous file with extension*"
      # REMOVE_METADATA_MISSING: |
      #   max_strikes: 3
      # REMOVE_MISSING_FILES: True
      # REMOVE_ORPHANS: True
      # REMOVE_SLOW: |
      #   min_speed: 100
      #   max_strikes: 3
      # REMOVE_STALLED: |
      #   max_strikes: 3
      # REMOVE_UNMONITORED: True
      # SEARCH_UNMET_CUTOFF_CONTENT: |
      #   min_days_between_searches: 7
      #   max_concurrent_searches: 3
      # SEARCH_MISSING_CONTENT: |
      #   min_days_between_searches: 7
      #   max_concurrent_searches: 3

      # --- Instances ---
      SONARR: >
        - base_url: "http://sonarr1:8989"
          api_key: "$SONARR_API_KEY"
        - base_url: "http://sonarr2:8989"
          api_key: "$SONARR_API_KEY"

      # RADARR: >
      #   - base_url: "http://radarr:7878"
      #     api_key: "$RADARR_API_KEY"

      # READARR: >
      #   - base_url: "http://readarr:8787"
      #     api_key: "$READARR_API_KEY"

      # LIDARR: >
      #   - base_url: "http://lidarr:8686"
      #     api_key: "$LIDARR_API_KEY"

      # WHISPARR: >
      #   - base_url: "http://whisparr:6969"
      #     api_key: "$WHISPARR_API_KEY"

      # --- Download Clients ---
      QBITTORRENT: >
        - base_url: "http://qbittorrent:8080"
          # username: "$QBIT_USERNAME" # (optional -> if not provided, assuming not needed)
          # password: "$QBIT_PASSWORD" # (optional -> if not provided, assuming not needed)
          # name: "qBittorrent" # (optional -> if not provided, assuming "qBittorrent". Must correspond with what is specified in your *arr as download client name)

    volumes:
      # - $DOCKERDIR/appdata/decluttarr/logs:/app/logs # Uncomment to get logs in text file, too
```
## Upgrading from V1 to V2

Decluttarr v2 is a major update with a cleaner config format and powerful new features. Here's what changed and how to upgrade.
---

### ✨ What’s New

- 🔁 **YAML in local setups**: For local setups: Replaced config.conf file with config.yaml, offering better readability and more granular / explicit control
- 🐳 **YAML in container setups**: Same YAML config.yaml can be used when running in container setups; previuosly, external configs were not possible
- 💥 **Multi-instance support**: Decluttarr can now handle multiple Sonarr/Radarr etc. instances, as well as multiple qBittorrent Instances
- 🧼 **Bad files handling**: Added ability to not download potentially malicious files and files such as trailers / samples
- 🐌 **Adaptive slowness**: Slow downloads-removal can be dynamically turned on/off depending on overall bandwidth usage
- 📄 **Log files**: Logs can now be retrieved from a log file
- 📌 **Removal behavior**: Rather than removing downloads, they can now also be tagged for later removal (ie. to allow for seed targets to be reached first). This can be done separately for private and public trackers

---

### ⚠️ Breaking Changes

V1 and V2 are not compatible, and some configurations have been changed.
Also, the structure of the config files / docker-compose keys are different.

Thus please check out [How to migrate](#️-how-to-migrate).

Below are **examples** how keys have changed.

| v1                              | v2                                 |
|----------------------------------|-------------------------------------|
| `REMOVE_TIMER`                  | `timer`                             |
| `PERMITTED_ATTEMPTS`            | `max_strikes`                       |
| `NO_STALLED_REMOVAL_QBIT_TAG`   | `protected_tag`                     |
| `REMOVE_FAILED`   | `remove_failed_downloads`                     |
| `RUN_PERIODIC_RESCANS`          | `search_better_content`, `search_missing_content` |
| `MIN_DAYS_BEFORE_RESCAN`   | `min_days_between_searches`                     |
| `MIN_DOWNLOAD_SPEED`   | `min_speed`                     |
---

### 🛠️ How to Migrate

- Best approach: check the [Getting Started](https://github.com/ManiMatter/decluttarr/tree/decluttarr-v2?tab=readme-ov-file#getting-started) section and use the example configs as a starting point.


## Explanation of the settings

### **General settings**

Configures the general behavior of the application (across all features)


#### LOG_LEVEL

-   Sets the level at which logging will take place
-   `INFO` will only show changes applied to radarr/sonarr/lidarr/readarr/whisparr
-   `VERBOSE` shows each check being performed even if no change is applied
-   `DEBUG` shows very granular information, only required for debugging
-   Type: String
-   Permissible Values: CRITICAL, ERROR, WARNING, INFO, VERBOSE, DEBUG
-   Is Mandatory: No (Defaults to INFO)
-   Note:
    - Logs are also written into the file /temp/logs.txt inside the decluttarr directory
    - If you run decluttarr inside docker, mount this file as volume (see docker-compose examples) to see them in your host system

#### TEST_RUN

-   Allows you to safely try out this tool. If active, downloads will not be removed
-   Type: Boolean
-   Permissible Values: True, False
-   Is Mandatory: No (Defaults to False)

#### TIMER

-   Sets the frequency of how often the queue is checked for orphan and stalled downloads
-   Type: Integer
-   Unit: Minutes
-   Is Mandatory: No (Defaults to 10)

#### SSL_VERIFICATION

-   Turns SSL certificate verification on or off for all API calls
-   `True` means that the SSL certificate verification is on
-   Warning: It's important to note that disabling SSL verification can have security implications, as it makes the system vulnerable to man-in-the-middle attacks. It should only be done in a controlled and secure environment where the risks are well understood and mitigated
-   Type: Boolean
-   Permissible Values: True, False
-   Is Mandatory: No (Defaults to True)

#### IGNORE_DOWNLOAD_CLIENTS

-   Allows you to configure download client names that will be skipped by decluttarr
    Note: The names provided here have to 100% match with how you have named your download clients in your *arr application(s)
-   Type: List of strings
-   Is Mandatory: No (Defaults to [], i.e. nothing ignored])

#### PRIVATE_TRACKER_HANDLING / PUBLIC_TRACKER_HANDLING

-   Defines what happens with private/public tracker torrents if they are flagged by a removal job
-   Note that this only works for qbittorrent currently (if you set up qbittorrent in your config)
    -   "remove" means that torrents are removed (default behavior)
    -   "skip" means they are disregarded (which some users might find handy to protect their private trackers prematurely, i.e., before their seed targets are met)
    -   "obsolete_tag" means that rather than being removed, the torrents are tagged. This allows other applications (such as [qbit_manage](https://github.com/StuffAnThings/qbit_manage) to monitor them and remove them once seed targets are fulfilled)
-   Type: String
-   Permissible Values: remove, skip, obsolete_tag
-   Is Mandatory: No (Defaults to remove)


#### OBSOLETE_TAG
-   Only relevant in conjunction with PRIVATE_TRACKER_HANDLING / PUBLIC_TRACKER_HANDLING
-   If either of these two settings are set to "obsolete_tag", then this setting can be used to define the tag that has to be applied
-   Type: String
-   Permissible Values: Any
-   Is Mandatory: No (Defaults to "Obsolete")


#### PROTECTED_TAG
-   If you do not want a given torrent being removed by decluttarr in any circumstance, you can use this feature to protect it from being removed
-   Go to qBittorrent and mark the torrent with the tag you define here - it won't be touched
-   Note that this only works for qbittorrent currently (if you set up qbittorrent in your config)
-   Type: String
-   Permissible Values: Any
-   Is Mandatory: No (Defaults to "Keep")

---

### **Job Defaults**

Certain jobs take in additional configuration settings. If you want to define these settings globally (for all jobs to which they apply), you can do this here. 

If a job has the same settings configured on job-level, the job-level settings will take precedence.

#### max_strikes

-   Certain jobs wait before removing a download, until the jobs have caught the same download a given number of times. This is defined by max_strikes
-   max_strikes defines the number of consecutive times a download can fail before it is removed.
-   If a download temporarily recovers the count is reset (for instance being caught twice for being slow and then picking up speed again before again being slow) 
-   Type: Integer
-   Unit: Number of consecutive misses
-   Is Mandatory: No (Defaults to 3)

#### MIN_DAYS_BETWEEN_SEARCHES

-   Only relevant together with search_unmet_cutoff_content and search_missing_content
-   Specified how many days should elapse before decluttarr tries to search for a given wanted item again
-   Type: Integer
-   Permissible Values: Any number
-   Is Mandatory: No (Defaults to 7)

#### MAX_CONCURRENT_SEARCHES

-   Only relevant together with search_unmet_cutoff_content and search_missing_content
-   Specified how many ites concurrently on a single arr should be searched for in a given iteration
-   Each arr counts separately
-   Example: If your wanted-list has 100 entries, and you define "3" as your number, after roughly 30 searches you'll have all items on your list searched for.
-   Since the timer-setting steer how often the jobs run, if you put 10minutes there, after one hour you'll have run 6x, and thus already processed 18 searches. Long story short: No need to put a very high number here (else you'll just create unnecessary traffic on your end.).
-   Type: Integer
-   Permissible Values: Any number
-   Is Mandatory: No (Defaults to 3)

### **Jobs**

This is the interesting section. It defines which job you want decluttarr to run for you.

#### REMOVE_BAD_FILES

- Steers whether files within torrents are marked as 'not download' if they match one of these conditions
  1) They are less than 100% available
  2) They are not one of the desired file types supported by the *arr apps:
  3) They contain one of these words (case-insensitive) and are smaller than 500 MB:
     - Trailer
     - Sample

-   If all files of a torrent are marked as 'not download' then the torrent will be removed and blacklisted
-   Note that this is only supported when qBittorrent is configured in decluttarr, and it will turn on the setting 'Keep unselected files in ".unwanted" folder' in qBittorrent 
-   Type: Boolean or Dict
-   Permissible Values: True, False or keep_archives (bool)
-   Is Mandatory: No (Defaults to False)
-   Note: 
      - If you turn keep_archives on (default: false), packaged files (rar, zip, 7zip, etc.) are not removed
      - This may be helpful if you use a tool such as [unpackerr](https://github.com/Unpackerr/unpackerr) that can handle it
      - However, you may also find that these packages may contain bad/malicious files (which will not removed by decluttarr)

#### REMOVE_FAILED_DOWNLOADS

-   Steers whether downloads that are marked as "failed" are removed from the queue
-   Blocklisted: Yes (same download won't be loaded again)
-   Type: Boolean
-   Permissible Values: True, False
-   Is Mandatory: No (Defaults to False)

#### REMOVE_FAILED_IMPORTS

-   Steers whether downloads that have failed to import are removed from the queue
-   Blocklisted: No
-   Type: Boolean or Dict
-   Permissible Values: True, False or message_patterns (with a list)
-   Is Mandatory: No (Defaults to False)
-   Note: 
      - You can use the message_pattern to limit which type of failed imports are removed
      - If you specify message_patterns instead of a bool, this will automatically be turned on
      - Message patterns are exact match, unless you use wild cards ("Failed" will not match "Failed Import" but "Failed*" will)

#### REMOVE_METADATA_MISSING

-   Steers whether downloads stuck obtaining metadata are removed from the queue
-   Blocklisted: Yes
-   Type: Boolean or Dict
-   Permissible Values: True, False or max_strikes (int)
-   Is Mandatory: No (Defaults to False)
-   Note:
      - With max_strikes you can define how many times this torrent can be caught before being removed
      - Instead of configuring it here, you may also configure it as a default across all jobs or use the built-in defaults (see further above under "max_strikes")

#### REMOVE_MISSING_FILES

-   Steers whether downloads that have the warning "Files Missing" are removed from the queue
-   Blocklisted: No
-   Type: Boolean
-   Permissible Values: True, False
-   Is Mandatory: No (Defaults to False)

#### REMOVE_ORPHANS

-   Steers whether orphan downloads are removed from the queue
-   Orphan downloads are those that do not belong to any requested media anymore (Since the media was removed from radarr/sonarr/lidarr/readarr/whisparr after the download started)
-   Blocklisted: Yes
-   Type: Boolean
-   Permissible Values: True, False
-   Is Mandatory: No (Defaults to False)

#### REMOVE_SLOW

-   Steers whether slow downloads are removed from the queue
-   Blocklisted: Yes
-   Note: 
      - Does not apply to usenet downloads (since there users pay for certain speed, slowness should not occur)
      - Applies only if qBittorrent is configured: The remove_slow check is automatically temporarily disabled if qBittorrent is already using more than 80% of your available download bandwidth.
        For this to work, you must set a Global Download Rate Limit in qBittorrent. Otherwise, unlimited capacity is assumed, and the auto-disable feature will never trigger.
        Make sure to configure the limit in the correct place — either the standard or the alternative limits, depending on which one is active in your setup.
-   Type: Boolean or Dict
-   Permissible Values: 
      If bool: True, False 
      If Dict: min_speed, max_strikes
-   Is Mandatory: No (Defaults to False)
-   Note:
      - With min_speed you can define the minimum average speed in KB/s that a download must have achieved between two checks
      - If not provided, 100 KB/s is used

#### REMOVE_STALLED

-   Steers whether stalled downloads with no connections are removed from the queue
-   Blocklisted: Yes
-   Type: Boolean or Dict
-   Permissible Values: True, False or max_strikes (int)
-   Is Mandatory: No (Defaults to False)

#### REMOVE_UNMONITORED

-   Steers whether downloads belonging to unmonitored media are removed from the queue
-   Note: Will only remove from queue if all TV shows depending on the same download are unmonitored
-   Blocklisted: False
-   Note: Since sonarr does not support multi-season packs, if you download one you should protect it with `PROTECTED_TAG` that was explained above 
-   Type: Boolean
-   Permissible Values: True, False
-   Is Mandatory: No (Defaults to False)

#### SEARCH_UNMET_CUTOFF_CONTENT

-   Steers whether searches are automatically triggered for items that are wanted and have not yet met the cutoff
-   Type: Boolean or Dict
-   Permissible Values: 
    - If Bool: True, False 
    - If Dict: min_days_between_searches, max_concurrent_searches
-   Is Mandatory: No (Defaults to False)
-   Note:
      - You can also specify min_days_between_searches and max_concurrent_searches as job defaults (see above) or simply rely on the system defaults

#### SEARCH_MISSING_CONTENT

-   Steers whether searches are automatically triggered for items that are missing
-   Type: Boolean or Dict
-   Permissible Values: 
    - If Bool: True, False 
    - If Dict: min_days_between_searches, max_concurrent_searches
-   Is Mandatory: No (Defaults to False)
-   Note:
      - You can also specify min_days_between_searches and max_concurrent_searches as job defaults (see above) or simply rely on the system defaults

---

### **Arr Instances**

Defines arr-instances on which download queue should be decluttered

#### Radarr
-   List of instances of radarr
-   Type: List of radarr instances
-   Keys per instance (all required)
    - base_url: URL under which the instance can be reached
    - api_key
-   Is Mandatory: No (Defaults to empty list)

#### Sonarr
- Equivalent of [Radarr](#radarr)
#### Readarr
- Equivalent of [Radarr](#radarr)
#### Lidarr
- Equivalent of [Radarr](#radarr)
#### Whisparr
- Equivalent of [Radarr](#radarr)


---

### **Download Clients**

Certain jobs need access directly to the download clients, as the arr instances don't offer all the relevant APIs / data.
You can perfectly use decluttarr without this; just certain features won't be available (as documented above).

For time being, only qbittorrent is supported.

#### QBITTORRENT
-   List of qbittorrent instances
-   Type: List of qbit instances
-   Keys per instance
    - base_url: URL under which the qbit can be reached (mandatory)
    - username: Optional - only needed if your qbit requires authentication (which you may not need if you have configured qbit in a way that it disables it for local connections)
    - password: Optional - see above
    - name: Optional. Needs to correspond with the name that you have set up in your Arr instance. Defaults to "qBittorrent"


## Disclaimer

This script comes free of any warranty, and you are using it at your own risk
