"""
Test Openpath dataclasses.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from pytest_mock import MockerFixture

from helpers.openpath_classes import OpenpathEvent, OpenpathUser


def test_openpath_event():
    """
    Test OpenpathEvent class.
    """
    event = OpenpathEvent("test", 123, 1706833599)
    assert event.entry == "test"
    assert event.user_id == 123
    assert event.timestamp == 1706833599
    assert event.timestamp_datetime == datetime.fromtimestamp(
        1706833599, tz=ZoneInfo("America/Chicago")
    )
    assert event.date == datetime.fromtimestamp(
        1706833599, tz=ZoneInfo("America/Chicago")
    ).strftime("%m/%d/%Y")
    assert event.time == datetime.fromtimestamp(
        1706833599, tz=ZoneInfo("America/Chicago")
    ).strftime("%I:%M %p")


def test_openpath_user(mocker: MockerFixture):
    """
    Test OpenpathUser class.
    """

    mocker.patch("helpers.openpath_classes.getUser").return_value = {
        "identity": {
            "firstName": "Joe",
            "lastName": "Shmoe",
            "email": "test@testemail.com",
        }
    }

    user = OpenpathUser(123)
    assert user.user_id == 123
    assert user.full_name == "Joe Shmoe"
    assert user.email == "test@testemail.com"
    assert user.first_name == "Joe"
    assert user.last_name == "Shmoe"

    assert user.user_data == {
        "identity": {
            "firstName": "Joe",
            "lastName": "Shmoe",
            "email": "test@testemail.com",
        }
    }
