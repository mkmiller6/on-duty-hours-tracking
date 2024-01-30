"""
Lambda function that is triggered by Openpath events on the clock-in and clock-out buttons
attached to the Openpath cabinet at Asmbly.
"""

import logging
import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo
from dataclasses import dataclass

from googleapiclient.discovery import build

from helpers.openPathUtil import getUser
from helpers.google_drive import (
    batch_update_new_sheet,
    get_access_token,
    batch_update_copied_spreadsheet,
    SlideshowOperations
)

if os.environ.get('AWS_LAMBDA_FUNCTION_NAME') is not None:
    from credentials import (
        priv_sa,
        MASTER_LOG_SPREADSHEET_ID,
        TEMPLATE_SHEET_ID,
        PARENT_FOLDER_ID,
        INTERNAL_API_KEY,
        DRIVE_ID
    )
else:
    from config import (
        priv_sa,
        MASTER_LOG_SPREADSHEET_ID,
        TEMPLATE_SHEET_ID,
        PARENT_FOLDER_ID,
        INTERNAL_API_KEY,
        DRIVE_ID
    )

logging.getLogger().setLevel(logging.INFO)


# Define Google OAuth2 scopes needed.
# See https://developers.google.com/identity/protocols/oauth2/scopes
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
]


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

    def __post_init__(self):
        self.user_data = getUser(self.user_id)
        self.first_name = self.user_data.get("identity").get("firstName")
        self.last_name = self.user_data.get("identity").get("lastName")
        self.full_name = f"{self.first_name} {self.last_name}"


