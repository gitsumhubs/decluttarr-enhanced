from unittest.mock import AsyncMock, MagicMock
import pytest

from src.jobs.removal_handler import RemovalHandler


@pytest.mark.parametrize(
    "qbittorrent_configured, is_private, client_impl, protocol, expected",
    [
        (True, True, "QBittorrent", "torrent", "private_handling"),
        (True, False, "QBittorrent", "torrent", "public_handling"),
        (False, True, "QBittorrent", "torrent", "remove"),
        (False, False, "QBittorrent", "torrent", "remove"),
        (True, False, "Transmission", "torrent", "remove"),  # unsupported client
        (True, False, "MyUseNetClient", "usenet", "remove"),  # unsupported protocol
    ],
)
@pytest.mark.asyncio
async def test_get_handling_method(
    qbittorrent_configured,
    is_private,
    client_impl,
    protocol,
    expected,
):
    # Mock arr
    arr = AsyncMock()
    arr.tracker.private = ["A"] if is_private else []
    arr.get_download_client_implementation.return_value = client_impl

    # Mock settings
    settings = MagicMock()
    settings.download_clients.qbittorrent = ["dummy"] if qbittorrent_configured else []
    settings.general.private_tracker_handling = "private_handling"
    settings.general.public_tracker_handling = "public_handling"

    handler = RemovalHandler(arr=arr, settings=settings, job_name="test")

    affected_download = {
        "downloadClient": "qBittorrent",
        "protocol": protocol,
    }

    result = await handler._get_handling_method( # pylint: disable=W0212
        "A", affected_download
    )
    assert result == expected
