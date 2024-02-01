"""
Dataclasses to hold Openpath user and event data.
"""

from datetime import datetime
from zoneinfo import ZoneInfo
from dataclasses import dataclass

from helpers.openPathUtil import getUser


@dataclass
class OpenpathEvent:
    """
    Class to hold Openpath event data.
    """

    entry: str
    user_id: int
    timestamp: int
    timestamp_datetime: datetime = None
    date: str = None
    time: str = None

    def __post_init__(self):
        self.timestamp_datetime = datetime.fromtimestamp(
            self.timestamp, tz=ZoneInfo("America/Chicago")
        )
        self.date = self.timestamp_datetime.strftime("%m/%d/%Y")
        self.time = self.timestamp_datetime.strftime("%I:%M %p")


@dataclass
class OpenpathUser:
    """
    Class to hold Openpath user data.
    """

    user_id: int
    user_data: dict = None
    first_name: str = None
    last_name: str = None
    full_name: str = None
    email: str = None

    def __post_init__(self):
        self.user_data = getUser(self.user_id)
        self.first_name = self.user_data.get("identity").get("firstName")
        self.last_name = self.user_data.get("identity").get("lastName")
        self.full_name = f"{self.first_name} {self.last_name}"
        self.email = self.user_data.get("identity").get("email")
