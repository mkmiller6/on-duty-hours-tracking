"""
Helper functions for interacting with Google Discovery APIs.
"""
import os
import logging

from google.auth import impersonated_credentials
from google.oauth2.service_account import Credentials
import google.auth.transport.requests
from googleapiclient.discovery import build

if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None:
    from credentials import key_file, priv_sa, DRIVE_ID
else:
    from config import key_file, priv_sa, DRIVE_ID

logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)

def batch_update_copied_spreadsheet(
    sheet, file_id, copied_sheet_id, protected_range_id
):
    """
    Batch update the copied spreadsheet. Updates protected range to allow Asmbly groups
    to edit, and formats the Hours column to Duration.
    """
    sheet.batchUpdate(
        spreadsheetId=file_id,
        body={
            "requests": [
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
                                "users": [
                                    "admin@asmbly.org",
                                    priv_sa
                                ],
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
                }
            ]
        }
    ).execute()


def batch_update_new_sheet(sheet, file_id, new_sheet_id, user_full_name):
    """
    Batch update the new sheet. Adds new sheet with volunteer's name and
    applies formatting.
    """
    sheet.batchUpdate(
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
                                            "stringValue": f"On-Duty Volunteer Timesheet - {user_full_name}"
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
                                        "userEnteredValue": {"stringValue": "Time In"},
                                        "userEnteredFormat": {
                                            "backgroundColor": {
                                                "red": 0.635,
                                                "green": 0.768,
                                                "blue": 0.788,
                                            }
                                        },
                                    },
                                    {
                                        "userEnteredValue": {"stringValue": "Time Out"},
                                        "userEnteredFormat": {
                                            "backgroundColor": {
                                                "red": 0.635,
                                                "green": 0.768,
                                                "blue": 0.788,
                                            }
                                        },
                                    },
                                    {
                                        "userEnteredValue": {"stringValue": "Hours"},
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
                                    priv_sa,
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
                }
            ]
        },
    ).execute()


def get_access_token(impersonated_account: str, scopes: list[str]):
    """
    Get access token for impersonated service account.
    """
    if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
        credentials = Credentials.from_service_account_info(key_file)
    else:
        credentials = Credentials.from_service_account_file(key_file)

    target_creds = impersonated_credentials.Credentials(
        source_credentials=credentials,
        target_principal=impersonated_account,
        target_scopes=scopes,
        lifetime=300,
    )

    request = google.auth.transport.requests.Request()
    target_creds.refresh(request)

    return target_creds

def get_folder_id(folder_name):
    """
    Get folder ID from folder name.
    """

    creds = get_access_token(priv_sa, ["https://www.googleapis.com/auth/drive.readonly"])

    drive_service = build("drive", "v3", credentials=creds)

    search = f"mimeType = 'application/vnd.google-apps.folder' and name = '{folder_name}'"
    fields = 'files(id, name, mimeType)'
    results = drive_service.files().list( # pylint: disable=maybe-no-member
            q=search,
            fields=fields,
            supportsAllDrives=True,
            driveId=DRIVE_ID,
            corpora="drive",
            includeItemsFromAllDrives=True).execute()

    items = results.get('files', [])

    if not items:
        return {}

    return items[0]
    #for item in items:
    #    print(u'{0} ({1})- {2}'.format(item['name'], item['id'],
    #    item['mimeType']))


class SlideshowOperations:
    """
    Class for Asmbly TV slideshow operations. Methods for adding and removing volunteers
    to the slideshow when they are actively on duty.
    """
    def __init__(self, drive_service, volunteer_name):
        self.drive_service = drive_service
        self.volunteer_name = volunteer_name
        self.slideshow_folder_id = get_folder_id("____LobbyTV").get("id")
        self.volunteer_slides_folder_id = get_folder_id("Volunteer Slides").get("id")

    def add_volunteer_to_slideshow(self):
        """
        Add volunteer to slideshow.
        """
        volunteer_slide = (
            self.drive_service.files()
            .list(
                q=f"""
                trashed=false and name="{self.volunteer_name}"
                and "{self.volunteer_slides_folder_id}" in parents
            """,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            corpora="drive",
            driveId=DRIVE_ID,
            )
            .execute()
        )

        if len(volunteer_slide.get("files")) > 0:
            self.drive_service.files().copy(
                fileId=volunteer_slide.get("files")[0].get("id"),
                body={
                    "name": self.volunteer_name,
                    "parents": [self.slideshow_folder_id],
                },
                supportsAllDrives=True,
            ).execute()
        else:
            logging.info("No slide for %s, consider adding them", self.volunteer_name)

    def remove_volunteer_from_slideshow(self):
        """
        Remove volunteer from slideshow.
        """

        volunteer_slide = self.drive_service.files().list(
            q=f"""
                trashed=false and name="{self.volunteer_name}"
                and "{self.slideshow_folder_id}" in parents
            """,
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            corpora="drive",
            driveId=DRIVE_ID,
        ).execute()

        if len(volunteer_slide.get("files")) > 0:
            slide_file_id = volunteer_slide.get("files")[0].get("id")

            self.drive_service.files().delete(
                fileId=slide_file_id
            ).execute()
