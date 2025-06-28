import asyncio
import signal
import types
import datetime
import sys

from src.job_manager import JobManager
from src.settings.settings import Settings
from src.utils.log_setup import logger
from src.utils.startup import launch_steps

settings = Settings()
job_manager = JobManager(settings)

def terminate(sigterm: signal.SIGTERM, frame: types.FrameType) -> None:  # noqa: ARG001, pylint: disable=unused-argument

    """Terminate cleanly. Needed for respecting 'docker stop'.

    Args:
    ----
        sigterm (signal.Signal): The termination signal.
        frame: The execution frame.

    """

    logger.info(f"Termination signal received at {datetime.datetime.now()}.")  # noqa: DTZ005
    sys.exit(0)

async def wait_next_run():
   # Calculate next run time dynamically (to display)
    next_run = datetime.datetime.now() + datetime.timedelta(minutes=settings.general.timer)
    formatted_next_run = next_run.strftime("%Y-%m-%d %H:%M")

    logger.verbose(f"*** Done - Next run at {formatted_next_run} ****")

    # Wait for the next run
    await asyncio.sleep(settings.general.timer * 60)

# Main function
async def main():
    await launch_steps(settings)

    # Start Cleaning
    while True:
        logger.info("-" * 50)

        # Refresh qBit Cookies
        for qbit in settings.download_clients.qbittorrent:
            await qbit.refresh_cookie()

        # Run script for each instance
        for arr in settings.instances:
            await job_manager.run_jobs(arr)
            logger.verbose("")

        # Wait for the next run
        await wait_next_run()
    return


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, terminate)
    asyncio.run(main())
