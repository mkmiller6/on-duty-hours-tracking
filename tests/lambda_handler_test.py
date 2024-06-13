# pylint: disable=missing-docstring, redefined-outer-name
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import pytest

from pytest_mock import MockerFixture
from lambda_function import handler

from config import INTERNAL_API_KEY, CLOCK_IN_ENTRY_NAME, CLOCK_OUT_ENTRY_NAME


@pytest.fixture(autouse=True)
def mock_base_function_calls(mocker: MockerFixture):
    mocker.patch("lambda_function.get_access_token").return_value = mocker.Mock()
    mocker.patch("lambda_function.build").return_value = mocker.Mock()


@pytest.fixture
def mock_clock_in_event_with_valid_key(mocker: MockerFixture):
    event = {
        "entryId": CLOCK_IN_ENTRY_NAME,
        "timestamp": 1706630094,
        "userId": 13804489,
        "apiKey": INTERNAL_API_KEY,
    }

    mocker.patch("lambda_function.DriveOperations.get_folder_id").return_value = "123"

    return {"body": json.dumps(event)}


@pytest.fixture
def mock_clock_in_event_with_invalid_key():
    event = {
        "entryId": CLOCK_IN_ENTRY_NAME,
        "timestamp": 1706630094,
        "userId": 13804489,
        "apiKey": "asfkl;jas",
    }

    return {"body": json.dumps(event)}


@pytest.fixture
def mock_clock_in_event_valid_key_datetimes(mock_clock_in_event_with_valid_key):
    timestamp = json.loads(mock_clock_in_event_with_valid_key["body"])["timestamp"]
    date = datetime.fromtimestamp(timestamp, tz=ZoneInfo("America/Chicago")).strftime(
        "%m/%d/%Y"
    )
    time = datetime.fromtimestamp(timestamp, tz=ZoneInfo("America/Chicago")).strftime(
        "%I:%M %p"
    )

    return {"date": date, "time": time}


@pytest.fixture
def mock_clock_out_event_with_valid_key(mocker: MockerFixture):
    event = {
        "entryId": CLOCK_OUT_ENTRY_NAME,
        "timestamp": 1706630094,
        "userId": 13804489,
        "apiKey": INTERNAL_API_KEY,
    }

    mocker.patch("lambda_function.DriveOperations.get_folder_id").return_value = "123"

    return {"body": json.dumps(event)}


@pytest.fixture
def mock_clock_out_event_valid_key_datetimes(mock_clock_out_event_with_valid_key):
    timestamp = json.loads(mock_clock_out_event_with_valid_key["body"])["timestamp"]
    date = datetime.fromtimestamp(timestamp, tz=ZoneInfo("America/Chicago")).strftime(
        "%m/%d/%Y"
    )
    time = datetime.fromtimestamp(timestamp, tz=ZoneInfo("America/Chicago")).strftime(
        "%I:%M %p"
    )

    return {"date": date, "time": time}


@pytest.fixture
def mock_clock_out_event_with_invalid_key():
    event = {
        "entryId": CLOCK_OUT_ENTRY_NAME,
        "timestamp": 1706630094,
        "userId": 13804489,
        "apiKey": "asfkl;jas",
    }

    return {"body": json.dumps(event)}


@pytest.fixture
def mock_nonsense_event():
    event = {
        "fakeKey1": "Nonsense",
        "blah": "blah",
    }

    return event


def test_handler_nonsense_event(mock_nonsense_event, caplog):
    with pytest.raises(Exception):
        handler(mock_nonsense_event, None)
        assert (
            "Error parsing event: {'fakeKey1': 'Nonsense', 'blah': 'blah'}"
            in caplog.text
        )


def test_handler_clock_in_invalid_key(mock_clock_in_event_with_invalid_key, caplog):
    result = handler(mock_clock_in_event_with_invalid_key, None)

    assert "Invalid API key" in caplog.text
    assert result == {"statusCode": 400}


def test_handler_clock_out_invalid_key(mock_clock_out_event_with_invalid_key, caplog):
    result = handler(mock_clock_out_event_with_invalid_key, None)

    assert "Invalid API key" in caplog.text
    assert result == {"statusCode": 400}


