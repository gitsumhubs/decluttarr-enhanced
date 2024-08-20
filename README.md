_Like this app? Thanks for giving it a_ ⭐️

# **Decluttarr**

## Table of contents

-   [Overview](#overview)
-   [Dependencies & Hints & FAQ](#dependencies--hints--faq)
-   [Getting started](#getting-started)
-   [Explanation of the settings](#explanation-of-the-settings)
-   [Disclaimer](#disclaimer)

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
-   Removing downloads that are stalled
-   Removing downloads belonging to movies/series/albums etc. that have been marked as "unmonitored"
-   Periodically searching for better content on movies/series/albums etc. where cutoff has not been reached yet
-   Periodcially searching for missing content that has not yet been found


Key behaviors:
-   Torrents of private trackers and public trackers in different ways (they can be removed, be skipped entirely, or be tagged as 'obsolete', so that other programs can remove them once the seed targets have been reached)
-   If a job removes a download, it will automatically trigger a search for a new download, and remove the (partial) files downloaded thus far
-   Certain jobs add removed downloads automatically to the blocklists of the arr-applications, to prevent the same download from being grabbed again
-   If certain downloads should not be touched by decluttarr, they can be tagged with a protection-tag in Qbit 
-   You can test decluttarr, which shows you what decluttarr would do, without it actually doing it (test_run)
-   Decluttarr supports multiple instances (for instance, multiple Sonarr instances) as well as multiple qBittorrent instances

How to run this:
-   There are two ways how to run decluttarr. 
-   Either, decluttarr is run as local script (run main.py) and settings are maintained in a config.yaml
-   Alternatively, delcuttarr is run as docker image. Here, either all settings can either be configured via docker-compose, or alternatively also the config.yaml is used
-   Check out [Getting started](#getting-started)


## Dependencies & Hints & FAQ

-   Use Sonarr v4 & Radarr v5, else certain features may not work correctly
-   qBittorrent is recommended but not required. If you don't use qBittorrent, you will experience the following limitations:
    -   When detecting slow downloads, the speeds provided by the \*arr apps will be used, which is less accurate than what qBittorrent returns when queried directly
    -   The feature that allows to protect downloads from removal (protected_tag) does not work
    -   The feature that distinguishes private and private trackers (private_tracker_handling, public_tracker_handling) does not work
    -   Removal of bad files and <100% availabiltiy (remove_bad_files) does not work 
-   If you see strange errors such as "found 10 / 3 times", consider turning on the setting "Reject Blocklisted Torrent Hashes While Grabbing". On nightly Radarr/Sonarr/Readarr/Lidarr/Whisparr, the option is located under settings/indexers in the advanced options of each indexer, on Prowlarr it is under settings/apps and then the advanced settings of the respective app
-   If you use qBittorrent and none of your torrents get removed and the verbose logs tell that all torrents are protected by the protected_tag even if they are not, you may be using a qBittorrent version that has problems with API calls and you may want to consider switching to a different qBit image (see https://github.com/ManiMatter/decluttarr/issues/56)
-   Currently, “\*Arr” apps are only supported in English. Refer to issue https://github.com/ManiMatter/decluttarr/issues/132 for more details
-   If you experience yaml issues, please check the closed issues. There are different notations, and it may very well be that the issue you found has already been solved in one of the issues. Once you figured your problem, feel free to post your yaml to help others here: https://github.com/ManiMatter/decluttarr/issues/173


## Getting started

There's two (and a half) ways to run this:
-   As a docker container with docker-compose, whilst leaving the detailed configuration in a separate yaml file (see [Method 1](#method-1-docker-with-config-file)). This is the __recommended setup__ when running in docker
-   As a docker container with docker-compose, with all configuration in your docker-compose (can be lengthy) (see [Method 2](#method-1-docker-with-config-file-recommended-setup))
-   By cloning the repository and running the script locally (see [Method 3](#method-3-running-locally))

The ways are explained below and there's an explanation for the different settings below that

### Method 1: Docker (with config file) __[recommended setup]__
1. Use the following input for your `docker-compose.yml`
2. Download the config_example.yaml from the config folder (on github) and put it into your mounted folder
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
      - $DOCKERDIR/appdata/decluttarr/config.yaml:/config/config.yaml
```


### Method 2: Docker (without config file)

1. Use the following input for your `docker-compose.yml`
2. Tweak the settings to your needs
3. Remove the things that are commented out (if you don't need them), or uncomment them
4. If you face problems with yaml formats etc, please first check the open and closed issues on github, before opening new ones
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

      # general settings
      GENERAL: >
        {
          "log_level": "VERBOSE",
          "test_run": true,
          "timer": 10,
          "ignored_download_clients": [],
          "ssl_verification": true
          // "private_tracker_handling": "obsolete_tag", // remove, skip, obsolete_tag. Optional. Default: remove
          // "public_tracker_handling": "remove", // remove, skip, obsolete_tag. Optional. Default: remove
          // "obsolete_tag": "Obsolete", // optional. Default: "Obsolete"
          // "protected_tag": "Keep" // optional. Default: "Keep"
        }

      # job defaults
      JOB_DEFAULTS: >
        {
          "max_strikes": 3,
          "min_days_between_searches": 7,
          "max_concurrent_searches": 3
        }

      # jobs
      JOBS: >
        {
          "remove_bad_files": {},
          "remove_failed_downloads": {},
          "remove_failed_imports": {
            // "message_patterns": ["*"]
          },
          "remove_metadata_missing": {
            // "max_strikes": 3
          },
          "remove_missing_files": {},
          "remove_orphans": {},
          "remove_slow": {
            // "min_speed": 100,
            // "max_strikes": 3
          },
          "remove_stalled": {
            // "max_strikes": 3
          },
          "remove_unmonitored": {},
          "search_unmet_cutoff_content": {
            // "min_days_between_searches": 7,
            // "max_concurrent_searches": 3
          },
          "search_missing_content": {
            // "min_days_between_searches": 7,
            // "max_concurrent_searches": 3
          }
        }

      # instances
      INSTANCES: >
        {
          "sonarr": [
            { "base_url": "http://sonarr:8989", "api_key": "xxxx" }
          ],
          "radarr": [
            { "base_url": "http://radarr:7878", "api_key": "xxxx" }
          ],
          "readarr": [
            { "base_url": "http://readarr:8787", "api_key": "xxxx" }
          ],
          "lidarr": [
            { "base_url": "http://lidarr:8686", "api_key": "xxxx" }
          ],
          "whisparr": [
            { "base_url": "http://whisparr:6969", "api_key": "xxxx" }
          ]
        }

      # download clients
      DOWNLOAD_CLIENTS: >
        {
          "qbittorrent": [
            {
              "base_url": "http://qbittorrent:8080"
              // "username": "xxxx", // optional
              // "password": "xxxx", // optional
              // "name": "qBittorrent" // optional; must match client name in *arr
            }
          ]
        }

```
    environment:
      <<: *default-tz-puid-pgid
      LOG_LEVEL: DEBUG
      TEST_RUN: True
      TIMER: 10
      # IGNORED_DOWNLOAD_CLIENTS: |
      #   - emulerr
      # SSL_VERIFICATION: true

      # # --- Optional: Job Defaults ---
      # MAX_STRIKES: 3
      # MIN_DAYS_BETWEEN_SEARCHES: 7
      # MAX_CONCURRENT_SEARCHES: 3

      # # --- Jobs (short notation) ---
      # REMOVE_BAD_FILES: True
      # REMOVE_FAILED_DOWNLOADS: True
      # REMOVE_FAILED_IMPORTS: True
      # REMOVE_METADATA_MISSING: True
      # REMOVE_MISSING_FILES: True
      # REMOVE_ORPHANS: True
      # REMOVE_SLOW: True
      # REMOVE_STALLED: True
      # REMOVE_UNMONITORED: True
      # SEARCH_BETTER_CONTENT: True
      # SEARCH_MISSING_CONTENT: True

      # # --- OR: Jobs (with job-specific settings) ---
      # REMOVE_BAD_FILES: True
      # REMOVE_FAILED_DOWNLOADS: True
      # REMOVE_FAILED_IMPORTS:
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
      # SEARCH_BETTER_CONTENT: |
      #   min_days_between_searches: 7
      #   max_concurrent_searches: 3
      # SEARCH_MISSING_CONTENT: |
      #   min_days_between_searches: 7
      #   max_concurrent_searches: 3

      # --- Instances ---
      SONARR: |
        - base_url: "http://sonarr:8989"
          api_key: "bdc9d74fdb2b4627aec1cf6c93ed2b2d"

      RADARR: |
        - base_url: "http://radarr:7878"
          api_key: "9412e07e582d4f9587fb56e8777ede10"

      # READARR: |
      #   - base_url: "http://readarr:8787"
      #     api_key: "e65e8ad6cdb6434289df002b20a27dc3"

      # --- Download Clients ---
      QBITTORRENT: |
        - base_url: "http://qbittorrent:8080"





### Method 3: Running locally

1. Clone the repository with `git clone -b latest https://github.com/ManiMatter/decluttarr.git`
Note: Do provide the `-b latest` in the clone command, else you will be pulling the dev branch which is not what you are after.
2. Rename the `config_example.yaml` inside the config folder to `config.yaml`
3. Tweak `config.yaml` to your needs
4. Install the libraries listed in the docker/requirements.txt (pip install -r requirements.txt)
5. Run the script with `python3 main.py`

## Explanation of the settings

### **General settings**

Configures the general behavior of the application (across all features)

**LOG_LEVEL**

-   Sets the level at which logging will take place
-   `INFO` will only show changes applied to radarr/sonarr/lidarr/readarr/whisparr
-   `VERBOSE` shows each check being performed even if no change is applied
-   `DEBUG` shows very granular information, only required for debugging
-   Type: String
-   Permissible Values: CRITICAL, ERROR, WARNING, INFO, VERBOSE, DEBUG
-   Is Mandatory: No (Defaults to INFO)

**TEST_RUN**

-   Allows you to safely try out this tool. If active, downloads will not be removed
-   Type: Boolean
-   Permissible Values: True, False
-   Is Mandatory: No (Defaults to False)

**TIMER**

-   Sets the frequency of how often the queue is checked for orphan and stalled downloads
-   Type: Integer
-   Unit: Minutes
-   Is Mandatory: No (Defaults to 10)

**SSL_VERIFICATION**

-   Turns SSL certificate verification on or off for all API calls
-   `True` means that the SSL certificate verification is on
-   Warning: It's important to note that disabling SSL verification can have security implications, as it makes the system vulnerable to man-in-the-middle attacks. It should only be done in a controlled and secure environment where the risks are well understood and mitigated
-   Type: Boolean
-   Permissible Values: True, False
-   Is Mandatory: No (Defaults to True)

**IGNORE_DOWNLOAD_CLIENTS**

-   Allows you to configure download client names that will be skipped by decluttarr
    Note: The names provided here have to 100% match with how you have named your download clients in your *arr application(s)
-   Type: List of strings
-   Is Mandatory: No (Defaults to [], ie. nothing ignored])

**PRIVATE_TRACKER_HANDLING / PUBLIC_TRACKER_HANDLING**

-   Defines what happens with private/public tracker torrents if they are flagged by a removal job
-   Note that this only works for qbittorrent currently (if you set up qbittorrent in your config)
    -   "remove" means that torrents are removed (default behavior)
    -   "skip" means they are disregarded (which some users might find handy to protect their private trackers prematurely, ie., before their seed targets are met)
    -   "obsolete_tag" means that rather than being removed, the torrents are tagged. This allows other applications (such as [qbit_manage](https://github.com/StuffAnThings/qbit_manage) to monitor them and remove them once seed targets are fulfilled
-   Type: String
-   Permissible Values: remove, skip, obsolete_tag
-   Is Mandatory: No (Defaults to remove)


**OBSOLETE_TAG**
-   Only relevant in conjunction with PRIVATE_TRACKER_HANDLING / PUBLIC_TRACKER_HANDLING
-   If either of these two settings are set to "obsolete_tag", then this setting can be used to define the tag that has to be applied
-   Type: String
-   Permissible Values: Any
-   Is Mandatory: No (Defaults to "Obsolete")


**PROTECTED_TAG**
-   If you do not want a given torrent being removed by decluttarr in any circumstance, you can use this feature to protect it from being removed
-   Go to qBittorrent and mark the torrent with the tag you define here - it won't be touched
-   Note that this only works for qbittorrent currently (if you set up qbittorrent in your config)
-   Type: String
-   Permissible Values: Any
-   Is Mandatory: No (Defaults to "Keep")

---

---

### **Job Defaults**

Certain jobs take in additional configuration settings. If you want to define these settings globally (for all jobs to which they apply), you can do this here. 

If a job has the same settings configured on job-level, the job-level settings will take precedence.

**MAX_STRIKES**

-   Certain jobs wait before removing a download, until the jobs have caught the same download a given number of times. This is defined by max_strikes
-   max_strikes defines the total permissible counts a job can catch a download; catching it once more, and it will remove the ownload.
-   Type: Integer
-   Unit: Number of times the job catches a download
-   Is Mandatory: No (Defaults to 3)

**MIN_DAYS_BETWEEN_SEARCHES**

-   Only relevant together with search_unmet_cutoff_content and search_missing_content
-   Specified how many days should elapse before decluttarr tries to search for a given wanted item again
-   Type: Integer
-   Permissible Values: Any number
-   Is Mandatory: No (Defaults to 7)

**MAX_CONCURRENT_SEARCHES**

-   Only relevant together with search_unmet_cutoff_content and search_missing_content
-   Specified how many ites concurrently on a single arr should be search for in a given iteration
-   Each arr counts separately
-   Example: If your wanted-list has 100 entries, and you define "3" as your number, after roughly 30 searches you'll have all items on your list searched for.
-   Since the timer-setting steer how often the jobs run, if you put 10minutes there, after one hour you'll have run 6x, and thus already processed 18 searches. Long story short: No need to put a very high number here (else you'll just create unecessary traffic on your end..).
-   Type: Integer
-   Permissible Values: Any number
-   Is Mandatory: No (Defaults to 3)

### **Jobs**

This is the interesting section. It defines which job you want decluttarr to run for you.
CONTINUE HEREEEEEEEE


**REMOVE_METADATA_MISSING**

-   Steers whether downloads stuck obtaining metadata are removed from the queue
-   These downloads are added to the blocklist, so that they are not re-requested
-   A new download from another source is automatically added by radarr/sonarr/lidarr/readarr/whisparr (if available)
-   Type: Boolean
-   Permissible Values: True, False
-   Is Mandatory: No (Defaults to False)

**REMOVE_MISSING_FILES**

-   Steers whether downloads that have the warning "Files Missing" are removed from the queue
-   These downloads are not added to the blocklist
-   Type: Boolean
-   Permissible Values: True, False
-   Is Mandatory: No (Defaults to False)

**REMOVE_ORPHANS**

-   Steers whether orphan downloads are removed from the queue
-   Orphan downloads are those that do not belong to any requested media anymore (Since the media was removed from radarr/sonarr/lidarr/readarr/whisparr after the download started)
-   These downloads are not added to the blocklist
-   Type: Boolean
-   Permissible Values: True, False
-   Is Mandatory: No (Defaults to False)

**REMOVE_SLOW**

-   Steers whether slow downloads are removed from the queue
-   Slow downloads are added to the blocklist, so that they are not re-requested in the future
-   Note: Does not apply to usenet downloads (since there users pay for certain speed, slowness should not occurr)
-   Type: Boolean
-   Permissible Values: True, False
-   Is Mandatory: No (Defaults to False)

**REMOVE_STALLED**

-   Steers whether stalled downloads with no connections are removed from the queue
-   These downloads are added to the blocklist, so that they are not re-requested in the future
-   Type: Boolean
-   Permissible Values: True, False
-   Is Mandatory: No (Defaults to False)

**REMOVE_UNMONITORED**

-   Steers whether downloads belonging to unmonitored media are removed from the queue
-   Note: Will only remove from queue if all TV shows depending on the same download are unmonitored
-   These downloads are not added to the blocklist
-   Note: Since sonarr does not support multi-season packs, if you download one you should protect it with `NO_STALLED_REMOVAL_QBIT_TAG` that is explained further down
-   Type: Boolean
-   Permissible Values: True, False
-   Is Mandatory: No (Defaults to False)

**SKIP_FILES**
- Steers whether files within torrents are marked as 'not download' if they match one of these conditions
  1) They are less than 100% available
  2) They are not one of the desired file types supported by the *arr apps:
  3) They contain one of these words (case insensitive) and are smaller than 500 MB:
     - Trailer
     - Sample

- If all files of a torrent are marked as 'not download' then the torrent will be removed and blacklisted
- Note that this is only supported when qBittorrent is configured in decluttarr and it will turn on the setting 'Keep unselected files in ".unwanted" folder' in qBittorrent 
- Type: Boolean
- Permissible Values: True, False
- Is Mandatory: No (Defaults to False)

**RUN_PERIODIC_RESCANS**

-   Steers whether searches are automatically triggered for items that are missing or have not yet met the cutoff
-   Note: Only supports Radarr/Sonarr currently (Lidarr depending on: https://github.com/Lidarr/Lidarr/pull/5084 / Readarr Depending on: https://github.com/Readarr/Readarr/pull/3724)
-   Type: Dictionaire
-   Is Mandatory: No (Defaults to no searches being triggered automatically)
-   "SONARR"/"RADARR" turns on the automatic searches for the respective instances
-   "MISSING"/"CUTOFF_UNMET" turns on the automatic search for those wanted items (defaults to True)
-   "MAX_CONCURRENT_SCANS" specifies the maximum number of items to be searched in each scan. This value dictates how many items are processed per search operation, which occurs according to the interval set by the REMOVE_TIMER.
-   Note: The limit is per wanted list. Thus if both Radarr & Sonarr are set up for automatic searches, both for missing and cutoff unmet items, the actual count may be four times the MAX_CONCURRENT_SCANS
-   "MIN_DAYS_BEFORE_RESCAN" steers the days that need to pass before an item is considered again for a scan
-   Note: RUN_PERIODIC_RESCANS will always search those items that haven been searched for longest

```
     RUN_PERIODIC_RESCANS: '
        {
          "SONARR": {"MISSING": true, "CUTOFF_UNMET": true, "MAX_CONCURRENT_SCANS": 3, "MIN_DAYS_BEFORE_RESCAN": 7},
          "RADARR": {"MISSING": true, "CUTOFF_UNMET": true, "MAX_CONCURRENT_SCANS": 3, "MIN_DAYS_BEFORE_RESCAN": 7}
        }'
```

There are different yaml notations, any some users suggested the below alternative notation.
If it you face issues, please first check the closed issues before opening a new one (e.g., https://github.com/ManiMatter/decluttarr/issues/173)

```
- RUN_PERIODIC_RESCANS=[
{
"SONARR":[{"MISSING":true, "CUTOFF_UNMET":true, "MAX_CONCURRENT_SCANS":3, "MIN_DAYS_BEFORE_RESCAN":7}],
"RADARR":[{"MISSING":true, "CUTOFF_UNMET":true, "MAX_CONCURRENT_SCANS":3, "MIN_DAYS_BEFORE_RESCAN":7}]
}
```

**MIN_DOWNLOAD_SPEED**

-   Sets the minimum download speed for active downloads
-   If the increase in the downloaded file size of a download is less than this value between two consecutive checks, the download is considered slow and is removed if happening more ofthen than the permitted strikes
-   Type: Integer
-   Unit: KBytes per second
-   Is Mandatory: No (Defaults to 100, but is only enforced when "REMOVE_SLOW" is true)

**PERMITTED_STRIKES**

-   Defines how many times a download has to be caught as stalled, slow or stuck downloading metadata before it is removed
-   Type: Integer
-   Unit: Number of scans
-   Is Mandatory: No (Defaults to 3)

**NO_STALLED_REMOVAL_QBIT_TAG**

-   Downloads in qBittorrent tagged with this tag will not be removed
-   Feature is not available when not using qBittorrent as torrent manager
-   Applies to all types of removal (ie. nothing will be removed automatically by decluttarr)
-   Note: You may want to try "force recheck" to get your stuck torrents manually back up and running
-   Tag is automatically created in qBittorrent (required qBittorrent is reachable on `QBITTORRENT_URL`)
-   Important: Also protects unmonitored downloads from being removed (relevant for multi-season packs)
-   Type: String
-   Is Mandatory: No (Defaults to `Don't Kill`)

**IGNORE_PRIVATE_TRACKERS**

-   Private torrents in qBittorrent will not be removed from the queue if this is set to true
-   Only works if qBittorrent is used (does not work with transmission etc.)
-   Applies to all types of removal (ie. nothing will be removed automatically by decluttarr); only exception to this is REMOVE_NO_FORMAT_UPGRADE, where for private trackers the queue item is removed (but the torrent files are kept)
-   Note: You may want to try "force recheck" to get your stuck torrents manually back up and running
-   Type: Boolean
-   Permissible Values: True, False
-   Is Mandatory: No (Defaults to True)

**FAILED_IMPORT_MESSAGE_PATTERNS**

-   Works in together with REMOVE_FAILED_IMPORTS (only relevant if this setting is true)
-   Defines the patterns based on which the tool decides if a completed download that has warnings on import should be considered failed
-   Queue items are considered failed if any of the specified patterns is contained in one of the messages of the queue item
-   Note: If left empty (or not specified), any such pending import with warning is considered failed
-   Type: List
-   Recommended values: ["Not a Custom Format upgrade for existing", "Not an upgrade for existing"]
-   Is Mandatory: No (Defaults to [], which means all messages are failures)

**IGNORED_DOWNLOAD_CLIENTS**

- If specified, downloads of the listed download clients are not removed / skipped entirely
- Is useful if multiple download clients are used and some of them are known to have slow downloads that recover (and thus should not be subject to slowness check), while other download clients should be monitored
- Type: List
- Is Mandatory: No (Defaults to [], which means no download clients are skipped)

---

### **Radarr section**

Defines radarr instance on which download queue should be decluttered

**RADARR_URL**

-   URL under which the instance can be reached
-   If not defined, this instance will not be monitored

**RADARR_KEY**

-   Your API key for radarr

---

### **Sonarr section**

Defines sonarr instance on which download queue should be decluttered

**SONARR_URL**

-   URL under which the instance can be reached
-   If not defined, this instance will not be monitored

**SONARR_KEY**

-   Your API key for sonarr

---

### **Lidarr section**

Defines lidarr instance on which download queue should be decluttered

**LIDARR_URL**

-   URL under which the instance can be reached
-   If not defined, this instance will not be monitored

**LIDARR_KEY**

-   Your API key for lidarr

---

### **Readarr section**

Defines readarr instance on which download queue should be decluttered

**READARR_URL**

-   URL under which the instance can be reached
-   If not defined, this instance will not be monitored

**READARR_KEY**

-   Your API key for readarr

---

### **Whisparr section**

Defines whisparr instance on which download queue should be decluttered

**WHISPARR_URL**

-   URL under which the instance can be reached
-   If not defined, this instance will not be monitored

**WHISPARR_KEY**

-   Your API key for whisparr

---

### **qBittorrent section**

Defines settings to connect with qBittorrent
If a different torrent manager is used, comment out this section (see above the limitations in functionality that arises from this)

**QBITTORRENT_URL**

-   URL under which the instance can be reached
-   If not defined, the NO_STALLED_REMOVAL_QBIT_TAG takes no effect

**QBITTORRENT_USERNAME**

-   Username used to log in to qBittorrent
-   Optional; not needed if authentication bypassing on qBittorrent is enabled (for instance for local connections)

**QBITTORRENT_PASSWORD**

-   Password used to log in to qBittorrent
-   Optional; not needed if authentication bypassing on qBittorrent is enabled (for instance for local connections)


## Disclaimer

This script comes free of any warranty, and you are using it at your own risk
