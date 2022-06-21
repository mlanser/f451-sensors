"""Command-line interface."""
import argparse
import logging
import os
import re
import sys
from configparser import ConfigParser
from configparser import ExtendedInterpolation
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List

import konsole
from faker import Faker
from rich import print as rprint
from rich import traceback
from rich.rule import Rule

import f451_sensors.constants as const
import f451_sensors.smart_sensor as smart_sensor
from . import __app_name__
from . import __version__

# =========================================================
#          G L O B A L    V A R S   &   I N I T S
# =========================================================
traceback.install()  # Ensure 'pretty' tracebacks
faker = Faker()  # Initialize 'Faker'

_APP_NAME_: str = "f451 Sensors Module"
_APP_NORMALIZED_: str = re.sub(r"[^A-Z0-9]", "_", str(__app_name__).upper())
_APP_DIR_: Path = Path(__file__).parent

# OS ENVIRON variable names
_APP_ENV_CONFIG_: str = f"{_APP_NORMALIZED_}_CONFIG"
_APP_ENV_SECRETS_: str = f"{_APP_NORMALIZED_}_SECRETS"

# Default CONFIG, SECRETS, and LOG filenames
# NOTE: these default filenames are used to search for files in degfault
#       locations if no files are inicated in OS ENVIRON vars or supplied
#       in CLI args.
# NOTE: we allow user to store secrets (i.e. API keys and other environ
#       secrets that should not go github), separately from 'safe' config
#       values (i.e. info that is safe to share on github). But both types
#       can also be stored in the same file.
_APP_LOG_: str = "f451-sensors.log"
_APP_CONFIG_: str = "f451-sensors.config.ini"
_APP_SECRETS_: str = "f451-sensors.secrets.ini"


# =========================================================
#              H E L P E R   F U N C T I O N S
# =========================================================


def init_cli_parser() -> argparse.ArgumentParser:
    """Initialize CLI (ArgParse) parser.

    Initialize the ArgParse parser with the CLI 'arguments' and
    return a new parser instance.

    Returns:
        ArgParse parser instance
    """
    parser = argparse.ArgumentParser(
        prog=__app_name__,
        description=f"Collect sensor data via 'f451 Sensors' [v{__version__}] module",
        epilog="NOTE: Only call a module if the corresponding service is installed",
    )

    parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        help="Display module version number and exit.",
    )
    parser.add_argument("-d", "--debug", action="store_true", help="Run in debug mode")
    parser.add_argument(
        "--sensor",
        action="store",
        default=const.SENSOR_ALL,
        type=str,
        help="Sensor(s) to use",
    )
    parser.add_argument(
        "--secrets",
        action="store",
        type=str,
        help="Path to primary config file",
    )
    parser.add_argument(
        "--config",
        action="store",
        type=str,
        help="Path to secondary config file",
    )
    parser.add_argument(
        "--log",
        action="store",
        type=str,
        help="Path to log file",
    )

    return parser


def init_ini_parser(fNames: Any) -> ConfigParser:
    """Initialize ConfigParser.

    Args:
        fNames:
            list with one or more paths to config files

    Returns:
        ConfigParser instance

    Raises:
        ValueError: Config file does not exist
    """
    parser = ConfigParser(interpolation=ExtendedInterpolation())

    tmpList = fNames if isinstance(fNames, list) else [fNames]
    for fn in tmpList:
        tmpName = Path(fn).expanduser()
        if not tmpName.exists():
            raise ValueError(f"Config file '{tmpName}' does not exist.")

        parser.read(tmpName)

    return parser


def get_valid_location(inFName: str) -> str:
    """Get valid location for a given filename.

    We use this to look for a given file (mainly config
    files) in a few default locations.

    Args:
        inFName:
            filename (string) to look for

    Returns:
        filename as string
    """
    cleanFName = inFName.strip("/")
    defaultLocations = [
        f"{Path.cwd()}/{cleanFName}",
        f"{Path(__file__).parent.absolute()}/{cleanFName}",
        f"{Path.home()}/{cleanFName}",
        f"/etc/{__app_name__}/{cleanFName}",
    ]

    outFName = ""
    for item in defaultLocations:
        if Path(item).exists():
            outFName = str(item)
            break

    return outFName