def test_handler_clock_in_valid_key_existing_volunteer_master_sheet_exsists_slack_user_exists(
    mock_clock_in_event_with_valid_key,
    mock_clock_in_event_valid_key_datetimes,
    mocker: MockerFixture,
    caplog,
):
    mocker.patch("helpers.openpath_classes.getUser").return_value = {
        "identity": {
            "firstName": "Joe",
            "lastName": "Shmoe",
            "email": "test@testemail.com",
        }
    }
    drive_mock = mocker.Mock()
    drive_mock.check_timesheet_exists.return_value = [
        {
            "id": "123",
            "name": "ODV Timesheet - Joe Shmoe",
            "mimeType": "application/vnd.google-apps.spreadsheet",
        }
    ]

    mocker.patch("lambda_function.DriveOperations").return_value = drive_mock

    sheets_mock = mocker.Mock()
    sheets_mock.check_master_log.return_value = True

    mocker.patch("lambda_function.SheetsOperations").return_value = sheets_mock

    slack_mock = mocker.Mock()
    slack_mock.get_slack_user_id.return_value = "ASLDKFJ123KLAJSD"
    slack_mock.clock_in_slack_message.return_value = mocker.Mock()

    mocker.patch("lambda_function.SlackOps").return_value = slack_mock

    result = handler(mock_clock_in_event_with_valid_key, None)

    assert (
        f"Parsed event: {{'entryId': '{CLOCK_IN_ENTRY_NAME}', 'timestamp': 1706630094, 'userId': 13804489}}"
        in caplog.text
    )
    assert "apiKey" not in caplog.text
    assert "Volunteer: Joe Shmoe" in caplog.text
    drive_mock.check_timesheet_exists.assert_called_once()
    drive_mock.create_timesheet.assert_not_called()
    sheets_mock.initialize_copied_template.assert_not_called()
    sheets_mock.add_clock_in_entry_to_timesheet.assert_has_calls(
        [
            mocker.call(
                (
                    mock_clock_in_event_valid_key_datetimes["date"],
                    mock_clock_in_event_valid_key_datetimes["time"],
                )
            ),
            mocker.call(
                (
                    mock_clock_in_event_valid_key_datetimes["date"],
                    mock_clock_in_event_valid_key_datetimes["time"],
                ),
                master=True,
            ),
        ]
    )
    sheets_mock.create_odv_sheet_in_master_spreadsheet.assert_not_called()
    drive_mock.add_volunteer_to_slideshow.assert_called_once()
    slack_mock.get_slack_user_id.assert_called_once()
    slack_mock.clock_in_slack_message.assert_called_once_with(
        "ASLDKFJ123KLAJSD",
    )
    sheets_mock.add_clock_out_entry_to_timesheet.assert_not_called()
    drive_mock.remove_volunteer_from_slideshow.assert_not_called()
    slack_mock.clock_out_slack_message.assert_not_called()

    assert result == {"statusCode": 200}


def test_handler_clock_in_valid_key_existing_volunteer_master_sheet_exsists_slack_user_not_exists(
    mock_clock_in_event_with_valid_key,
    mock_clock_in_event_valid_key_datetimes,
    mocker: MockerFixture,
    caplog,
):
    mocker.patch("helpers.openpath_classes.getUser").return_value = {
        "identity": {
            "firstName": "Joe",
            "lastName": "Shmoe",
            "email": "test@testemail.com",
        }
    }
    drive_mock = mocker.Mock()
    drive_mock.check_timesheet_exists.return_value = [
        {
            "id": "123",
            "name": "ODV Timesheet - Joe Shmoe",
            "mimeType": "application/vnd.google-apps.spreadsheet",
        }
    ]

    mocker.patch("lambda_function.DriveOperations").return_value = drive_mock

    sheets_mock = mocker.Mock()
    sheets_mock.check_master_log.return_value = True

    mocker.patch("lambda_function.SheetsOperations").return_value = sheets_mock

    slack_mock = mocker.Mock()
    slack_mock.get_slack_user_id.return_value = None
    slack_mock.clock_in_slack_message.return_value = mocker.Mock()

    mocker.patch("lambda_function.SlackOps").return_value = slack_mock

    result = handler(mock_clock_in_event_with_valid_key, None)

    assert (
        f"Parsed event: {{'entryId': '{CLOCK_IN_ENTRY_NAME}', 'timestamp': 1706630094, 'userId': 13804489}}"
        in caplog.text
    )
    assert "apiKey" not in caplog.text
    assert "Volunteer: Joe Shmoe" in caplog.text
    drive_mock.check_timesheet_exists.assert_called_once()
    drive_mock.create_timesheet.assert_not_called()
    sheets_mock.initialize_copied_template.assert_not_called()
    sheets_mock.add_clock_in_entry_to_timesheet.assert_has_calls(
        [
            mocker.call(
                (
                    mock_clock_in_event_valid_key_datetimes["date"],
                    mock_clock_in_event_valid_key_datetimes["time"],
                )
            ),
            mocker.call(
                (
                    mock_clock_in_event_valid_key_datetimes["date"],
                    mock_clock_in_event_valid_key_datetimes["time"],
                ),
                master=True,
            ),
        ]
    )
    sheets_mock.create_odv_sheet_in_master_spreadsheet.assert_not_called()
    drive_mock.add_volunteer_to_slideshow.assert_called_once()
    slack_mock.get_slack_user_id.assert_called_once()
    slack_mock.clock_in_slack_message.assert_called_once_with(None)
    assert "Slack user not found for: Joe Shmoe" in caplog.text
    sheets_mock.add_clock_out_entry_to_timesheet.assert_not_called()
    drive_mock.remove_volunteer_from_slideshow.assert_not_called()
    slack_mock.clock_out_slack_message.assert_not_called()

    assert result == {"statusCode": 200}


