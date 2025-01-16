"""
Helper functions for interacting with Google Discovery APIs.
"""

import os
import logging
import datetime
import re

from google.auth.impersonated_credentials import Credentials as ImpersonatedCredentials
from google.oauth2.service_account import Credentials
import google.auth.transport.requests

if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None:
    from credentials import (
        key_file,
        PRIV_SA,
        ON_DUTY_DRIVE_ID,
        MAIN_DRIVE_ID,
        MASTER_LOG_SPREADSHEET_ID,
        TEMPLATE_SHEET_ID,
        PARENT_FOLDER_ID,
    )
else:
    from config import (
        key_file,
        PRIV_SA,
        ON_DUTY_DRIVE_ID,
        MAIN_DRIVE_ID,
        MASTER_LOG_SPREADSHEET_ID,
        TEMPLATE_SHEET_ID,
        PARENT_FOLDER_ID,
    )

logging.getLogger("googleapiclient.discovery_cache").setLevel(logging.ERROR)


def get_access_token(impersonated_account: str, scopes: list[str]):
    """
    Get access token for impersonated service account.
    """
    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        credentials = Credentials.from_service_account_info(key_file)
    else:
        credentials = Credentials.from_service_account_file(key_file)

    target_creds = ImpersonatedCredentials(
        source_credentials=credentials,
        target_principal=impersonated_account,
        target_scopes=scopes,
        lifetime=300,
    )

    request = google.auth.transport.requests.Request()
    target_creds.refresh(request)

    return target_creds


class DriveOperations:
    """
    Class for Google Drive operations. Methods for creating, searching,
    and copying files
    """

    def __init__(self, drive_service, volunteer_name):
        self.drive_service = drive_service
        self.volunteer_name = volunteer_name
        self.on_duty_drive_id = ON_DUTY_DRIVE_ID
        self.main_drive_id = MAIN_DRIVE_ID
        self.template_sheet_id = TEMPLATE_SHEET_ID
        self.parent_folder_id = PARENT_FOLDER_ID
        self.slideshow_folder_id = self.get_folder_id(MAIN_DRIVE_ID, "____LobbyTV").get(
            "id"
        )
        self.volunteer_slides_folder_id = self.get_folder_id(
            ON_DUTY_DRIVE_ID, "Volunteer Slides"
        ).get("id")

    def add_volunteer_to_slideshow(self):
        """
        Add volunteer to slideshow.
        """
        if self.volunteer_slides_folder_id is None:
            logging.error("Folder 'Volunteer Slides' not found")
            return

        volunteer_slide = self.slide_search(
            self.on_duty_drive_id, self.volunteer_name, self.volunteer_slides_folder_id
        )

        if len(volunteer_slide.get("files")) > 0:
            slide_file_id = volunteer_slide.get("files")[0].get("id")

            self.add_slide(slide_file_id)
        else:
            logging.info("No slide for %s, consider adding them", self.volunteer_name)

    def remove_volunteer_from_slideshow(self):
        """
        Remove volunteer from slideshow.
        """
        if self.slideshow_folder_id is None:
            logging.error("Folder '____LobbyTV' not found")
            return

        volunteer_slide = self.slide_search(
            self.main_drive_id, self.volunteer_name, self.slideshow_folder_id
        )

        if len(volunteer_slide.get("files")) > 0:
            slide_file_id = volunteer_slide.get("files")[0].get("id")

            self.trash_slide(slide_file_id)

    def slide_search(self, drive_id: str, volunteer_name: str, folder_id: str):
        """
        Search for a file.
        """
        return (
            self.drive_service.files()
            .list(
                q=f"""
                trashed=false and name="ODV - {volunteer_name}.png"
                and "{folder_id}" in parents
            """,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                corpora="drive",
                driveId=drive_id,
            )
            .execute()
        )

    def add_slide(self, slide_file_id: str):
        """
        Add slide to slideshow.
        """
        self.drive_service.files().copy(
            fileId=slide_file_id,
            body={
                "name": self.volunteer_name,
                "parents": [self.slideshow_folder_id],
            },
            supportsAllDrives=True,
        ).execute()

    def trash_slide(self, slide_file_id: str):
        """
        Trash slide.
        """
        self.drive_service.files().update(
            fileId=slide_file_id,
            body={"trashed": True},
            supportsAllDrives=True,
        ).execute()

    def asmbly_drive_file_search(self, drive_id, search_query):
        """
        Search Asmbly shared drive for files.
        """

        fields = "files(id, name, mimeType)"
        results = (
            self.drive_service.files()
            .list(  # pylint: disable=maybe-no-member
                q=search_query,
                fields=fields,
                supportsAllDrives=True,
                driveId=drive_id,
                corpora="drive",
                includeItemsFromAllDrives=True,
            )
            .execute()
        )

        return results

    def get_folder_id(self, drive_id, folder_name):
        """
        Get folder ID from folder name.
        """

        search = f"mimeType = 'application/vnd.google-apps.folder' and name = '{folder_name}'"

        items = self.asmbly_drive_file_search(drive_id, search).get("files", [])

        if len(items) == 0:
            return {}

        if len(items) > 1:
            logging.error("More than one folder found with name '%s'", folder_name)

        return items[0]

    def check_timesheet_exists(self):
        """
        Check if volunteer's timesheet already exists in the shared Drive.
        """
        search_query = (
            f'mimeType="application/vnd.google-apps.spreadsheet"'
            f' and "{self.parent_folder_id}" in parents'
            f' and name="ODV Timesheet - {self.volunteer_name}"'
            f" and trashed=false"
        )

        result = self.asmbly_drive_file_search(self.on_duty_drive_id, search_query)

        return result.get("files", [])

    def create_timesheet(self):
        """
        Create a new timesheet for the volunteer.
        """
        return (
            self.drive_service.files()
            .copy(
                fileId=self.template_sheet_id,
                body={
                    "name": f"ODV Timesheet - {self.volunteer_name}",
                    "parents": [self.parent_folder_id],
                },
                supportsAllDrives=True,
            )
            .execute()
            .get("id")
        )


