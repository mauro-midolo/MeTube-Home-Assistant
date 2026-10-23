"""Small client for the MeTube HTTP API."""

from __future__ import annotations

from typing import Any

import aiohttp


class MeTubeError(Exception):
    """MeTube could not be reached or refused a request."""


class MeTubeClient:
    """Talks to one MeTube server."""

    def __init__(self, session: aiohttp.ClientSession, url: str) -> None:
        self._session = session
        self.url = url.rstrip("/") + "/"

    async def _request(self, method: str, path: str, json: Any = None) -> Any:
        try:
            async with self._session.request(
                method,
                self.url + path,
                json=json,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                if resp.status >= 400:
                    # MeTube puts the reason for a rejected request in the body.
                    detail = (await resp.text()).strip()[:300]
                    raise MeTubeError(f"{path}: HTTP {resp.status} {detail}".rstrip())
                return await resp.json(content_type=None)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise MeTubeError(f"{path}: {err}") from err

    async def version(self) -> dict[str, Any]:
        return await self._request("GET", "version")

    async def history(self) -> dict[str, list[dict[str, Any]]]:
        return await self._request("GET", "history")

    async def add(
        self,
        url: str,
        download_type: str,
        format_: str,
        quality: str,
        folder: str | None = None,
        playlist_item_limit: int | None = None,
    ) -> None:
        body: dict[str, Any] = {
            "url": url,
            "download_type": download_type,
            "format": format_,
            "quality": quality,
            "auto_start": True,
        }
        if folder:
            body["folder"] = folder
        if playlist_item_limit is not None:
            body["playlist_item_limit"] = playlist_item_limit
        result = await self._request("POST", "add", body)
        if result.get("status") != "ok":
            raise MeTubeError(result.get("msg") or "MeTube rejected the download")

    async def clear_done(self, ids: list[str]) -> None:
        await self._request("POST", "delete", {"ids": ids, "where": "done"})
