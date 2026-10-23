"""Translate /data/options.json into MeTube's environment, then start MeTube."""

import json
import os
import sys

OPTIONS_FILE = "/data/options.json"
ALLOWED_ROOTS = ("/media/", "/share/")


def check_dir(name, path):
    path = os.path.normpath(path)
    if not path.startswith(ALLOWED_ROOTS):
        sys.exit(f"[metube] '{name}' deve stare sotto /media o /share, non '{path}'")
    return path


with open(OPTIONS_FILE, encoding="utf-8") as f:
    options = json.load(f)

env = os.environ
audio_dir = check_dir("audio_dir", options["audio_dir"])
video_dir = check_dir("video_dir", options["video_dir"])

env["DOWNLOAD_DIR"] = video_dir
env["AUDIO_DOWNLOAD_DIR"] = audio_dir
# Queue and history live in the app's own folder, so they are part of HA backups.
env["STATE_DIR"] = "/data/state"
# Half-finished files stay out of the library (and out of backups) until
# they are complete.
env["TEMP_DIR"] = "/tmp/metube"
env["OUTPUT_TEMPLATE"] = options["output_template"]
env["OUTPUT_TEMPLATE_PLAYLIST"] = options["output_template_playlist"]
env["MAX_CONCURRENT_DOWNLOADS"] = str(options["max_concurrent_downloads"])
env["DELETE_FILE_ON_TRASHCAN"] = options.get("delete_files", "ask")
env["DEFAULT_THEME"] = options["theme"]
env["LOGLEVEL"] = options["log_level"].upper()
env["PORT"] = "8081"
# Ingress serves the UI under a per-install path; MeTube's UI uses relative
# URLs, so it works there as long as it runs at the root.
env.pop("URL_PREFIX", None)
# Files are written as root, the same user Music Assistant reads them as;
# leave the ownership of the existing media folders alone.
env["PUID"] = "0"
env["PGID"] = "0"
env["CHOWN_DIRS"] = "false"

if options.get("ytdl_options"):
    try:
        json.loads(options["ytdl_options"])
    except ValueError as err:
        sys.exit(f"[metube] 'ytdl_options' non è JSON valido: {err}")
    env["YTDL_OPTIONS"] = options["ytdl_options"]
if options.get("nightly_update_time"):
    env["YTDL_NIGHTLY_UPDATE_TIME"] = options["nightly_update_time"]

print(f"[metube] audio -> {audio_dir}, video -> {video_dir}", flush=True)
os.chdir("/app")
os.execv("/app/docker-entrypoint.sh", ["/app/docker-entrypoint.sh"])