# =========================================================
#      M A I N   F U N C T I O N    /   A C T I O N S
# =========================================================
def main(inArgs: Any = None) -> None:  # noqa: C901
    """Core function to run through demo.    # noqa: D417,D415

    This function will run through one or more 'demo' scenarios
    depending on the arguments passed to CLI.

    Note:
        - Application will exit with error level 1 if invalid communications
          channels are included

        - Application will exit with error level 0 if either no arguments are
          entered via CLI, or if arguments '-V' or '--version' are used. No message
          will be sent in that case.

    Args:
        inArgs:
            CLI arguments used to start application
    """
    cli = init_cli_parser()

    # Show 'help' and exit if no args
    cliArgs, unknown = cli.parse_known_args(inArgs)
    if (not inArgs and len(sys.argv) == 1) or (len(sys.argv) == 2 and cliArgs.debug):
        cli.print_help(sys.stdout)
        sys.exit(0)

    if cliArgs.version:
        rprint(f"{_APP_NAME_} ({__app_name__}) v{__version__}")
        sys.exit(0)

    # Initialize loggers
    logger = logging.getLogger()
    logging.basicConfig(
        filename=cliArgs.log or f"{_APP_DIR_}/{_APP_LOG_}",
        # encoding="utf-8",     # Not available in Python v3.8
        level=logging.INFO,
    )
    logger.setLevel(logging.DEBUG if cliArgs.debug else logging.INFO)

    konsole.config(level=konsole.DEBUG if cliArgs.debug else konsole.ERROR)

    # # Initialize main Communications Module with 'config' and 'secrets' data
    # comms = Comms(
    #     init_ini_parser(
    #         [
    #             (
    #                 cliArgs.config
    #                 or (
    #                     os.environ.get(_APP_ENV_CONFIG_)
    #                     or get_valid_location(_APP_CONFIG_)
    #                 )
    #             ),
    #             (
    #                 cliArgs.secrets
    #                 or (
    #                     os.environ.get(_APP_ENV_SECRETS_)
    #                     or get_valid_location(_APP_SECRETS_)
    #                 )
    #             ),
    #         ]
    #     )
    # )

    # # Exit if invalid channel
    # availableChannels = (
    #     comms.valid_channels
    #     if cliArgs.channel == const.CHANNEL_ALL
    #     else comms.process_channel_list(cliArgs.channel.split(const.DELIM_STD))
    # )

    # if not comms.is_valid_channel(availableChannels):
    #     rprint(f"ERROR: '{cliArgs.channel}' is not a valid communications channel!")
    #     sys.exit(1)

    # -----------------------
    # Run communication demos
    # -----------------------
    rprint(Rule())

    rprint("Hello world!")

    # -----------------------
    # rprint("[bold black on white] - Available Channels - [/bold black on white]")
    # if comms.channels:
    #     for key, val in comms.channels.items():  # type: ignore[union-attr]
    #         rprint(f"{key:.<20.20}: {'ON' if val else 'OFF'}")
    # else:
    #     rprint("There are no channels enabled!")
    rprint(Rule())

    # # -----------------------
    # # - 1 - Broadcast message based on args
    # rprint(
    #     f"[bold black on white] - Broadcast to {availableChannels} - [/bold black on white]"
    # )
    # try:
    #     comms.send_message(cliArgs.msg, **{const.KWD_CHANNELS: availableChannels})

    # except (MissingAttributeError, CommunicationsError) as e:
    #     rprint(e)

    # # -----------------------
    # # - 2 - Send Email via Mailgun
    # if const.CHANNEL_MAILGUN in availableChannels:
    #     send_test_msg_via_mailgun(comms, cliArgs.msg)

    # # -----------------------
    # # - 3 - Send messages via Slack
    # if const.CHANNEL_SLACK in availableChannels:
    #     send_test_msg_via_slack(comms, cliArgs.msg)

    # # -----------------------
    # # - 4 - Send SMS via Twilio
    # if const.CHANNEL_TWILIO in availableChannels:
    #     send_test_msg_via_twilio(comms, cliArgs.msg)

    # # -----------------------
    # # - 5 - Send tweets and DMs via Twitter
    # if const.CHANNEL_TWITTER in availableChannels:
    #     send_test_msg_via_twitter(comms, cliArgs.msg)

    # -----------------------
    rprint(Rule())


# =========================================================
#            G L O B A L   C A T C H - A L L
# =========================================================
if __name__ == "__main__":
    main()  # pragma: no cover
