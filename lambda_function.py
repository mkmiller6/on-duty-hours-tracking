"""
Lambda function that is triggered by Openpath events on the clock-in and clock-out buttons
attached to the Openpath cabinet at Asmbly.
"""

import logging
import os
import json

from googleapiclient.discovery import build

from helpers.openpath_classes import OpenpathUser, OpenpathEvent
from helpers.slack import SlackOps
from helpers.google_services import (
    get_access_token,
    SheetsOperations,
    DriveOperations,
)

if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None:
    from credentials import (
        priv_sa,
        INTERNAL_API_KEY,
    )
else:
    from config import (
        priv_sa,
        INTERNAL_API_KEY,
    )

# Suppress disovery cache warnings
logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)

# AWS Lambda runtime has its own root logger. Set level to INFO
logging.getLogger().setLevel(logging.INFO)


# Define Google OAuth2 scopes needed.
# See https://developers.google.com/identity/protocols/oauth2/scopes
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]


def handler(event, _):
    """
    Main Lambda Function handler. Triggered by Openpath unlock event on Clock-in and
    clock-out buttons.
    """

    try:
        op_event = json.loads(event.get("body"))
        parsed_event = op_event.copy()
        del parsed_event["apiKey"]
        logging.info("Parsed event: %s", parsed_event)
    except Exception as e:
        logging.error("Error parsing event: %s", e)
        raise

    if op_event.get("apiKey") != INTERNAL_API_KEY:
        logging.error("Invalid API key")
        return {
            "statusCode": 400,
        }

    creds = get_access_token(priv_sa, SCOPES)

    # Create the API services using built credential tokens
    drive_service = build("drive", "v3", credentials=creds)
    sheets_service = build("sheets", "v4", credentials=creds)

    op_event = OpenpathEvent(
        op_event.get("entryId"),
        int(op_event.get("userId")),
        int(op_event.get("timestamp")),
    )

    op_user = OpenpathUser(op_event.user_id)

    drive_ops = DriveOperations(drive_service, op_user.full_name)

    slack_user = SlackOps(op_user.email, op_user.full_name)

    logging.info("Volunteer: %s", op_user.full_name)

    # Check if On-Duty hours Google Sheet already exsists for this user.
    # If not, copy the template sheet.
    existing_sheet_check = drive_ops.check_timesheet_exists()

    # Spreadsheet columns are: Date, Time In, Time Out, Hours (calculated)
    if len(existing_sheet_check) > 0:
        timesheet_id = existing_sheet_check[0].get("id")
        sheets_ops = SheetsOperations(sheets_service, op_user.full_name, timesheet_id)
    else:
        timesheet_id = drive_ops.create_timesheet()
        sheets_ops = SheetsOperations(sheets_service, op_user.full_name, timesheet_id)

        # Initialize the copied template with volunteer name,
        # range protection, duration format, etc.
        sheets_ops.initialize_copied_template()

    if op_event.entry == "OnDuty Check In":
        # Append clock-in time to user's log sheet
        sheets_ops.add_clock_in_entry_to_timesheet((op_event.date, op_event.time))

        # Check if sheet already exists for this volunteer in the master log sheet.
        exists = sheets_ops.check_master_log()

        # If not, create it.
        if not exists:
            sheets_ops.create_odv_sheet_in_master_spreadsheet()

        # Update the master sheet with the clock-in time
        sheets_ops.add_clock_in_entry_to_timesheet(
            (op_event.date, op_event.time), master=True
        )

        # Add volunteer to the TV slideshow if they have a corresponding slide
        drive_ops.add_volunteer_to_slideshow()

        # Lookup Slack user ID
        user_id = slack_user.get_slack_user_id()
        if user_id is None:
            logging.error("Slack user not found for: %s", op_user.full_name)

        # Send Slack message notifying the On-duty channel that the volunteer has clocked in.
        # If user_id is not None, the message will @mention the volunteer.
        # If user_id is None, the message will just contain the volunteer's bolded name.
        slack_user.clock_in_slack_message(user_id)

    elif op_event.entry == "OnDuty Check Out":
        # Update the user's log sheet with the clock-out time
        sheets_ops.add_clock_out_entry_to_timesheet(op_event.time)

        # Update the master sheet with the clock-out time
        sheets_ops.add_clock_out_entry_to_timesheet(op_event.time, master=True)

        # Remove volunteer from the TV slideshow if they have a corresponding slide
        drive_ops.remove_volunteer_from_slideshow()

        slack_user.clock_out_slack_message(slack_user.get_slack_user_id())

    return {"statusCode": 200}
