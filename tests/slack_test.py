# pylint: disable=missing-docstring
# pylint: disable=redefined-outer-name

import pytest
from pytest_mock import MockerFixture
import requests_mock
import requests

from helpers.slack import SlackOps, lookup_by_email, lookup_by_name


@pytest.fixture
def user_with_email():
    return SlackOps("nicovaulter6@gmail.com", "Nick", "Maskal")


@pytest.fixture
def no_user():
    return SlackOps("oshofmann@gmail.com", "Owen", "Hofmann")


@pytest.fixture
def user_with_only_first_name():
    return SlackOps("email.not.in.slack@test.com", "Joe", "Schmoe")


@pytest.fixture
def email_only_user():
    return SlackOps("matthew.miller@asmbly.org", "", "")


@pytest.fixture
def slack_api_user_list(mocker: MockerFixture):
    mocker.Mock().side_effect = {
        "ok": True,
        "members": [
            {"id": "U06CVGHD1GC", "profile": {"real_name": "Nick Maskal"}},
            {"id": "asdfasdf", "profile": {"real_name": "Joe"}},
        ],
    }


def test_lookup_by_email_with_email(user_with_email: SlackOps):
    session = requests.Session()

    with requests_mock.Mocker(session=session) as m:
        m.get(
            "https://slack.com/api/users.lookupByEmail",
            status_code=200,
            json={"ok": True, "user": {"id": "U06CVGHD1GC"}},
        )

        assert lookup_by_email(session, user_with_email.user_email) == "U06CVGHD1GC"


def test_lookup_by_email_no_email(user_with_only_first_name: SlackOps):
    session = requests.Session()

    with requests_mock.Mocker(session=session) as m:
        m.get(
            "https://slack.com/api/users.lookupByEmail",
            status_code=200,
            json={"ok": False, "error": "user_not_found"},
        )

        assert lookup_by_email(session, user_with_only_first_name.user_email) is None


def test_lookup_by_name_full_name(user_with_email: SlackOps):
    session = requests.Session()

    with requests_mock.Mocker(session=session) as m:
        m.get(
            "https://slack.com/api/users.list",
            status_code=200,
            json={
                "ok": True,
                "members": [
                    {"id": "U06CVGHD1GC", "profile": {"real_name": "Nick Maskal"}},
                    {"id": "asdfasdf", "profile": {"real_name": "Joe Schmoe"}},
                ],
            },
        )

        assert (
            lookup_by_name(
                session,
                user_with_email.first_name,
                user_with_email.last_name,
                "test_channel",
            )
            == "U06CVGHD1GC"
        )


def test_lookup_by_name_first_name_only(
    user_with_only_first_name: SlackOps, mocker: MockerFixture
):
    mocker.patch("helpers.slack.lookup_users_in_channel").return_value = set(
        [
            "asdfasdf",
            "U06CVGHD1GC",
        ]
    )

    session = requests.Session()

    with requests_mock.Mocker(session=session) as m:
        m.get(
            "https://slack.com/api/users.list",
            status_code=200,
            json={
                "ok": True,
                "members": [
                    {"id": "U06CVGHD1GC", "profile": {"real_name": "Nick Maskal"}},
                    {"id": "asdfasdf", "profile": {"real_name": "Joe"}},
                ],
            },
        )

        assert (
            lookup_by_name(
                session,
                user_with_only_first_name.first_name,
                user_with_only_first_name.last_name,
                "test_channel",
            )
            == "asdfasdf"
        )


def test_lookup_by_name_first_name_only_no_users_in_channel(
    user_with_only_first_name: SlackOps, mocker: MockerFixture
):
    mocker.patch("helpers.slack.lookup_users_in_channel").return_value = set([])

    session = requests.Session()

    with requests_mock.Mocker(session=session) as m:
        m.get(
            "https://slack.com/api/users.list",
            status_code=200,
            json={
                "ok": True,
                "members": [
                    {"id": "U06CVGHD1GC", "profile": {"real_name": "Nick Maskal"}},
                    {"id": "asdfasdf", "profile": {"real_name": "Joe"}},
                ],
            },
        )

        assert (
            lookup_by_name(
                session,
                user_with_only_first_name.first_name,
                user_with_only_first_name.last_name,
                "test_channel",
            )
            is None
        )


