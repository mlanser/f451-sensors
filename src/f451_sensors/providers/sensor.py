"""Interface/base classes used in f451 Sensors module.

This module holds base classes used for various sensor
components (e.g. temperature, humidity, speed, etc.).
"""
import logging
import pprint
from abc import ABC
from abc import abstractmethod
from pathlib import Path
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from requests import Response as reqResponse
from rich import print as rprint
from rich.pretty import pprint as rpp
from rich.rule import Rule

import f451_sensors.constants as const
from f451_sensors.exceptions import InvalidAttributeError
from f451_sensors.exceptions import SensorAccessError
from f451_sensors.exceptions import SensorConnectionError

__all__ = [
    "Response",
    "Sensor",
    "is_valid_file",
    "verify_file",
]

# =========================================================
#          G L O B A L S   A N D   H E L P E R S
# =========================================================
log = logging.getLogger()
pp = pprint.PrettyPrinter(indent=4)

# Default set of valid (pseudo) formats
# DATA_FORMATS = (
#     const.FMT_KWD_STR,  # strings (e.g. "some long string")
#     const.FMT_KWD_STRIDX,  # strings as index (for SQL data stores)
#     const.FMT_KWD_INT,  # integers (e.g. 1, 2, 3, ... gazillion ... maybe ;-)
#     const.FMT_KWD_INTIDX,  # integers as index (for SQL data stores)
#     const.FMT_KWD_FLOAT,  # floats (e.g. 0.1. 0.22, 0.333, ... )
#     const.FMT_KWD_BOOL,  # booleans (e.g. True|False, Yes|No, etc.)
# )


# =========================================================
#       C O M M O N   U T I L I T Y    C L A S S E S
# =========================================================


# =========================================================
#       C O R E   C L A S S   D E F I N I T I O N S
# =========================================================
class Response:
    """Generic response class.

    This class provides a standard interface for responses from sending messages
    via various communication services.

    Attributes:
        status:
            Response status string. const.STATUS_SUCCESS or const.STATUS_SUCCESS
        sensor:
            Provider name that returned that response. Correlates to :attr:'~notifiers.core.Provider.name'
        data:
            The notification data that was used for the notification
        response:
            The response object that was returned. Usually :class:'requests.Response'
        errors:
            Holds a list of errors if relevant

    Note:
        This class is inspired by the "Response" class in the "Notifiers" module
        by Or Carmi: https://github.com/liiight/notifiers
    """

    def __init__(
        self,
        status: str,
        sensor: str,
        data: Any,
        response: Optional[reqResponse] = None,
        errors: Any = None,
    ):
        self.status: str = status
        self.sensor: str = sensor
        self.data: Any = data
        self.response: Optional[reqResponse] = response
        self.errors: Any = errors

    def __repr__(self) -> str:
        return f"<Response,sensor={self.sensor.capitalize()},status={self.status}, errors={self.errors}>"  # noqa: B950

    def raise_on_errors(self) -> None:
        """Raise exception on error in request response.

        Raises:
             SensorConnectionError: if request response has errors
        """
        if self.errors:
            raise SensorConnectionError(
                sensor=self.sensor,
                data=self.data,
                errors=self.errors,
                response=self.response,
            )

    @property
    def isOK(self) -> bool:
        """Return 'true' (boolean) if no errors."""
        return self.errors is None


class Sensor(ABC):
    """Base class for physical and virtual sensors.

    Attributes:
        sensorType:
            data storage type (e.g. CSV, JSON, SQL, etc.)
        sensorName:
            data storage name (e.g. CSV, JSON, SQLite, PostgreSQL, etc.)
        configSection:
            name of section in config files (e.g. f451_csv, f451_sqlite, etc.)
        mqttHost:
            name of database host (for SQL) and database file (for file-based)
        mqttTopic:
            port number for database host (for SQL)
    """

    def __init__(
        self,
        sensorType: str,
        sensorName: str,
        configSection: str,
        mqttHost: str = '',
        mqttTopic: str = '',
    ) -> None:
        self._snsrType: str = sensorType
        self._snsrName: str = sensorName
        self._sctnName: str = configSection
        self._mqttHost: str = mqttHost
        self._mqttTopic: str = mqttTopic

    def __repr__(self) -> str:
        return f"<Sensor, type={self._snsrType}, name={self._snsrName}>"

    @property
    def sensorType(self) -> str:
        """Return 'sensorType' property."""
        return self._snsrType

    @property
    def sensorName(self) -> str:
        """Return 'sensorName' property."""
        return self._snsrName

    @property
    def configSection(self) -> str:
        """Return 'configSection' property."""
        return self._sctnName

    @property
    def mqttHost(self) -> str:
        """Return 'mqttHost' property."""
        return self._mqttHost

    @property
    def mqttTopic(self) -> str:
        """Return 'mqttTopic' property."""
        return self._mqttTopic

    @abstractmethod
    def collect_data(self, **kwargs: Any) -> Dict[str, Any]:
        """Stub for 'collect_data()' method."""
        pass

    @abstractmethod
    def publish_data(self, inDelay: int = 1, iterMax: int = 0, **kwargs: Any) -> int:
        """Stub for 'publish_data()' method."""
        pass

    def _make_response(
        self,
        data: Any = None,
        response: Optional[reqResponse] = None,
        errors: Any = None,
    ) -> Response:
        """Generate 'Response' object.

        Args:
            data:
                Data that was submitted during call to 'send_message()' (and similar) methods
            response:
               'requests.Response' class if available
            errors:
                List of errors if available

        Returns:
            'Response' object

        Note:
            This method is inspired by the "create_response" method in the "Notifiers" module
            by Or Carmi: https://github.com/liiight/notifiers
        """
        status = const.STATUS_FAILURE if errors else const.STATUS_SUCCESS
        return Response(
            status=status,
            sensor=self._snsrName,
            data=data,
            response=response,
            errors=errors,
        )


# =========================================================
#              U T I L I T Y   F U N C T I O N S
# =========================================================
def is_valid_file(fName: Union[Path, str]) -> bool:
    """Verify that a file exists.

    Args:
        fName:
            Single filename (Path object or string).

    Returns:
        'True' if files exists.
    """
    fp = Path(fName) if isinstance(fName, str) else fName
    return fp.exists() and fp.is_file()


def verify_file(fName: str, strict: bool) -> str:
    """Verify that a file exists and return Path object.

    This function will raise an exception if 'strict' is set to 'True'.

    Args:
        fName:
            Single filename (Path object or string).
        strict:
            If 'True' then exception is raised when file does not exist

    Returns:
        Given file name 'str' if it exists and 'strict' is 'True'. This will
        also return an empty string if the path is not valid.

    Raises:
        InvalidAttributeError: If file does not exist
    """
    isValid = is_valid_file(fName)

    if strict and not isValid:
        log.error(f"File '{fName or '<blank>'}' does not exist.")
        raise InvalidAttributeError(f"File '{fName or '<blank>'}' does not exist.")

    return fName


def pretty_print_response_records(inData: Any) -> None:
    """Helper: Pretty print response records.

    Args:
        inData:
            Data (response records) to be printed.
    """

    def _print_item(item: Any, printRule: bool = False) -> None:
        if printRule:
            rprint(Rule())

        rprint(type(item))
        rpp(item, expand_all=True)

    recList = inData if isinstance(inData, list) else [inData]

    for i, rec in enumerate(recList):
        if isinstance(rec, list):
            for ii, subRec in enumerate(rec):
                _print_item(subRec, i > 0 and ii > 0)

        else:
            _print_item(rec, i > 0)
