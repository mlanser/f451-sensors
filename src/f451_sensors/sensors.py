"""f451 Sensors module.

This module acts as a common interface to several physical and virtual sensors, and 
its main purpose is to make it easy to collect data from several sensors at the same.

An application can define which sensors to activate, at what intervals to collect data, 
and for how long.

Note:
    * Store secrets (e.g. API keys, etc.) in a separate configuration file.
    * Store defaults (e.g. default sensors, etc.) in a separate configuration file.
    * Use ``.ini`` files that can be parsed by the Python ConfigParser (see example files)
"""
import logging
import pprint
from configparser import ConfigParser
from typing import Any
from typing import Dict
from typing import List
from typing import Union

import f451_sensors.constants as const
import f451_sensors.providers.sensor as sensor
import f451_sensors.utils as utils
from f451_sensors.exceptions import InvalidSensorError
from f451_sensors.providers.chameleon import Chameleon

# =========================================================
#          G L O B A L S   A N D   H E L P E R S
# =========================================================
SRV_PROVIDER: str = "Main"
SRV_CONFIG_SCTN: str = "f451_main"

log = logging.getLogger()
pp = pprint.PrettyPrinter(indent=4)

typeDefProvider = Union[Chameleon, None]
typeDefStringLists = Union[str, List[str], None]
typeDefSensorInfo = Union[
    ConfigParser, Dict[str, str], Dict[str, Any], List[str], None
]
typeDefSendMsgResponse = Union[List[sensor.Response], Any]