def test_lookup_by_name_first_name_only_multiple_matches(
    user_with_only_first_name: SlackOps, mocker: MockerFixture, caplog
):
    mocker.patch("helpers.slack.lookup_users_in_channel").return_value = set(
        [
            "asdfasdf",
            "U06CVGHD1GC",
        ]
    )

    session = requests.Session()

    with requests_mock.Mocker(session=session) as m:
        m.get(
            "https://slack.com/api/users.list",
            status_code=200,
            json={
                "ok": True,
                "members": [
                    {"id": "U06CVGHD1GC", "profile": {"real_name": "Joe"}},
                    {"id": "asdfasdf", "profile": {"real_name": "Joe"}},
                ],
            },
        )

        response = lookup_by_name(
            session,
            user_with_only_first_name.first_name,
            user_with_only_first_name.last_name,
            "test_channel",
        )

        assert (
            "Volunteer's name (Joe) is ambiguous in Slack, so we aren't sending a message"
            in caplog.text
        )

        assert response is None


def test_get_slack_user_id_with_email(user_with_email: SlackOps, mocker: MockerFixture):

    mocker.patch("helpers.slack.lookup_by_email").return_value = "test_response"

    assert user_with_email.get_slack_user_id() == "test_response"


def test_get_slack_user_id_without_email(
    user_with_email: SlackOps, mocker: MockerFixture
):

    mocker.patch("helpers.slack.lookup_by_email").return_value = None

    mocker.patch("helpers.slack.lookup_by_name").return_value = "test_response"

    assert user_with_email.get_slack_user_id() == "test_response"


def test_get_slack_user_id_not_found(user_with_email: SlackOps, mocker: MockerFixture):

    mocker.patch("helpers.slack.lookup_by_email").return_value = None

    mocker.patch("helpers.slack.lookup_by_name").return_value = None

    assert user_with_email.get_slack_user_id() is None


def test_get_slack_user_id_by_email(email_only_user: SlackOps):

    with requests_mock.Mocker() as m:
        m.get(
            "https://slack.com/api/users.list",
            status_code=200,
            json={
                "ok": True,
                "members": [
                    {"id": "U06CVGHD1GC", "profile": {"real_name": "Nick Maskal"}},
                    {"id": "asdfasdf", "profile": {"real_name": "Joe Schmoe"}},
                ],
            },
        )

        m.get(
            "https://slack.com/api/users.lookupByEmail",
            status_code=200,
            json={"ok": True, "user": {"id": "U03P4JKB7PE"}},
        )
        assert email_only_user.get_slack_user_id() == "U03P4JKB7PE"


def test_clock_in_slack_message_with_user_id(
    user_with_email: SlackOps, mocker: MockerFixture
):
    mocker.patch("helpers.slack.requests.post").return_value.json.return_value = {
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


def test_clock_in_slack_message_no_user_id(no_user: SlackOps, mocker: MockerFixture):
    mocker.patch("helpers.slack.requests.post").return_value = mocker.Mock()

    assert no_user.clock_in_slack_message(slack_id=None) == {
        "blocks": [
            {
                "type": "rich_text",
                "elements": [
                    {
                        "type": "rich_text_section",
                        "elements": [
                            {
                                "type:": "text",
                                "text": "Owen Hofmann",
                                "style": {"bold": True},
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


def test_clock_out_slack_message_with_user_id(
    user_with_email: SlackOps, mocker: MockerFixture
):
    mocker.patch("helpers.slack.requests.post").return_value.json.return_value = {
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


def test_clock_out_slack_message_no_user_id(no_user: SlackOps, mocker: MockerFixture):
    mocker.patch("helpers.slack.requests.post").return_value = mocker.Mock()

    assert no_user.clock_out_slack_message(slack_id=None) == {
        "blocks": [
            {
                "type": "rich_text",
                "elements": [
                    {
                        "type": "rich_text_section",
                        "elements": [
                            {
                                "type:": "text",
                                "text": "Owen Hofmann",
                                "style": {"bold": True},
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
