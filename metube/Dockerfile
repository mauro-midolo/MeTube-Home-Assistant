ARG BUILD_FROM=ghcr.io/alexta69/metube:2026.10.22
FROM ${BUILD_FROM}

COPY rootfs/run.py /run.py

# MeTube's own entrypoint is still used; run.py only turns the app options
# into the environment variables MeTube reads, then hands over to it.
ENTRYPOINT ["/usr/bin/tini", "-g", "--", "python3", "/run.py"]