def test_handler_clock_in_valid_key_existing_volunteer_master_sheet_not_exsists_slack_user_exists(
    mock_clock_in_event_with_valid_key,
    mock_clock_in_event_valid_key_datetimes,
    mocker: MockerFixture,
    caplog,
):
    mocker.patch("helpers.openpath_classes.getUser").return_value = {
        "identity": {
            "firstName": "Joe",
            "lastName": "Shmoe",
            "email": "test@testemail.com",
        }
    }
    drive_mock = mocker.Mock()
    drive_mock.check_timesheet_exists.return_value = [
        {
            "id": "123",
            "name": "ODV Timesheet - Joe Shmoe",
            "mimeType": "application/vnd.google-apps.spreadsheet",
        }
    ]

    mocker.patch("lambda_function.DriveOperations").return_value = drive_mock

    sheets_mock = mocker.Mock()
    sheets_mock.check_master_log.return_value = False

    mocker.patch("lambda_function.SheetsOperations").return_value = sheets_mock

    slack_mock = mocker.Mock()
    slack_mock.get_slack_user_id.return_value = "123456"
    slack_mock.clock_in_slack_message.return_value = mocker.Mock()

    mocker.patch("lambda_function.SlackOps").return_value = slack_mock

    result = handler(mock_clock_in_event_with_valid_key, None)

    assert (
        f"Parsed event: {{'entryId': '{CLOCK_IN_ENTRY_NAME}', 'timestamp': 1706630094, 'userId': 13804489}}"
        in caplog.text
    )
    assert "apiKey" not in caplog.text
    assert "Volunteer: Joe Shmoe" in caplog.text
    drive_mock.check_timesheet_exists.assert_called_once()
    drive_mock.create_timesheet.assert_not_called()
    sheets_mock.initialize_copied_template.assert_not_called()
    sheets_mock.add_clock_in_entry_to_timesheet.assert_has_calls(
        [
            mocker.call(
                (
                    mock_clock_in_event_valid_key_datetimes["date"],
                    mock_clock_in_event_valid_key_datetimes["time"],
                )
            ),
            mocker.call(
                (
                    mock_clock_in_event_valid_key_datetimes["date"],
                    mock_clock_in_event_valid_key_datetimes["time"],
                ),
                master=True,
            ),
        ]
    )
    sheets_mock.create_odv_sheet_in_master_spreadsheet.assert_called_once()
    drive_mock.add_volunteer_to_slideshow.assert_called_once()
    slack_mock.get_slack_user_id.assert_called_once()
    slack_mock.clock_in_slack_message.assert_called_once_with("123456")
    sheets_mock.add_clock_out_entry_to_timesheet.assert_not_called()
    drive_mock.remove_volunteer_from_slideshow.assert_not_called()
    slack_mock.clock_out_slack_message.assert_not_called()

    assert result == {"statusCode": 200}


