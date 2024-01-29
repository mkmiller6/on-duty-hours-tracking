from google.auth import impersonated_credentials
from google.oauth2.service_account import Credentials
import google.auth.transport.requests

from config import key_file


#File containing private key for the service account used to implement automation
#Edit service account in Google Cloud Console 
#This script requires domain-wide delegation to run. See https://support.google.com/a/answer/162106?hl=en
SERVICE_ACCOUNT_FILE = key_file

def batch_update_new_sheet(sheet, file_id, new_sheet_id, user_first_name, user_last_name):
    sheet.batchUpdate(
                spreadsheetId=file_id,
                body={
                    'requests': [
                        {
                            'mergeCells': {
                                'range': {
                                    'sheetId': new_sheet_id,
                                    'startRowIndex': 0,
                                    'endRowIndex': 1,
                                    'startColumnIndex': 0,
                                    'endColumnIndex': 2
                                },
                                'mergeType': 'MERGE_ALL'
                            }
                        },
                        {
                            'updateCells': {
                                'rows': [
                                    {
                                        'values': [
                                            {
                                                'userEnteredValue': {
                                                    'stringValue': f"On-Duty Volunteer Timesheet for {user_first_name} {user_last_name}"
                                                },
                                                'userEnteredFormat': {
                                                    'textFormat': {
                                                        'bold': True
                                                    },
                                                    'horizontalAlignment': 'CENTER',
                                                    'verticalAlignment': 'MIDDLE',
                                                    'backgroundColor': {
                                                        'red': 0.635,
                                                        'green': 0.768,
                                                        'blue': 0.788
                                                    }
                                                }
                                            }
                                        ]
                                    },
                                    {
                                        'values': [
                                            {
                                                'userEnteredValue': {
                                                    'stringValue': "Date"
                                                },
                                                'userEnteredFormat': {
                                                    'backgroundColor': {
                                                        'red': 0.635,
                                                        'green': 0.768,
                                                        'blue': 0.788
                                                    }
                                                }
                                            },
                                            {
                                                'userEnteredValue': {
                                                    'stringValue': "Time In"
                                                },
                                                'userEnteredFormat': {
                                                    'backgroundColor': {
                                                        'red': 0.635,
                                                        'green': 0.768,
                                                        'blue': 0.788
                                                    }
                                                }
                                            },
                                            {
                                                'userEnteredValue': {
                                                    'stringValue': "Time Out"
                                                },
                                                'userEnteredFormat': {
                                                    'backgroundColor': {
                                                        'red': 0.635,
                                                        'green': 0.768,
                                                        'blue': 0.788
                                                    }
                                                }
                                            },
                                            {
                                                'userEnteredValue': {
                                                    'stringValue': "Hours"
                                                },
                                                'userEnteredFormat': {
                                                    'backgroundColor': {
                                                        'red': 0.635,
                                                        'green': 0.768,
                                                        'blue': 0.788
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                ],
                                'fields': ['userEnteredValue', 'userEnteredFormat'],
                                'start': {
                                    'sheetId': new_sheet_id,
                                    'rowIndex': 0,
                                    'columnIndex': 0
                                }
                            }
                        },
                        {
                            'updateDimensionProperties': {
                                'range': {
                                    'sheetId': new_sheet_id,
                                    'dimension': 'ROWS',
                                    'startIndex': 0,
                                    'endIndex': 1
                                },
                                'properties': {
                                    'pixelSize': 48
                                },
                                'fields': 'pixelSize'
                            }
                        },
                        {
                            'addProtectedRange': {
                                'protectedRange': {
                                    'range': {
                                        'sheetId': new_sheet_id,
                                        'startColumnIndex': 0,
                                        'endColumnIndex': 4
                                    },
                                    'description': 'On-Duty Hours',
                                    'warningOnly': False,
                                    'editors': {
                                        'users': [
                                            'admin@asmbly.org'
                                        ],
                                        'groups': [
                                            'membership@asmbly.org',
                                            'leadership@asmbly.org',
                                            'classes@asmbly.org'
                                        ]
                                    }
                                }
                            }
                        }
                    ]
                }).execute()
    

def get_access_token(impersonated_account: str, scopes: list[str]):
    credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)

    target_creds = impersonated_credentials.Credentials(
        source_credentials=credentials,
        target_principal=impersonated_account,
        target_scopes=scopes,
        lifetime=300
    )

    request = google.auth.transport.requests.Request()
    target_creds.refresh(request)

    return target_creds.token