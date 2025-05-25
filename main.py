import asyncio
import signal
import sys
import types

from src.job_manager import JobManager
from src.settings.settings import Settings
from src.utils.log_setup import logger
from src.utils.startup import launch_steps

settings = Settings()
job_manager = JobManager(settings)


# # Main function
async def main():
    await launch_steps(settings)

    # Start Cleaning
    while True:
        logger.verbose("-" * 50)

        # Refresh qBit Cookies
        for qbit in settings.download_clients.qbittorrent:
            await qbit.refresh_cookie()

        # Run script for each instance
        for arr in settings.instances.arrs:
            await job_manager.run_jobs(arr)

        logger.verbose("")
        logger.verbose("Queue clean-up complete!")

        # Wait for the next run
        await asyncio.sleep(settings.general.timer * 60)


if __name__ == "__main__":
    def terminate(sigterm: signal.SIGTERM, frame: types.FrameType) -> None:  # noqa: ARG001
        """
        Terminate cleanly. Needed for respecting 'docker stop'.

        Args:
        ----
            sigterm (signal.Signal): The termination signal.
            frame: The execution frame.

        """
        logger.info("Termination signal received.")
        sys.exit(0)
    signal.signal(signal.SIGTERM, terminate)
    asyncio.run(main())