def test_handler_clock_in_valid_key_new_volunteer_master_sheet_not_exsists_slack_user_exists(
    mock_clock_in_event_with_valid_key,
    mock_clock_in_event_valid_key_datetimes,
    mocker: MockerFixture,
    caplog,
):
    mocker.patch("helpers.openpath_classes.getUser").return_value = {
        "identity": {
            "firstName": "Joe",
            "lastName": "Shmoe",
            "email": "test@testemail.com",
        }
    }
    drive_mock = mocker.Mock()
    drive_mock.check_timesheet_exists.return_value = []

    mocker.patch("lambda_function.DriveOperations").return_value = drive_mock

    sheets_mock = mocker.Mock()
    sheets_mock.check_master_log.return_value = False

    mocker.patch("lambda_function.SheetsOperations").return_value = sheets_mock

    slack_mock = mocker.Mock()
    slack_mock.get_slack_user_id.return_value = "123456"
    slack_mock.clock_in_slack_message.return_value = mocker.Mock()

    mocker.patch("lambda_function.SlackOps").return_value = slack_mock

    result = handler(mock_clock_in_event_with_valid_key, None)

    assert (
        f"Parsed event: {{'entryId': '{CLOCK_IN_ENTRY_NAME}', 'timestamp': 1706630094, 'userId': 13804489}}"
        in caplog.text
    )
    assert "apiKey" not in caplog.text
    assert "Volunteer: Joe Shmoe" in caplog.text
    drive_mock.check_timesheet_exists.assert_called_once()
    drive_mock.create_timesheet.assert_called_once()
    sheets_mock.initialize_copied_template.assert_called_once()
    sheets_mock.add_clock_in_entry_to_timesheet.assert_has_calls(
        [
            mocker.call(
                (
                    mock_clock_in_event_valid_key_datetimes["date"],
                    mock_clock_in_event_valid_key_datetimes["time"],
                )
            ),
            mocker.call(
                (
                    mock_clock_in_event_valid_key_datetimes["date"],
                    mock_clock_in_event_valid_key_datetimes["time"],
                ),
                master=True,
            ),
        ]
    )
    sheets_mock.create_odv_sheet_in_master_spreadsheet.assert_called_once()
    drive_mock.add_volunteer_to_slideshow.assert_called_once()
    slack_mock.get_slack_user_id.assert_called_once()
    slack_mock.clock_in_slack_message.assert_called_once_with("123456")
    sheets_mock.add_clock_out_entry_to_timesheet.assert_not_called()
    drive_mock.remove_volunteer_from_slideshow.assert_not_called()
    slack_mock.clock_out_slack_message.assert_not_called()

    assert result == {"statusCode": 200}


def test_handler_clock_out_valid_key_existing_volunteer_master_sheet_exsists_slack_user_exists(
    mock_clock_out_event_with_valid_key,
    mock_clock_out_event_valid_key_datetimes,
    mocker: MockerFixture,
    caplog,
):
    mocker.patch("helpers.openpath_classes.getUser").return_value = {
        "identity": {
            "firstName": "Joe",
            "lastName": "Shmoe",
            "email": "test@testemail.com",
        }
    }
    drive_mock = mocker.Mock()
    drive_mock.check_timesheet_exists.return_value = [
        {
            "id": "123",
            "name": "ODV Timesheet - Joe Shmoe",
            "mimeType": "application/vnd.google-apps.spreadsheet",
        }
    ]

    mocker.patch("lambda_function.DriveOperations").return_value = drive_mock

    sheets_mock = mocker.Mock()
    sheets_mock.check_master_log.return_value = True

    mocker.patch("lambda_function.SheetsOperations").return_value = sheets_mock

    slack_mock = mocker.Mock()
    slack_mock.get_slack_user_id.return_value = "123456"
    slack_mock.clock_in_slack_message.return_value = mocker.Mock()

    mocker.patch("lambda_function.SlackOps").return_value = slack_mock

    result = handler(mock_clock_out_event_with_valid_key, None)

    assert (
        f"Parsed event: {{'entryId': '{CLOCK_OUT_ENTRY_NAME}', 'timestamp': 1706630094, 'userId': 13804489}}"
        in caplog.text
    )
    assert "apiKey" not in caplog.text
    assert "Volunteer: Joe Shmoe" in caplog.text
    drive_mock.check_timesheet_exists.assert_called_once()
    drive_mock.create_timesheet.assert_not_called()
    sheets_mock.initialize_copied_template.assert_not_called()
    sheets_mock.add_clock_out_entry_to_timesheet.assert_has_calls(
        [
            mocker.call(
                mock_clock_out_event_valid_key_datetimes["time"],
            ),
            mocker.call(
                mock_clock_out_event_valid_key_datetimes["time"],
                master=True,
            ),
        ]
    )
    sheets_mock.create_odv_sheet_in_master_spreadsheet.assert_not_called()
    drive_mock.add_volunteer_to_slideshow.assert_not_called()
    slack_mock.get_slack_user_id.assert_called_once()
    slack_mock.clock_in_slack_message.assert_not_called()
    sheets_mock.add_clock_in_entry_to_timesheet.assert_not_called()
    drive_mock.remove_volunteer_from_slideshow.assert_called_once()
    slack_mock.clock_out_slack_message.assert_called_once()

    assert result == {"statusCode": 200}
