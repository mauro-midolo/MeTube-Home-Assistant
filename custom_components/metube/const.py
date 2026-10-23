"""Constants for the MeTube integration."""

from datetime import timedelta

DOMAIN = "metube"

# Suggested address when the MeTube app is not found among the installed apps:
# the hostname a local copy of the app gets on Home Assistant's internal network.
DEFAULT_URL = "http://local-metube:8081"

CONF_DOWNLOAD_TYPE = "download_type"
CONF_FORMAT = "format"
CONF_QUALITY = "quality"
CONF_FOLDER = "folder"

DOWNLOAD_TYPES = ["audio", "video"]
AUDIO_FORMATS = ["mp3", "m4a", "opus", "flac", "wav", "auto"]
VIDEO_FORMATS = ["any", "mp4", "ios"]
QUALITIES = [
    "best",
    "320",
    "192",
    "128",
    "2160",
    "1440",
    "1080",
    "720",
    "480",
    "360",
    "240",
    "worst",
]

DEFAULT_OPTIONS = {
    CONF_DOWNLOAD_TYPE: "audio",
    CONF_FORMAT: "mp3",
    CONF_QUALITY: "best",
    CONF_FOLDER: "",
}

SCAN_INTERVAL = timedelta(seconds=10)
