import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from googleapiclient.discovery import build

from helpers.openPathUtil import getUser
from helpers.googleDrive import batch_update_new_sheet, get_access_token
from config import priv_sa, MASTER_LOG_SPREADSHEET_ID, TEMPLATE_SHEET_ID, PARENT_FOLDER_ID


#Define Google OAuth2 scopes needed. See https://developers.google.com/identity/protocols/oauth2/scopes
SCOPES = ['https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/spreadsheets']


def handler(event, context):
    logging.info("Received OP event: %s", event)

    creds = get_access_token(priv_sa, SCOPES)

    #Create the API services using built credential tokens
    driveService = build('drive', 'v3', credentials=creds)
    sheetsService = build('sheets', 'v4', credentials=creds)

    op_event = json.loads(event.get('body'))
    op_entry = op_event.get('entryId')
    op_id = op_event['userId']
    timestamp = op_event['timestamp']

    op_user = getUser(op_id)

    user_first_name = op_user.get('data').get('identity').get('firstName')
    user_last_name = op_user.get('data').get('identity').get('lastName')

    # Check if On-Duty hours Google Sheet already exsists for this user. If not, copy the template sheet.
    existing_sheet_check = driveService.files().list(q=f"mimeType='application/vnd.google-apps.spreadsheet' and trashed=false and '{PARENT_FOLDER_ID}' in parents and name='ODV Timesheet - {user_first_name} {user_last_name}'",
                                    includeItemsFromAllDrives=True,
                                    supportsAllDrives=True,
                                    corpora='drive',
                                    driveId='0ADuGDgrEXJMJUk9PVA'
                                    ).execute()


    if len(existing_sheet_check.get('files')) > 0:
        sheet_id = existing_sheet_check.get('files')[0].get('id')
    else:
        spreadsheet = driveService.files().copy(
            fileId=TEMPLATE_SHEET_ID, 
            body=
            {
                'name': f'ODV Timesheet - {user_first_name} {user_last_name}',
                'parents': [PARENT_FOLDER_ID]
            },
            supportsAllDrives=True).execute()
        sheet_id = spreadsheet.get('id')
    
    # Format the timestamp and add to the user's log sheet
    timestamp_datetime = datetime.fromtimestamp(timestamp, tz=ZoneInfo("America/Chicago"))
    date = timestamp_datetime.strftime("%m/%d/%Y")
    time = timestamp_datetime.strftime("%I:%M %p")
    
    # Spreadsheet columns are: Date, Time In, Time Out, Hours (calculated)
    sheet = sheetsService.spreadsheets()

    #TODO: Change this entry name to Clock-in entry name when ready to deploy
    if op_entry == "Instructors Locker":
        # Append to user's log sheet
        sheet.values().append(
            spreadsheetId=sheet_id, 
            range='Sheet1!A3:B',
            body={'values': [[date, time]]}, 
            valueInputOption='USER_ENTERED').execute()
        
        # Check if sheet already exists for this volunteer in the master log sheet. If not, create it.
        odv_sheets = sheet.get(spreadsheetId=MASTER_LOG_SPREADSHEET_ID).execute().get('sheets')
        exists = False
        for sheet in odv_sheets:
            if sheet.get('properties').get('title') == f"{user_first_name} {user_last_name}":
                exists = True
                break

        if not exists:
            new_sheet = sheet.batchUpdate(
                spreadsheetId=MASTER_LOG_SPREADSHEET_ID,
                body={
                    'requests': [
                        {
                            'addSheet': {
                                'properties': {
                                    'title': f"{user_first_name} {user_last_name}"
                                }
                            }
                        }
                    ]
                }
            ).execute()

            new_sheet_id = new_sheet.get('replies')[0].get('addSheet').get('properties').get('sheetId')

            batch_update_new_sheet(sheet, MASTER_LOG_SPREADSHEET_ID, new_sheet_id, user_first_name, user_last_name)

        sheet.values().append(
            spreadsheetId=MASTER_LOG_SPREADSHEET_ID, 
            range=f"'{user_first_name} {user_last_name}'!A3:B",
            body={'values': [[date, time]]}, 
            valueInputOption='USER_ENTERED').execute()
        
        #TODO: Add active On-Duty slide for this volunteer to the TV slideshow Drive folder

    elif op_entry == "Clock Out":
        # Update the user's log sheet with the clock-out time
        rows = sheet.values().get(spreadsheetId=sheet_id, range='Sheet1!A1:B').execute()
        last_row = len(rows)

        sheet.values().update(
            spreadsheetId=sheet_id, 
            range=f'Sheet1!C{last_row if last_row > 2 else 3}:D{last_row if last_row > 2 else 3}',
            body={'values': [[time, f"=C{last_row if last_row > 2 else 3}-B{last_row if last_row > 2 else 3}"]]}, 
            valueInputOption='USER_ENTERED').execute()
        
        # Update the master sheet with the clock-out time
        rows = sheet.values().get(spreadsheetId=MASTER_LOG_SPREADSHEET_ID, range=f"'{user_first_name} {user_last_name}'!A1:B").execute()
        last_row = len(rows)

        sheet.values().update(
            spreadsheetId=MASTER_LOG_SPREADSHEET_ID, 
            range=f"'{user_first_name} {user_last_name}'!C{last_row if last_row > 2 else 3}:D{last_row if last_row > 2 else 3}",
            body={'values': [[time, f"=C{last_row if last_row > 2 else 3}-B{last_row if last_row > 2 else 3}"]]}, 
            valueInputOption='USER_ENTERED').execute()

        #TODO: Remove active On-Duty slide for this volunteer from the TV slideshow Drive folder
