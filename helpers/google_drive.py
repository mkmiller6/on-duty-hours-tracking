"""
Helper functions for interacting with Google Discovery APIs.
"""

from google.auth import impersonated_credentials
from google.oauth2.service_account import Credentials
import google.auth.transport.requests

from config import key_file, priv_sa

# File path containing private key for the service account used to implement automation
SERVICE_ACCOUNT_FILE = key_file


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
                                            "stringValue": f"""On-Duty Volunteer Timesheet
                                                            - {user_full_name}
                                                            """
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
                        "fields": ["userEnteredValue", "userEnteredFormat"],
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
            ]
        },
    ).execute()


def get_access_token(impersonated_account: str, scopes: list[str]):
    """
    Get access token for impersonated service account.
    """
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)

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
    from googleapiclient.discovery import build

    creds = get_access_token(priv_sa, ["https://www.googleapis.com/auth/drive.readonly"])

    drive_service = build("drive", "v3", credentials=creds)

    search = f"mimeType = 'application/vnd.google-apps.folder' and name = '{folder_name}'"
    fields = 'files(id, name, mimeType)'
    results = drive_service.files().list( # pylint: disable=maybe-no-member
            q=search,
            fields=fields,
            supportsAllDrives=True).execute()

    items = results.get('files', [])
    for item in items:
        print(u'{0} ({1})- {2}'.format(item['name'], item['id'],
        item['mimeType']))