def handler(event, _):
    """
    Main Lambda Function handler. Triggered by Openpath unlock event on Clock-in and
    clock-out buttons.
    """

    logging.info("Received OP event: %s", event)

    try:
        op_event = json.loads(event.get("body"))
        logging.info("Parsed event: %s", op_event)
    except Exception as e:
        logging.error("Error parsing event: %s", e)
        raise

    if op_event.get("apiKey") != INTERNAL_API_KEY:
        logging.error("Invalid API key")
        return

    creds = get_access_token(priv_sa, SCOPES)

    # Create the API services using built credential tokens
    drive_service = build("drive", "v3", credentials=creds)
    sheets_service = build("sheets", "v4", credentials=creds)


    op_event = OpenpathEvent(
        op_event.get("entryId"), int(op_event.get("userId")), int(op_event.get("timestamp"))
    )

    op_user = OpenpathUser(op_event.user_id)

    slideshows_ops = SlideshowOperations(
        drive_service, op_user.full_name
    )

    # Check if On-Duty hours Google Sheet already exsists for this user.
    # If not, copy the template sheet.
    existing_sheet_check = (
        drive_service.files() # pylint: disable=maybe-no-member
        .list(
            q=f"""
                mimeType="application/vnd.google-apps.spreadsheet"
                and trashed=false and "{PARENT_FOLDER_ID}" in parents
                and name="ODV Timesheet - {op_user.full_name}"
            """,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            corpora="drive",
            driveId=DRIVE_ID,
        )
        .execute()
    )

    # Spreadsheet columns are: Date, Time In, Time Out, Hours (calculated)
    sheet = sheets_service.spreadsheets()  # pylint: disable=maybe-no-member

    if len(existing_sheet_check.get("files")) > 0:
        sheet_id = existing_sheet_check.get("files")[0].get("id")
    else:
        sheet_id = (
            drive_service.files() # pylint: disable=maybe-no-member
            .copy(
                fileId=TEMPLATE_SHEET_ID,
                body={
                    "name": f"ODV Timesheet - {op_user.full_name}",
                    "parents": [PARENT_FOLDER_ID],
                },
                supportsAllDrives=True,
            )
            .execute().get("id")
        )

        ind_sheet = sheet.get(
            spreadsheetId=sheet_id,
        ).execute().get("sheets")[0]

        ind_sheet_id = ind_sheet.get("properties").get("sheetId")
        protected_range_id = ind_sheet.get("protectedRanges")[0].get("protectedRangeId")

        sheet.values().append(
            spreadsheetId=sheet_id,
            range="Sheet1!F1:F2",
            body={"values": [[f"Name: {op_user.full_name}"], ["Notes/Comments"]]},
            valueInputOption="USER_ENTERED",
        ).execute()

        batch_update_copied_spreadsheet(sheet, sheet_id, ind_sheet_id, protected_range_id)


    # TODO: Change this entry name to Clock-in entry name when ready to deploy
    if op_event.entry == "Instructors Locker":
        # Append to user's log sheet
        sheet.values().append(
            spreadsheetId=sheet_id,
            range="Sheet1!A3:B",
            body={"values": [[op_event.date, op_event.time]]},
            valueInputOption="USER_ENTERED",
        ).execute()

        # Check if sheet already exists for this volunteer in the master log sheet.
        # If not, create it.
        odv_sheets = (
            sheet.get(spreadsheetId=MASTER_LOG_SPREADSHEET_ID).execute().get("sheets")
        )
        exists = False
        for odv_sheet in odv_sheets:
            if odv_sheet.get("properties").get("title") == f"{op_user.full_name}":
                exists = True
                break

        if not exists:
            new_sheet = sheet.batchUpdate(
                spreadsheetId=MASTER_LOG_SPREADSHEET_ID,
                body={
                    "requests": [
                        {"addSheet": {"properties": {"title": f"{op_user.full_name}"}}}
                    ]
                },
            ).execute()

            new_sheet_id = (
                new_sheet.get("replies")[0]
                .get("addSheet")
                .get("properties")
                .get("sheetId")
            )

            batch_update_new_sheet(
                sheet,
                MASTER_LOG_SPREADSHEET_ID,
                new_sheet_id,
                op_user.full_name
            )

        sheet.values().append(
            spreadsheetId=MASTER_LOG_SPREADSHEET_ID,
            range=f"'{op_user.full_name}'!A3:B",
            body={"values": [[op_event.date, op_event.time]]},
            valueInputOption="USER_ENTERED",
        ).execute()

        slideshows_ops.add_volunteer_to_slideshow()

    elif op_event.entry == "Clock Out":
        # Update the user's log sheet with the clock-out time
        rows = sheet.values().get(
            spreadsheetId=sheet_id,
            range="Sheet1!A1:B",
            majorDimension="ROWS",
            ).execute().get("values")
        last_row = len(rows)

        sheet.values().update(
            spreadsheetId=sheet_id,
            range=f"Sheet1!C{last_row if last_row > 2 else 3}:D{last_row if last_row > 2 else 3}",
            body={
                "values": [
                    [
                        op_event.time,
                        f"=C{last_row if last_row > 2 else 3}-B{last_row if last_row > 2 else 3}",
                    ]
                ]
            },
            valueInputOption="USER_ENTERED",
        ).execute()

        # Update the master sheet with the clock-out time
        rows = (
            sheet.values()
            .get(
                spreadsheetId=MASTER_LOG_SPREADSHEET_ID,
                range=f"'{op_user.full_name}'!A1:B",
                majorDimension="ROWS",
            )
            .execute().get("values")
        )
        last_row = len(rows)

        sheet.values().update(
            spreadsheetId=MASTER_LOG_SPREADSHEET_ID,
            range=f"'{op_user.full_name}'!C{last_row if last_row > 2 else 3}:D{last_row if last_row > 2 else 3}",
            body={
                "values": [
                    [
                        op_event.time,
                        f"=C{last_row if last_row > 2 else 3}-B{last_row if last_row > 2 else 3}",
                    ]
                ]
            },
            valueInputOption="USER_ENTERED",
        ).execute()

        slideshows_ops.remove_volunteer_from_slideshow()
