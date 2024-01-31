"""
Helpers for Slack.
"""

import os
import logging
import requests

if os.environ.get('AWS_LAMBDA_FUNCTION_NAME') is not None:
    from credentials import (
        SLACK_WEBHOOK_URL,
        SLACK_TOKEN
    )
else:
    from config import (
        SLACK_WEBHOOK_URL,
        SLACK_TOKEN
    )

class SlackOps:
    """
    Operations related to Slack. Get Slack user ID from full name. Send Slack messages.
    """
    def __init__(self, user_email, full_name):
        self.webhook_url = SLACK_WEBHOOK_URL
        self.user_email = user_email
        self.full_name = full_name

    def get_slack_user_id(self):
        """
        Get Slack user ID by full name. If not found, try to lookup by Openpath email.
        If not found, return None. Allows mentioning user in Slack messages.
        """
        url = "https://slack.com/api/users.list"
        params = {"limit": 300}
        response = requests.get(
            url,
            params=params,
            headers={"Authorization": "Bearer " + SLACK_TOKEN},
            timeout=10
            )

        if response.status_code != 200:
            logging.error("Get %s returned status code %s", url, response.status_code)
            return None

        response = response.json()

        if response.get("ok") is False:
            logging.error("Get %s returned error: %s", url, response.get("error"))
            return None


        user = filter(
            lambda user: user.get("profile").get("real_name") == self.full_name,
            response["members"]
        )

        found_user = list(user)

        if len(found_user) > 0:
            return found_user[0].get("id")

        url = "https://slack.com/api/users.lookupByEmail"
        params = {"email": self.user_email}
        response = requests.get(
            url,
            params=params,
            headers={"Authorization": "Bearer " + SLACK_TOKEN},
            timeout=10
            )

        if response.status_code != 200:
            logging.error("Get %s returned status code %s", url, response.status_code)
            return None

        response = response.json()

        if response.get("ok") is False:
            return None

        return response.get("user").get("id")


    def clock_in_slack_message(self, slack_id):
        """
        Send a message in the on-duty channel to indicate an ODV is starting their shift.
        """
        if slack_id is None:
            slack_event_payload = {
                "blocks": [
                    {
                        "type": "rich_text",
                        "elements": [
                            {
                                "type": "rich_text_section",
                                "elements": [
                                    {
                                        "type:": "text",
                                        "text": f"{self.full_name}",
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
        else:
            slack_event_payload = {
                "blocks": [
                    {
                        "type": "rich_text",
                        "elements": [
                            {
                                "type": "rich_text_section",
                                "elements": [
                                    {
                                        "type": "user",
                                        "user_id": slack_id,
                                    },
                                    {
                                        "type": "text",
                                        "text": " is now on duty.",
                                    }
                                ]
                            },
                        ]
                    },
                ]
            }

        requests.post(SLACK_WEBHOOK_URL,
                      json=slack_event_payload,
                      headers={"Content-Type": "application/json"},
                      timeout=10
                      )

        return slack_event_payload

    def clock_out_slack_message(self, slack_id):
        """
        Send a message in the on-duty channel to indicate an ODV is ending their shift.
        """
        if slack_id is None:
            slack_event_payload = {
                "blocks": [
                    {
                        "type": "rich_text",
                        "elements": [
                            {
                                "type": "rich_text_section",
                                "elements": [
                                    {
                                        "type:": "text",
                                        "text": f"{self.full_name}",
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
        else:
            slack_event_payload = {
                "blocks": [
                    {
                        "type": "rich_text",
                        "elements": [
                            {
                                "type": "rich_text_section",
                                "elements": [
                                    {
                                        "type": "user",
                                        "user_id": slack_id,
                                    },
                                    {
                                        "type": "text",
                                        "text": " is now off duty.",
                                    }
                                ]
                            },
                        ]
                    },
                ]
            }

        requests.post(SLACK_WEBHOOK_URL,
                      json=slack_event_payload,
                      headers={"Content-Type": "application/json"},
                      timeout=10
                      )

        return slack_event_payload
    