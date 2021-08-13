"""Constants for the Flipr integration."""
import enum
from dataclasses import dataclass

DOMAIN = "flipr"

CONF_USERNAME = "email"
CONF_PASSWORD = "password"

ATTRIBUTION = "Flipr Data"
MANUFACTURER = "CTAC-TECH"
NAME = "Flipr"

API_TIMEOUT = 100

MODE_HUB_AUTO = "auto"
MODE_HUB_MANUAL = "manual"
MODE_HUB_PLANNING = "planning"
HUB_MODES = [MODE_HUB_AUTO, MODE_HUB_MANUAL, MODE_HUB_PLANNING]


class FliprType(enum.Enum):
    """The Flipr speech types."""
    hub = "hub"
    flipr = "flipr"


@dataclass
class FliprResult:
    """Wrapper class to hold an Flipr device and set of data."""
    id: str
    type: FliprType
    data: dict
