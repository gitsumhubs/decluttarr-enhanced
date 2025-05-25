import warnings

from src.utils.log_setup import logger


def show_welcome(settings):
    messages = ["🎉🎉🎉 Decluttarr - Application Started! 🎉🎉🎉",
                "-" * 80,
                "⭐️ Like this app?",
                "Thanks for giving it a ⭐️ on GitHub!",
                "https://github.com/ManiMatter/decluttarr/"]

    # Show welcome message

    # Show info level tip
    if settings.general.log_level == "INFO":
        messages.append("")
        messages.append("💡 Tip: More logs?")
        messages.append("If you want to know more about what's going on, switch log level to 'VERBOSE'")

    # Show bug report tip
    messages.append("")
    messages.append("🐛 Found a bug?")
    messages.append("Before reporting bugs on GitHub, please:")
    messages.append("1) Check the readme on github")
    messages.append("2) Check open and closed issues on github")
    messages.append("3) Switch your logs to 'DEBUG' level")
    messages.append("4) Turn off any features other than the one(s) causing it")
    messages.append("5) Provide the full logs via pastebin on your GitHub issue")
    messages.append("Once submitted, thanks for being responsive and helping debug / re-test")

    # Show test mode tip
    if settings.general.test_run:
        messages.append("")
        messages.append("=================== IMPORTANT ====================")
        messages.append("     ⚠️ ⚠️ ⚠️  TEST MODE IS ACTIVE  ⚠️ ⚠️ ⚠️")
        messages.append("Decluttarr won't actually do anything for you...")
        messages.append("You can change this via the setting 'test_run'")
        messages.append("==================================================")

    messages.append("")
    # Log all messages at once
    logger.info("\n".join(messages))


async def launch_steps(settings):
    # Hide SSL Verification Warnings
    if not settings.general.ssl_verification:
        warnings.filterwarnings("ignore", message="Unverified HTTPS request")

    logger.verbose(settings)
    show_welcome(settings)

    logger.info("*** Checking Instances ***")
    # Check qbit, fetch initial cookie, and set tag (if needed)
    for qbit in settings.download_clients.qbittorrent:
        await qbit.setup()

    # Setup arrs (apply checks, and store information)
    settings.instances.check_any_arrs()
    for arr in settings.instances.arrs:
        await arr.setup()
