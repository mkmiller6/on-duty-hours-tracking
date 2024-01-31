import pytest
from pytest_mock import MockerFixture
import requests_mock

from helpers.slack import SlackOps

@pytest.fixture
def user_with_email():
    return SlackOps("nicovaulter6@gmail.com", "Nick Maskal")

@pytest.fixture
def no_user():
    return SlackOps("oshofmann@gmail.com", "Owen Hofmnan")

@pytest.fixture
def email_only_user():
    return SlackOps("matthew.miller@asmbly.org", "")

def test_get_slack_user_id(user_with_email: SlackOps):
    assert user_with_email.get_slack_user_id() == "U06CVGHD1GC"

def test_get_slack_user_id_not_found(no_user: SlackOps):
    assert no_user.get_slack_user_id() is None

def test_get_slack_user_id_by_email(email_only_user: SlackOps):
    assert email_only_user.get_slack_user_id() == "U03P4JKB7PE"


def test_get_slack_user_id_status_400_list(user_with_email: SlackOps, caplog):
    with requests_mock.Mocker() as m:
        m.get(
            "https://slack.com/api/users.list",
            status_code=400,
            json={"ok": False},
        )

        user_with_email.get_slack_user_id()

    assert "Get https://slack.com/api/users.list returned status code 400" in caplog.text

def test_get_slack_user_id_ok_false_list(user_with_email: SlackOps, mocker: MockerFixture, caplog):
    with requests_mock.Mocker() as m:
        m.get(
            "https://slack.com/api/users.list",
            status_code=200,
            json={"ok": False},
        )

        response = user_with_email.get_slack_user_id()

    assert response is None

    assert "Get https://slack.com/api/users.list returned error: " in caplog.text

def test_get_slack_user_id_status_400_email(user_with_email: SlackOps, mocker: MockerFixture, caplog):
    with requests_mock.Mocker() as m:
        m.get(
            "https://slack.com/api/users.list",
            status_code=200,
            json={"ok": True, "members": []},
        )

        m.get(
            "https://slack.com/api/users.lookupByEmail",
            status_code=400,
            json={"ok": False},
        )

        response = user_with_email.get_slack_user_id()

    assert response is None

    assert "Get https://slack.com/api/users.lookupByEmail returned status code 400" in caplog.text

def test_get_slack_user_id_ok_false_email(user_with_email: SlackOps, mocker: MockerFixture, caplog):
    with requests_mock.Mocker() as m:
        m.get(
            "https://slack.com/api/users.list",
            status_code=200,
            json={"ok": True, "members": []},
        )

        m.get(
            "https://slack.com/api/users.list",
            status_code=200,
            json={"ok": False},
        )

        response = user_with_email.get_slack_user_id()

    assert response is None

def test_clock_in_slack_message_with_user_id(user_with_email: SlackOps, mocker: MockerFixture):
    mocker.patch(
        "helpers.slack.requests.post"
    ).return_value.json.return_value = {
        "ok": True,
    }

    assert user_with_email.clock_in_slack_message("U06CVGHD1GC") == {
        "blocks": [
            {
                "type": "rich_text",
                "elements": [
                    {
                        "type": "rich_text_section",
                        "elements": [
                            {
                                "type": "user",
                                "user_id": "U06CVGHD1GC",
                            },
                            {
                                "type": "text",
                                "text": " is now on duty.",
                            },
                        ],
                    }
                ],
            },
        ],
    }

def test_clock_in_slack_message_no_user_id(no_user: SlackOps):
    assert no_user.clock_in_slack_message(None) == {
                "blocks": [
                    {
                        "type": "rich_text",
                        "elements": [
                            {
                                "type": "rich_text_section",
                                "elements": [
                                    {
                                        "type:": "text",
                                        "text": "Owen Hofmnan",
                                        "style": {
                                            "bold": True
                                        }
                                    },
                                    {
                                        "type": "text",
                                        "text": " is now on duty.",
                                    }
                                ],
                            }
                        ],
                    },
                ],
            }

def test_clock_out_slack_message_with_user_id(user_with_email: SlackOps, mocker: MockerFixture):
    mocker.patch(
        "helpers.slack.requests.post"
    ).return_value.json.return_value = {
        "ok": True,
    }

    assert user_with_email.clock_out_slack_message("U06CVGHD1GC") == {
        "blocks": [
            {
                "type": "rich_text",
                "elements": [
                    {
                        "type": "rich_text_section",
                        "elements": [
                            {
                                "type": "user",
                                "user_id": "U06CVGHD1GC",
                            },
                            {
                                "type": "text",
                                "text": " is now off duty.",
                            },
                        ],
                    }
                ],
            },
        ],
    }

def test_clock_out_slack_message_no_user_id(no_user: SlackOps):
    assert no_user.clock_out_slack_message(None) == {
                "blocks": [
                    {
                        "type": "rich_text",
                        "elements": [
                            {
                                "type": "rich_text_section",
                                "elements": [
                                    {
                                        "type:": "text",
                                        "text": "Owen Hofmnan",
                                        "style": {
                                            "bold": True
                                        }
                                    },
                                    {
                                        "type": "text",
                                        "text": " is now off duty.",
                                    }
                                ],
                            }
                        ],
                    },
                ],
            }