class SheetsOperations:
    """
    Class for Google Sheets operations related to a specific volunteer.
    Methods for logging clock-in and clock-out times to the volunteer's
    individual ODV Log Sheet as well as the Master Log.
    """

    def __init__(self, sheets_service, volunteer_name, volunteer_timesheet_id):
        self.sheets_service = sheets_service
        self.volunteer_name = volunteer_name
        self.master_sheet_id = MASTER_LOG_SPREADSHEET_ID
        self.volunteer_timesheet_id = volunteer_timesheet_id
        self.sheet = sheets_service.spreadsheets()

    def initialize_copied_template(self):
        """
        Initialize copied template timesheet with formatting,
        names, range protection, etc.
        """
        ind_sheet = (
            self.sheet.get(spreadsheetId=self.volunteer_timesheet_id)
            .execute()
            .get("sheets")[0]
        )

        sheet_id = ind_sheet.get("properties").get("sheetId")
        protected_range_id = ind_sheet.get("protectedRanges")
        if protected_range_id:
            protected_range_id = protected_range_id[0].get("protectedRangeId")

        name_field = f"Name: {self.volunteer_name}"
        self.sheet.values().append(
            spreadsheetId=self.volunteer_timesheet_id,
            range="Sheet1!F1:F2",
            body={"values": [[name_field], ["Notes/Comments"]]},
            valueInputOption="USER_ENTERED",
        ).execute()

        self.batch_update_copied_spreadsheet(
            self.volunteer_timesheet_id,
            sheet_id,
            protected_range_id,
        )

    def get_last_entry_datetime(
        self, clock_in: bool = True
    ) -> datetime.datetime | None:
        """Get the datetime of the last clock-in or clock-out entry in the spreadsheet"""

        date_index = 0
        time_index = 1 if clock_in else 2

        log_entries = (
            self.sheet.values()
            .get(
                spreadsheetId=self.volunteer_timesheet_id,
                range="Sheet1!A3:C",  # Columns are A: Date, B: Clock-in time, C: Clock-out time
                majorDimension="ROWS",
                dateTimeRenderOption="FORMATTED_STRING",
            )
            .execute()
            .get("values")
        )

        if not log_entries or len(log_entries) == 0:
            return None

        date_part = log_entries[-1][date_index]
        if not date_part:
            date_part = datetime.datetime.now().strftime("%m/%d/%Y")
        elif re.match(r"\d{1,2}/\d{1,2}/\d{4}", date_part) is None:
            return None

        time_part = log_entries[-1]
        if len(time_part) < time_index + 1:
            time_part = (
                datetime.datetime.now() - datetime.timedelta(hours=1)
            ).strftime("%I:%M %p")
        else:
            time_part = time_part[time_index]

        return datetime.datetime.strptime(
            f"{date_part} {time_part}", "%m/%d/%Y %I:%M %p"
        )

    def add_clock_in_entry_to_timesheet(self, log_entry: tuple, master=False):
        """
        Add clock-in entry to individual timesheet or master log.
        """
        self.sheet.values().append(
            spreadsheetId=(
                self.master_sheet_id if master else self.volunteer_timesheet_id
            ),
            range=f"'{self.volunteer_name}'!A3:B" if master else "Sheet1!A3:B",
            body={"values": [[log_entry[0], log_entry[1]]]},
            valueInputOption="USER_ENTERED",
        ).execute()

    def add_clock_out_entry_to_timesheet(self, log_entry: str, master=False):
        """
        Add clock-out entry to individual timesheet or master log.
        """

        def get_currents_rows():
            return (
                self.sheet.values()
                .get(
                    spreadsheetId=(
                        self.master_sheet_id if master else self.volunteer_timesheet_id
                    ),
                    range=f"'{self.volunteer_name}'!A1:B" if master else "Sheet1!A1:B",
                    majorDimension="ROWS",
                )
                .execute()
                .get("values")
            )

        current_rows = get_currents_rows()

        last_row = len(current_rows)

        current_row = last_row if last_row > 2 else 3

        if master:
            self.sheet.values().update(
                spreadsheetId=self.master_sheet_id,
                range=(f"'{self.volunteer_name}'!C{current_row}" f":D{current_row}"),
                body={
                    "values": [
                        [
                            log_entry,
                            (
                                f"=IF(C{current_row}-B{current_row}>0, C{current_row}-B{current_row}, 1 + (C{current_row}-B{current_row}))"
                            ),
                        ]
                    ]
                },
                valueInputOption="USER_ENTERED",
            ).execute()

            return

        self.sheet.values().update(
            spreadsheetId=self.volunteer_timesheet_id,
            range=f"Sheet1!C{current_row}:D{current_row}",
            body={
                "values": [
                    [
                        log_entry,
                        f"=IF(C{current_row}-B{current_row}>0, C{current_row}-B{current_row}, 1 + (C{current_row}-B{current_row}))",
                    ]
                ]
            },
            valueInputOption="USER_ENTERED",
        ).execute()

    def get_all_sheets(self):
        """
        Get all sheets in the Master Log.
        """
        return (
            self.sheet.get(spreadsheetId=self.master_sheet_id).execute().get("sheets")
        )

    def check_master_log(self):
        """
        Check if a sheet already exsists in the Master Log for this volunteer.
        """

        all_sheets = self.get_all_sheets()

        for sheet in all_sheets:
            if sheet.get("properties").get("title") == self.volunteer_name:
                return True

        return False

    def create_odv_sheet_in_master_spreadsheet(self):
        """
        Create a new sheet in the Master Log for this volunteer.
        """
        new_sheet_id = (
            self.sheet.batchUpdate(
                spreadsheetId=self.master_sheet_id,
                body={
                    "requests": [
                        {"addSheet": {"properties": {"title": self.volunteer_name}}}
                    ]
                },
            )
            .execute()
            .get("replies")[0]
            .get("addSheet")
            .get("properties")
            .get("sheetId")
        )

        self.batch_update_new_master_sheet(
            self.master_sheet_id,
            new_sheet_id,
            self.volunteer_name,
        )

    def batch_update_copied_spreadsheet(
        self, file_id, copied_sheet_id, protected_range_id
    ):
        """
        Batch update the copied spreadsheet. Updates protected range to allow Asmbly groups
        to edit, and formats the Hours column to Duration.
        """
        body = {
            "requests": [
                {
                    "updateCells": {
                        "rows": [
                            {
                                "values": [
                                    {
                                        "userEnteredFormat": {
                                            "numberFormat": {
                                                "type": "DATE_TIME",
                                                "pattern": "[h]:mm:ss",
                                            }
                                        },
                                    },
                                ]
                            }
                        ],
                        "fields": "userEnteredFormat.numberFormat",
                        "range": {
                            "sheetId": copied_sheet_id,
                            "startRowIndex": 2,
                            "startColumnIndex": 3,
                            "endColumnIndex": 4,
                        },
                    },
                },
            ]
        }

        if protected_range_id:
            body["requests"].append(
                {
                    "updateProtectedRange": {
                        "protectedRange": {
                            "protectedRangeId": protected_range_id,
                            "range": {
                                "sheetId": copied_sheet_id,
                                "startColumnIndex": 0,
                                "endColumnIndex": 4,
                            },
                            "description": "On-Duty Hours",
                            "warningOnly": False,
                            "editors": {
                                "users": ["admin@asmbly.org", PRIV_SA],
                                "groups": [
                                    "membership@asmbly.org",
                                    "leadership@asmbly.org",
                                    "classes@asmbly.org",
                                ],
                            },
                        },
                        "fields": "*",
                    }
                },
            )

        self.sheet.batchUpdate(spreadsheetId=file_id, body=body).execute()

    def batch_update_new_master_sheet(self, file_id, new_sheet_id, user_full_name):
        """
        Batch update the new sheet. Adds new sheet with volunteer's name and
        applies formatting.
        """
        self.sheet.batchUpdate(
            spreadsheetId=file_id,
            body={
                "requests": [
                    {
                        "mergeCells": {
                            "range": {
                                "sheetId": new_sheet_id,
                                "startRowIndex": 0,
                                "endRowIndex": 1,
                                "startColumnIndex": 0,
                                "endColumnIndex": 4,
                            },
                            "mergeType": "MERGE_ALL",
                        }
                    },
                    {
                        "updateCells": {
                            "rows": [
                                {
                                    "values": [
                                        {
                                            "userEnteredValue": {
                                                "stringValue": (
                                                    f"On-Duty Volunteer Timesheet - "
                                                    f"{user_full_name}"
                                                )
                                            },
                                            "userEnteredFormat": {
                                                "textFormat": {"bold": True},
                                                "horizontalAlignment": "CENTER",
                                                "verticalAlignment": "MIDDLE",
                                                "backgroundColor": {
                                                    "red": 0.635,
                                                    "green": 0.768,
                                                    "blue": 0.788,
                                                },
                                            },
                                        }
                                    ]
                                },
                                {
                                    "values": [
                                        {
                                            "userEnteredValue": {"stringValue": "Date"},
                                            "userEnteredFormat": {
                                                "backgroundColor": {
                                                    "red": 0.635,
                                                    "green": 0.768,
                                                    "blue": 0.788,
                                                }
                                            },
                                        },
                                        {
                                            "userEnteredValue": {
                                                "stringValue": "Time In"
                                            },
                                            "userEnteredFormat": {
                                                "backgroundColor": {
                                                    "red": 0.635,
                                                    "green": 0.768,
                                                    "blue": 0.788,
                                                }
                                            },
                                        },
                                        {
                                            "userEnteredValue": {
                                                "stringValue": "Time Out"
                                            },
                                            "userEnteredFormat": {
                                                "backgroundColor": {
                                                    "red": 0.635,
                                                    "green": 0.768,
                                                    "blue": 0.788,
                                                }
                                            },
                                        },
                                        {
                                            "userEnteredValue": {
                                                "stringValue": "Hours"
                                            },
                                            "userEnteredFormat": {
                                                "backgroundColor": {
                                                    "red": 0.635,
                                                    "green": 0.768,
                                                    "blue": 0.788,
                                                }
                                            },
                                        },
                                    ]
                                },
                            ],
                            "fields": "*",
                            "start": {
                                "sheetId": new_sheet_id,
                                "rowIndex": 0,
                                "columnIndex": 0,
                            },
                        }
                    },
                    {
                        "updateDimensionProperties": {
                            "range": {
                                "sheetId": new_sheet_id,
                                "dimension": "ROWS",
                                "startIndex": 0,
                                "endIndex": 1,
                            },
                            "properties": {"pixelSize": 48},
                            "fields": "pixelSize",
                        }
                    },
                    {
                        "updateDimensionProperties": {
                            "range": {
                                "sheetId": new_sheet_id,
                                "dimension": "COLUMNS",
                                "startIndex": 4,
                                "endIndex": 5,
                            },
                            "properties": {"pixelSize": 15},
                            "fields": "pixelSize",
                        }
                    },
                    {
                        "addProtectedRange": {
                            "protectedRange": {
                                "range": {
                                    "sheetId": new_sheet_id,
                                    "startColumnIndex": 0,
                                    "endColumnIndex": 4,
                                },
                                "description": "On-Duty Hours",
                                "warningOnly": False,
                                "editors": {
                                    "users": [
                                        "admin@asmbly.org",
                                        PRIV_SA,
                                    ],
                                    "groups": [
                                        "membership@asmbly.org",
                                        "leadership@asmbly.org",
                                        "classes@asmbly.org",
                                    ],
                                },
                            }
                        }
                    },
                    {
                        "updateSheetProperties": {
                            "properties": {
                                "sheetId": new_sheet_id,
                                "gridProperties": {"frozenRowCount": 2},
                            },
                            "fields": "gridProperties.frozenRowCount",
                        }
                    },
                    {
                        "updateCells": {
                            "rows": [
                                {
                                    "values": [
                                        {
                                            "userEnteredFormat": {
                                                "numberFormat": {
                                                    "type": "DATE_TIME",
                                                    "pattern": "[h]:mm:ss",
                                                }
                                            },
                                        },
                                    ]
                                }
                            ],
                            "fields": "userEnteredFormat.numberFormat",
                            "range": {
                                "sheetId": new_sheet_id,
                                "startRowIndex": 2,
                                "startColumnIndex": 3,
                                "endColumnIndex": 4,
                            },
                        },
                    },
                ]
            },
        ).execute()
