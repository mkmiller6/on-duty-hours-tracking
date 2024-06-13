"""
Helpers for Slack.
"""

import os
import logging
import requests

if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None:
    from credentials import SLACK_WEBHOOK_URL, SLACK_TOKEN, SLACK_ON_DUTY_CHANNEL_ID
else:
    from config import SLACK_WEBHOOK_URL, SLACK_TOKEN, SLACK_ON_DUTY_CHANNEL_ID


def lookup_users_in_channel(session: requests.Session, channel_id: str) -> set | None:
    """
    Find all user IDs in the given channel_id
    """
    url = "https://slack.com/api/conversations.members"
    params = {"channel": channel_id}
    response = session.get(
        url=url,
        params=params,
        timeout=10,
    )

    if response.status_code != 200:
        logging.error("Get %s returned status code %s", url, response.status_code)
        return None

    response = response.json()

    if response.get("ok") is False:
        logging.error("Get %s returned error: %s", url, response.get("error"))
        return None

    return set(response.get("members"))


def lookup_by_email(session: requests.Session, email: str) -> int | None:
    """Lookup a Slack user by email address"""
    url = "https://slack.com/api/users.lookupByEmail"
    params = {"email": email}
    response = session.get(
        url=url,
        params=params,
        timeout=10,
    )

    if response.status_code != 200:
        logging.error("Get %s returned status code %s", url, response.status_code)
        return None

    response = response.json()

    if response.get("ok") is False:
        return None

    return response.get("user").get("id")


def lookup_by_name(
    session: requests.Session, first_name: str, last_name: str, channel_id: str
) -> int | None:
    """
    Lookup a Slack user by name. First checks for a full name match. If no match, filters
    by first name only, and checks if there is a single match in the given channel_id. If so
    return that user ID.
    """
    url = "https://slack.com/api/users.list"
    params = {"limit": 300}
    response = session.get(
        url=url,
        params=params,
        timeout=10,
    )

    if response.status_code != 200:
        logging.error("Get %s returned status code %s", url, response.status_code)
        return None

    response = response.json()

    if response.get("ok") is False:
        logging.error("Get %s returned error: %s", url, response.get("error"))
        return None

    if any(
        (user := member).get("profile").get("real_name")
        == (first_name + " " + last_name)
        for member in response["members"]
    ):
        return user.get("id")

    potentials = list(
        filter(
            lambda x: first_name in x.get("profile").get("real_name"),
            response["members"],
        )
    )

    potentials_ids = {user.get("id") for user in potentials}

    users_in_on_duty_channel = lookup_users_in_channel(session, channel_id)

    if not users_in_on_duty_channel:
        return None

    potentials_in_channel = potentials_ids & users_in_on_duty_channel

    if len(potentials_in_channel) == 1:
        user_id = list(potentials_in_channel)
        return user_id[0]

    logging.info(
        "Volunteer's name (%s) is ambiguous in Slack, so we aren't sending a message",
        first_name,
    )

    return None


def build_slack_message(message: list[dict]):
    """Build a slack message"""
    return {
        "blocks": [
            {
                "type": "rich_text",
                "elements": [{"type": "rich_text_section", "elements": message}],
            },
        ],
    }


class SlackOps:
    """
    Operations related to Slack. Get Slack user ID from full name. Send Slack messages.
    """

    def __init__(self, user_email, first_name, last_name):
        self.webhook_url = SLACK_WEBHOOK_URL
        self.token = SLACK_TOKEN
        self.on_duty_channel_id = SLACK_ON_DUTY_CHANNEL_ID
        self.user_email = user_email
        self.first_name = first_name
        self.last_name = last_name

    def get_slack_user_id(self):
        """
        Get Slack user ID by full name. If not found, try to lookup by Openpath email.
        If not found, return None. Allows mentioning user in Slack messages.
        """
        session = requests.Session()
        session.headers.update({"Authorization": f"Bearer {self.token}"})

        user_id = lookup_by_email(session, self.user_email)
        if user_id:
            return user_id

        user_id = lookup_by_name(
            session, self.first_name, self.last_name, self.on_duty_channel_id
        )

        return user_id

    def clock_in_slack_message(self, slack_id):
        """
        Send a message in the on-duty channel to indicate an ODV is starting their shift.
        """
        if slack_id is None:
            elements = [
                {
                    "type:": "text",
                    "text": self.first_name + " " + self.last_name,
                    "style": {"bold": True},
                },
                {
                    "type": "text",
                    "text": " is now on duty.",
                },
            ]

        else:
            elements = [
                {
                    "type": "user",
                    "user_id": slack_id,
                },
                {
                    "type": "text",
                    "text": " is now on duty.",
                },
            ]

        slack_event_payload = build_slack_message(elements)

        requests.post(
            self.webhook_url,
            json=slack_event_payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        return slack_event_payload

    def clock_out_slack_message(self, slack_id):
        """
        Send a message in the on-duty channel to indicate an ODV is ending their shift.
        """
        if slack_id is None:
            elements = [
                {
                    "type:": "text",
                    "text": self.first_name + " " + self.last_name,
                    "style": {"bold": True},
                },
                {
                    "type": "text",
                    "text": " is now off duty.",
                },
            ]
        else:
            elements = [
                {
                    "type": "user",
                    "user_id": slack_id,
                },
                {
                    "type": "text",
                    "text": " is now off duty.",
                },
            ]

        slack_event_payload = build_slack_message(elements)

        requests.post(
            self.webhook_url,
            json=slack_event_payload,
            headers={"Content-Type": "application/json"},
            timeout=10,
        )

        return slack_event_payload
