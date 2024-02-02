# pylint: disable=missing-docstring, redefined-outer-name, no-member

import pytest
from pytest_mock import MockerFixture

from helpers.google_services import DriveOperations

from config import DRIVE_ID, PARENT_FOLDER_ID, TEMPLATE_SHEET_ID


class TestDriveOperations:
    @pytest.fixture
    def mock_folders(self, mocker: MockerFixture):
        mocker.Mock().side_effect = [
            {
                "id": "123",
                "name": "____LobbyTV",
                "mimeType": "application/vnd.google-apps.folder",
            },
            {
                "id": "456",
                "name": "Volunteer Slides",
                "mimeType": "application/vnd.google-apps.folder",
            },
        ]

    def test_init(self, mock_folders, mocker: MockerFixture):
        mocker.patch(
            "helpers.google_services.DriveOperations.asmbly_drive_file_search"
        ).side_effect = mock_folders

        mock_instance = DriveOperations(mocker.Mock(), "Test Volunteer Name")

        assert mock_instance.drive_id == DRIVE_ID
        assert mock_instance.parent_folder_id == PARENT_FOLDER_ID
        assert mock_instance.template_sheet_id == TEMPLATE_SHEET_ID
        assert mock_instance.volunteer_name == "Test Volunteer Name"

    def test_get_folder_id_with_file(self, mocker: MockerFixture):
        mocker.patch(
            "helpers.google_services.DriveOperations.asmbly_drive_file_search"
        ).return_value = {
            "files": [
                {
                    "id": "123",
                    "name": "On Duty Timesheets",
                    "mimeType": "application/vnd.google-apps.folder",
                }
            ]
        }

        mock_drive_instance = DriveOperations(mocker.Mock(), "Test Volunteer Name")

        assert mock_drive_instance.get_folder_id("On Duty Timesheets") == {
            "id": "123",
            "name": "On Duty Timesheets",
            "mimeType": "application/vnd.google-apps.folder",
        }

        mock_drive_instance.asmbly_drive_file_search.assert_called_with(
            "mimeType = 'application/vnd.google-apps.folder' and name = 'On Duty Timesheets'"
        )

    def test_get_folder_id_no_file(self, mocker: MockerFixture):
        mocker.patch(
            "helpers.google_services.DriveOperations.asmbly_drive_file_search"
        ).return_value = {"files": []}

        mock_drive_instance = DriveOperations(mocker.Mock(), "Test Volunteer Name")

        assert mock_drive_instance.get_folder_id("On Duty Timesheets") == {}

        mock_drive_instance.asmbly_drive_file_search.assert_called_with(
            "mimeType = 'application/vnd.google-apps.folder' and name = 'On Duty Timesheets'"
        )

    def test_get_folder_id_multiple_files(self, mocker: MockerFixture, caplog):
        mocker.patch(
            "helpers.google_services.DriveOperations.asmbly_drive_file_search"
        ).return_value = {
            "files": [
                {
                    "id": "123",
                    "name": "On Duty Timesheets",
                    "mimeType": "application/vnd.google-apps.folder",
                },
                {
                    "id": "456",
                    "name": "On Duty Timesheets",
                    "mimeType": "application/vnd.google-apps.folder",
                },
            ]
        }

        mock_drive_instance = DriveOperations(mocker.Mock(), "Test Volunteer Name")

        assert mock_drive_instance.get_folder_id("On Duty Timesheets") == {
            "id": "123",
            "name": "On Duty Timesheets",
            "mimeType": "application/vnd.google-apps.folder",
        }

        mock_drive_instance.asmbly_drive_file_search.assert_called_with(
            "mimeType = 'application/vnd.google-apps.folder' and name = 'On Duty Timesheets'"
        )

        assert (
            "More than one folder found with name 'On Duty Timesheets'" in caplog.text
        )

    def test_check_timesheet_exists(self, mocker: MockerFixture):
        mocker.patch(
            "helpers.google_services.DriveOperations.asmbly_drive_file_search"
        ).return_value = {
            "files": [
                {
                    "id": "78910",
                    "name": "Test Volunteer Name",
                    "mimeType": "application/vnd.google-apps.spreadsheet",
                }
            ]
        }

        mock_instance = DriveOperations(mocker.Mock(), "Test Volunteer Name")

        mock_instance.check_timesheet_exists()

        mock_instance.asmbly_drive_file_search.assert_called_with(
            'mimeType="application/vnd.google-apps.spreadsheet"'
            f' and "{mock_instance.parent_folder_id}" in parents'
            f' and name="ODV Timesheet - {mock_instance.volunteer_name}"'
            " and trashed=false"
        )

    def test_create_timesheet(self, mock_folders, mocker: MockerFixture):
        mocker.patch(
            "helpers.google_services.DriveOperations.get_folder_id"
        ).side_effect = mock_folders

        mock_instance = DriveOperations(mocker.Mock(), "Test Volunteer Name")

        m = mocker.MagicMock()
        m.files().copy().execute.return_value = {
            "id": "12345678",
            "name": "Test Volunteer Name",
            "mimeType": "application/vnd.google-apps.spreadsheet",
        }

        mocker.patch.object(mock_instance, "drive_service", new=m)

        mock_instance.create_timesheet()

        m.files().copy.assert_called_with(
            fileId=mock_instance.template_sheet_id,
            body={
                "name": f"ODV Timesheet - {mock_instance.volunteer_name}",
                "parents": [mock_instance.parent_folder_id],
            },
            supportsAllDrives=True,
        )
