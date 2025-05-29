import sys
import time
import asyncio
import logging
import copy
import requests
from src.utils.log_setup import logger

def sanitize_kwargs(data):
    """Recursively redact sensitive values in kwargs for safe logging."""
    if isinstance(data, dict):
        redacted = {}
        for key, value in data.items():
            if key.lower() in {"username", "password", "x-api-key", "cookies"} and value:
                redacted[key] = "[**redacted**]"
            else:
                redacted[key] = sanitize_kwargs(value)
        return redacted
    elif isinstance(data, list):
        return [sanitize_kwargs(item) for item in data]
    return data

async def make_request(
    method: str, endpoint: str, settings, timeout: int = 15, log_error = True, **kwargs
) -> requests.Response:
    """
    A utility function to make HTTP requests (GET, POST, DELETE, PUT).
    """
    try:
        if logger.isEnabledFor(logging.DEBUG):
            sanitized_kwargs = sanitize_kwargs(copy.deepcopy(kwargs))
            logger.debug(
                f"common.py/make_request: Making {method.upper()} request to {endpoint} with kwargs={sanitized_kwargs}"
            )

        # Make the request using the method passed (get, post, etc.)
        response = await asyncio.to_thread(
            getattr(requests, method.lower()),
            endpoint,
            **kwargs,
            verify=settings.general.ssl_verification,
            timeout=timeout,
        )
        response.raise_for_status()
        return response
    except requests.exceptions.HTTPError as http_err:
        if log_error:
            logger.error(f"HTTP error occurred: {http_err}", exc_info=True)
        raise

    except Exception as err:
        if log_error:
            logger.error(f"Other error occurred: {err}", exc_info=True)
        raise


def wait_and_exit(seconds=30):
    logger.info(f"Decluttarr will wait for {seconds} seconds and then exit.")
    time.sleep(seconds)
    sys.exit()