# =========================================================
#        M A I N   C L A S S   D E F I N I T I O N
# =========================================================
class Sensors(sensor.Sensor):
    """Main class for f451 Sensor module.

    Use this main class as default interface to collect data from
    one or more sensors and then send/publish to some data store.

    All available sensors and associated attributes are defined
    during initialization of the class.

    Attributes:
        config:
            set of attributes for 'secrets' such as API keys, general
            attributes, and default settings
    """

    def __init__(self, config: Any = None) -> None:
        super().__init__(const.SNSR_TYPE_MAIN, SRV_PROVIDER, SRV_CONFIG_SCTN)

        settings = utils.process_config(config, False)

        self.default_sensors = settings
        self.sensor_map = settings
        self.sensors = settings

    @property
    def sensors(self) -> typeDefSensorInfo:
        """Return 'sensors' property."""
        return self._sensors

    @sensors.setter
    def sensors(self, settings: ConfigParser) -> None:
        """Set 'sensors' property."""
        self._sensors = {
            const.SENSOR_TEMP: self._init_temperature(settings),
            const.SENSOR_HUMID: self._init_humidity(settings),
            const.SENSOR_WIND: self._init_wind(settings),
            const.SENSOR_RAIN: self._init_rain(settings),
            const.SENSOR_SPEED: self._init_speed(settings),
        }

    @property
    def Temperature(self) -> typeDefProvider:
        """Return 'Temperature' sensor client."""
        return self._sensors[const.SENSOR_TEMP]

    @property
    def Humidity(self) -> typeDefProvider:
        """Return 'Humidity' sensor client."""
        return self._sensors[const.SENSOR_HUMID]

    @property
    def Wind(self) -> typeDefProvider:
        """Return 'Wind' sensor client."""
        return self._sensors[const.SENSOR_WIND]

    @property
    def Rain(self) -> typeDefProvider:
        """Return 'Rain' sensor client."""
        return self._sensors[const.SENSOR_RAIN]

    @property
    def Speed(self) -> typeDefProvider:
        """Return 'Speed' sensor client."""
        return self._sensors[const.SENSOR_SPEED]

    @property
    def valid_sensors(self) -> List[str]:
        """Return 'senderName' property."""
        return list(self._sensors.keys())

    @property
    def sensor_map(self) -> typeDefSensorInfo:
        """Return 'sensor_map' property."""
        return self._sensor_map

    @sensor_map.setter
    def sensor_map(self, settings: ConfigParser) -> None:
        """Set 'sensor_map' property."""
        self._sensor_map = utils.process_key_value_map(
            settings.get(const.SENSOR_MAIN, const.KWD_SENSOR_MAP, fallback="")
        )

    def is_valid_sensor(self, inChannels: typeDefStringLists) -> bool:
        """Check if communications sensor is valid."""
        tmpList = self._normalize_sensor_list(inChannels)
        return (
            all(self._verify_sensor(ch, True) for ch in tmpList) if tmpList else False
        )

    def is_enabled_sensor(self, inChannels: typeDefStringLists) -> bool:
        """Check if communications sensor is enabled."""
        tmpList = self._normalize_sensor_list(inChannels)
        return (
            all(ch in self._sensors and self._sensors[ch] for ch in tmpList)
            if tmpList
            else False
        )

    @property
    def default_sensors(self) -> typeDefSensorInfo:
        """Return 'default_sensors' property."""
        return self._default_sensors

    @default_sensors.setter
    def default_sensors(self, settings: ConfigParser) -> None:
        """Set 'default_sensors' property."""
        self._default_sensors = str(
            settings.get(const.SENSOR_MAIN, const.KWD_SENSORS, fallback="")
        ).split(const.DELIM_STD)

    def _verify_sensor(self, chName: str, force: bool) -> bool:
        return (
            (chName != "" and (chName in self._sensors or chName in self._sensor_map))
            if force
            else (chName != "")
        )

    @staticmethod
    def _normalize_sensor_list(inChannels: typeDefStringLists) -> List[str]:
        if inChannels:
            if isinstance(inChannels, str):
                return inChannels.split(const.DELIM_STD)
            elif all(isinstance(ch, str) for ch in inChannels):
                return inChannels

        return []

    @staticmethod
    def _init_temperature(settings: ConfigParser) -> typeDefProvider:
        """Initialize Temperature sensor client."""
        if not settings.has_section(const.SENSOR_TEMP):
            return None

        # fromName = settings.get(
        #     const.SENSOR_MAIN,
        #     const.KWD_FROM,
        #     fallback=settings.get(
        #         const.SENSOR_MAILGUN, const.KWD_FROM_NAME, fallback=""
        #     ),
        # )
        #
        # defaultTo = settings.get(
        #     const.SENSOR_MAIN,
        #     const.KWD_TO,
        #     fallback=settings.get(
        #         const.SENSOR_MAILGUN, const.KWD_TO_EMAIL, fallback=""
        #     ),
        # )
        #
        # return Mailgun(
        #     apiKey=settings.get(const.SENSOR_MAILGUN, const.KWD_PRIV_KEY, fallback=""),
        #     fromDomain=settings.get(
        #         const.SENSOR_MAILGUN, const.KWD_FROM_DOMAIN, fallback=""
        #     ),
        #     from_name=fromName,
        #     to_email=defaultTo,
        #     subject=settings.get(const.SENSOR_MAILGUN, const.KWD_SUBJECT, fallback=""),
        #     tags=settings.get(const.SENSOR_MAILGUN, const.KWD_TAGS, fallback=""),
        #     tracking=settings.get(
        #         const.SENSOR_MAILGUN, const.KWD_TRACKING, fallback=""
        #     ),
        #     testmode=settings.get(
        #         const.SENSOR_MAILGUN, const.KWD_TESTMODE, fallback=""
        #     ),
        # )
        return None

    @staticmethod
    def _init_humidity(settings: ConfigParser) -> typeDefProvider:
        """Initialize Humidity sensor client."""
        if not settings.has_section(const.SENSOR_HUMID):
            return None

        # fromSlack = settings.get(
        #     const.SENSOR_MAIN,
        #     const.KWD_FROM,
        #     fallback=settings.get(
        #         const.SENSOR_SLACK, const.KWD_FROM_SLACK, fallback=""
        #     ),
        # )
        #
        # defaultChannel = settings.get(
        #     const.SENSOR_SLACK, const.KWD_TO_SENSOR, fallback=""
        # )
        #
        # return Slack(
        #     authToken=settings.get(
        #         const.SENSOR_SLACK, const.KWD_AUTH_TOKEN, fallback=""
        #     ),
        #     signingSecret=settings.get(
        #         const.SENSOR_SLACK, const.KWD_SIGN_SECRET, fallback=""
        #     ),
        #     appToken=settings.get(
        #         const.SENSOR_SLACK, const.KWD_APP_TOKEN, fallback=""
        #     ),
        #     to_sensor=defaultChannel,
        #     from_slack=fromSlack,
        #     icon_emoji=settings.get(
        #         const.SENSOR_SLACK, const.KWD_ICON_EMOJI, fallback=""
        #     ),
        # )
        return None

    @staticmethod
    def _init_wind(settings: ConfigParser) -> typeDefProvider:
        """Initialize Wind sensor client."""
        if not settings.has_section(const.SENSOR_WIND):
            return None

        # fromPhone = settings.get(
        #     const.SENSOR_MAIN,
        #     const.KWD_FROM,
        #     fallback=settings.get(
        #         const.SENSOR_TWILIO, const.KWD_FROM_PHONE, fallback=""
        #     ),
        # )
        #
        # defaultTo = settings.get(
        #     const.SENSOR_MAIN,
        #     const.KWD_TO,
        #     fallback=settings.get(
        #         const.SENSOR_TWILIO, const.KWD_TO_PHONE, fallback=""
        #     ),
        # )
        #
        # return Twilio(
        #     acctSID=settings.get(const.SENSOR_TWILIO, const.KWD_ACCT_SID, fallback=""),
        #     authToken=settings.get(
        #         const.SENSOR_TWILIO, const.KWD_AUTH_TOKEN, fallback=""
        #     ),
        #     from_phone=fromPhone,
        #     to_phone=defaultTo,
        # )
        return None

    @staticmethod
    def _init_rain(settings: ConfigParser) -> typeDefProvider:
        """Initialize Rain sensor client."""
        if not settings.has_section(const.SENSOR_RAIN):
            return None

        # defaultTo = settings.get(
        #     const.SENSOR_MAIN,
        #     const.KWD_TO,
        #     fallback=settings.get(
        #         const.SENSOR_TWITTER, const.KWD_TO_TWITTER, fallback=""
        #     ),
        # )
        #
        # return Twitter(
        #     usrKey=settings.get(const.SENSOR_TWITTER, const.KWD_USER_KEY, fallback=""),
        #     usrSecret=settings.get(
        #         const.SENSOR_TWITTER, const.KWD_USER_SECRET, fallback=""
        #     ),
        #     authToken=settings.get(
        #         const.SENSOR_TWITTER, const.KWD_AUTH_TOKEN, fallback=""
        #     ),
        #     authSecret=settings.get(
        #         const.SENSOR_TWITTER, const.KWD_AUTH_SECRET, fallback=""
        #     ),
        #     to_twitter=defaultTo,
        #     tags=settings.get(const.SENSOR_TWITTER, const.KWD_TAGS, fallback=""),
        # )
        return None

    @staticmethod
    def _init_speed(settings: ConfigParser) -> typeDefProvider:
        """Initialize Speed sensor client."""
        if not settings.has_section(const.SENSOR_SPEED):
            return None

        # defaultTo = settings.get(
        #     const.SENSOR_MAIN,
        #     const.KWD_TO,
        #     fallback=settings.get(
        #         const.SENSOR_TWITTER, const.KWD_TO_TWITTER, fallback=""
        #     ),
        # )
        #
        # return Twitter(
        #     usrKey=settings.get(const.SENSOR_TWITTER, const.KWD_USER_KEY, fallback=""),
        #     usrSecret=settings.get(
        #         const.SENSOR_TWITTER, const.KWD_USER_SECRET, fallback=""
        #     ),
        #     authToken=settings.get(
        #         const.SENSOR_TWITTER, const.KWD_AUTH_TOKEN, fallback=""
        #     ),
        #     authSecret=settings.get(
        #         const.SENSOR_TWITTER, const.KWD_AUTH_SECRET, fallback=""
        #     ),
        #     to_twitter=defaultTo,
        #     tags=settings.get(const.SENSOR_TWITTER, const.KWD_TAGS, fallback=""),
        # )
        return None

    def process_sensor_list(
        self, inList: typeDefStringLists, strict: bool = False
    ) -> List[str]:
        """Process list of sensor names and convert to list of strings.

        The purpose of this method is to process a list with one or
        more sensor names and placing them into a list.

        Args:
            inList:
                Single string or list with one or more strings
            strict:
                If 'True' then include only valid and enabled sensor names

        Returns:
            String with zero or more sensor names
        """
        tmpList = (
            inList
            if isinstance(inList, list)
            else utils.convert_attrib_str_to_list(inList)
        )

        return [
            ch
            for ch in [
                self._sensor_map[item] if item in self._sensor_map else item
                for item in [
                    tmp.strip()
                    for tmp in tmpList
                    if self._verify_sensor(tmp.strip(), strict)
                ]
            ]
            if self.is_enabled_sensor(ch)
        ]

    def collect_data(self, **kwargs: Any) -> Dict[str, Any]:
        print("COLLECT DATA called")
        return {'foo': "bar"}

    def publish_data(self, inDelay: int = 1, iterMax: int = 0, **kwargs: Any) -> int:
        print("PUBLISH DATA called")
        return 1

    # def send_message(self, msg: str, **kwargs: Any) -> typeDefSendMsgResponse:
    #     """Send message to one or more sensors.
    #
    #     This method sends a given message to one or more sensors at
    #     the same time. The 'sensors' keyword argument defines which
    #     communication sensors to use.
    #
    #     The keyword arguments can also include additional message data
    #     such as HTML for emails and Slack blocks.
    #
    #     Args:
    #         msg:
    #             Simple/plain text version of message to be sent
    #         kwargs:
    #             Additional optional arguments
    #
    #     Returns:
    #         List of 'response' records. We always return a list even though we
    #         may only have a single item. This allows us to be consistent across
    #         all 'send_message()' functions.
    #
    #     Raises:
    #         InvalidProviderError: Channel/service provider is not valid/active
    #     """
    #     chList = kwargs.get(const.KWD_SENSORS, self._default_sensors)
    #     sensors = self.process_sensor_list(inList=chList, strict=True)
    #
    #     if not sensors:
    #         log.error(f"Invalid communication sensor(s): {chList}")
    #         raise InvalidProviderError("Invalid communication sensor(s)).")
    #
    #     return [
    #         self._sensors[ch].send_message(msg, **kwargs)  # type: ignore[union-attr]
    #         for ch in sensors
    #         if self._sensors[ch]
    #     ]

    # def send_message_via_mailgun(
    #     self, msg: str, **kwargs: Any
    # ) -> typeDefSendMsgResponse:
    #     """Send email via Mailgun.
    #
    #     This method sends a given message via email using the Mailgun service
    #     provider. The keyword arguments can also include additional message
    #     data such as an HTML version of the message.
    #
    #     Args:
    #         msg:
    #             Simple/plain text version of message to be sent
    #         kwargs:
    #             Additional optional arguments
    #
    #     Returns:
    #         List of 'response' records from email Mailgun service. We always return a list
    #         even though we may only have a single item. This allows us to be consistent
    #         across all 'send_message()' functions.
    #
    #     Raises:
    #         InvalidProviderError: Mailgun service is not valid/active
    #     """
    #     if self._sensors[const.SENSOR_MAILGUN]:
    #         return self._sensors[const.SENSOR_MAILGUN].send_message(msg, **kwargs)  # type: ignore[union-attr]  # noqa: B950
    #
    #     log.error(f"'{const.SENSOR_MAILGUN}' is not a valid communication sensor")
    #     raise InvalidProviderError(
    #         f"'{const.SENSOR_MAILGUN}' is not a valid communication sensor."
    #     )

    # def send_message_via_slack(self, msg: Any, **kwargs: Any) -> typeDefSendMsgResponse:
    #     """Send message via Slack.
    #
    #     This method sends a given message via Slack. The 'kwargs' arguments can
    #     also include additional message data such Slack blocks.
    #
    #     Args:
    #         msg:
    #             simple/plain text version of message to be sent. The 'msg' argument
    #             can also be a 'list' of Slack blocks.
    #         kwargs:
    #             Additional optional arguments
    #
    #     Returns:
    #         List of 'response' records from Slack. We always return a list
    #         even though we may only have a single item. This allows us to be consistent
    #         across all 'send_message()' functions.
    #
    #     Raises:
    #         InvalidProviderError: Slack sensor is not valid/active
    #     """
    #     if self._sensors[const.SENSOR_SLACK]:
    #         if isinstance(msg, list):
    #             return self._sensors[const.SENSOR_SLACK].send_message_with_blocks(  # type: ignore[union-attr]  # noqa: B950
    #                 msg, **kwargs
    #             )
    #         else:
    #             return self._sensors[const.SENSOR_SLACK].send_message(msg, **kwargs)  # type: ignore[union-attr]  # noqa: B950
    #
    #     log.error(
    #         f"ERROR: '{const.SENSOR_SLACK}' is not a valid communication sensor"
    #     )
    #     raise InvalidProviderError(
    #         f"'{const.SENSOR_SLACK}' is not a valid communication sensor."
    #     )

    # def send_message_via_twilio(
    #     self, msg: str, **kwargs: Any
    # ) -> typeDefSendMsgResponse:
    #     """Send SMS via Twilio.
    #
    #     This method sends a given message via SMS (using Twilio) to one or
    #     more recipients. The phone numbers of the recipients must be specified
    #     in the 'to_phone' keyword argument.
    #
    #     Args:
    #         msg:
    #             Simple/plain text version of message to be sent
    #         kwargs:
    #             Additional optional arguments
    #
    #     Returns:
    #         List of 'response' records from Twilio SMS service. We always return a list
    #         even though we may only have a single item. This allows us to be consistent
    #         across all 'send_message()' functions.
    #
    #     Raises:
    #         InvalidProviderError: Twilio service is not valid/active
    #     """
    #     if self._sensors[const.SENSOR_TWILIO]:
    #         return self._sensors[const.SENSOR_TWILIO].send_message(msg, **kwargs)  # type: ignore[union-attr]  # noqa: B950
    #
    #     log.error(f"'{const.SENSOR_TWILIO}' is not a valid communication sensor")
    #     raise InvalidProviderError(
    #         f"'{const.SENSOR_TWILIO}' is not a valid communication sensor."
    #     )

    # def send_message_via_twitter(
    #     self, msg: str, **kwargs: Any
    # ) -> typeDefSendMsgResponse:
    #     """Send message via Twitter.
    #
    #     This method sends a given message via Twitter either as 'status update' or as
    #     DM to a specific recipient. If the latter, then the recipient must be specified
    #     in the 'kwargs' arguments.
    #
    #     Args:
    #         msg:
    #             simple/plain text version of message to be sent
    #         kwargs:
    #             Additional optional arguments
    #
    #     Returns:
    #         List of 'response' records from Twitter. We always return a list
    #         even though we may only have a single item. This allows us to be consistent
    #         across all 'send_message()' functions.
    #
    #     Raises:
    #         InvalidProviderError: Twitter sensor is not valid/active
    #     """
    #     if self._sensors[const.SENSOR_TWITTER]:
    #         return self._sensors[const.SENSOR_TWITTER].send_message(msg, **kwargs)  # type: ignore[union-attr]  # noqa: B950
    #
    #     log.error(
    #         f"ERROR: '{const.SENSOR_TWITTER}' is not a valid communication sensor"
    #     )
    #     raise InvalidProviderError(
    #         f"'{const.SENSOR_TWITTER}' is not a valid communication sensor."
    #     )
