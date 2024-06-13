# pylint: disable=missing-docstring, redefined-outer-name, no-member

import pytest
from pytest_mock import MockerFixture

from helpers.google_services import SheetsOperations

from config import MASTER_LOG_SPREADSHEET_ID, PRIV_SA


class TestSheetsOperations:
    @pytest.fixture
    def mock_instance(self, mocker: MockerFixture):
        mock_instance = SheetsOperations(
            mocker.Mock(), "Test Volunteer Name", "12345678"
        )

        return mock_instance

    @pytest.fixture
    def mock_clock_in_entry(self):
        return ("02/01/2024", "3:00 PM")

    @pytest.fixture
    def mock_clock_out_entry(self):
        return "5:00 PM"

    def test_init(self, mock_instance):
        assert mock_instance.volunteer_name == "Test Volunteer Name"
        assert mock_instance.volunteer_timesheet_id == "12345678"
        assert mock_instance.master_sheet_id == MASTER_LOG_SPREADSHEET_ID

    def test_initialize_copied_template(self, mock_instance, mocker: MockerFixture):
        m = mocker.MagicMock()
        m.get().execute.return_value = {
            "sheets": [
                {
                    "properties": {
                        "sheetId": 12345678,
                        "title": "Sheet1",
                    },
                    "protectedRanges": [
                        {
                            "protectedRangeId": 678,
                            "range": {
                                "sheetId": 12345678,
                                "startColumnIndex": 0,
                                "endColumnIndex": 4,
                            },
                            "description": "On-Duty Hours",
                            "warningOnly": False,
                            "editors": {"users": [PRIV_SA]},
                        }
                    ],
                }
            ]
        }

        m.values().append.return_value = mocker.Mock()

        mocker.patch.object(
            mock_instance,
            "sheet",
            new=m,
        )

        mocker.patch(
            "helpers.google_services.SheetsOperations.batch_update_copied_spreadsheet"
        ).return_value = mocker.Mock()

        mock_instance.initialize_copied_template()

        m.values().append.assert_called_with(
            spreadsheetId=mock_instance.volunteer_timesheet_id,
            range="Sheet1!F1:F2",
            body={
                "values": [
                    [f"Name: {mock_instance.volunteer_name}"],
                    ["Notes/Comments"],
                ]
            },
            valueInputOption="USER_ENTERED",
        )

        mock_instance.batch_update_copied_spreadsheet.assert_called_with(
            mock_instance.volunteer_timesheet_id,
            12345678,
            678,
        )

    def test_clock_in_master_sheet(self, mock_instance, mock_clock_in_entry):
        mock_instance.add_clock_in_entry_to_timesheet(mock_clock_in_entry, master=True)

        mock_instance.sheet.values().append.assert_called_with(
            spreadsheetId=mock_instance.master_sheet_id,
            range=f"'{mock_instance.volunteer_name}'!A3:B",
            body={"values": [[mock_clock_in_entry[0], mock_clock_in_entry[1]]]},
            valueInputOption="USER_ENTERED",
        )

    def test_clock_in_individual_sheet(self, mock_instance, mock_clock_in_entry):
        mock_instance.add_clock_in_entry_to_timesheet(mock_clock_in_entry)

        mock_instance.sheet.values().append.assert_called_with(
            spreadsheetId=mock_instance.volunteer_timesheet_id,
            range="Sheet1!A3:B",
            body={"values": [[mock_clock_in_entry[0], mock_clock_in_entry[1]]]},
            valueInputOption="USER_ENTERED",
        )

    def test_clock_out_master_sheet_gt_2_rows(
        self, mock_instance, mock_clock_out_entry, mocker: MockerFixture
    ):
        new_value = {
            "values": [
                ["ODV Timesheet - Test Volunteer Name"],
                ["Date", "Time"],
                ["02/01/2024", "3:00 PM"],
                ["02/01/2024", "5:00 PM"],
                ["02/01/2024", "7:00 PM"],
            ]
        }

        m = mocker.MagicMock()
        m.values().get().execute.return_value = new_value

        mocker.patch.object(
            mock_instance,
            "sheet",
            new=m,
        )

        mock_instance.add_clock_out_entry_to_timesheet(
            mock_clock_out_entry, master=True
        )

        m.values().update.assert_called_with(
            spreadsheetId=mock_instance.master_sheet_id,
            range=f"'{mock_instance.volunteer_name}'!C5:D5",
            body={
                "values": [
                    [
                        mock_clock_out_entry,
                        "=C5-B5",
                    ]
                ]
            },
            valueInputOption="USER_ENTERED",
        )

    def test_clock_out_ind_sheet_gt_2_rows(
        self, mock_instance, mock_clock_out_entry, mocker: MockerFixture
    ):
        new_value = {
            "values": [
                ["ODV Timesheet - Test Volunteer Name"],
                ["Date", "Time"],
                ["02/01/2024", "3:00 PM"],
                ["02/01/2024", "5:00 PM"],
                ["02/01/2024", "7:00 PM"],
            ]
        }

        m = mocker.MagicMock()
        m.values().get().execute.return_value = new_value

        mocker.patch.object(
            mock_instance,
            "sheet",
            new=m,
        )

        mock_instance.add_clock_out_entry_to_timesheet(mock_clock_out_entry)

        m.values().update.assert_called_with(
            spreadsheetId=mock_instance.volunteer_timesheet_id,
            range="Sheet1!C5:D5",
            body={
                "values": [
                    [
                        mock_clock_out_entry,
                        "=C5-B5",
                    ]
                ]
            },
            valueInputOption="USER_ENTERED",
        )

    def test_clock_out_master_sheet_lt_2_rows(
        self, mock_instance, mock_clock_out_entry, mocker: MockerFixture
    ):
        new_value = {
            "values": [["ODV Timesheet - Test Volunteer Name"], ["Date", "Time"]]
        }

        m = mocker.MagicMock()
        m.values().get().execute.return_value = new_value

        mocker.patch.object(
            mock_instance,
            "sheet",
            new=m,
        )

        mock_instance.add_clock_out_entry_to_timesheet(
            mock_clock_out_entry, master=True
        )

        m.values().update.assert_called_with(
            spreadsheetId=mock_instance.master_sheet_id,
            range=f"'{mock_instance.volunteer_name}'!C3:D3",
            body={
                "values": [
                    [
                        mock_clock_out_entry,
                        "=C3-B3",
                    ]
                ]
            },
            valueInputOption="USER_ENTERED",
        )

    def test_clock_out_ind_sheet_lt_2_rows(
        self, mock_instance, mock_clock_out_entry, mocker: MockerFixture
    ):
        new_value = {
            "values": [["ODV Timesheet - Test Volunteer Name"], ["Date", "Time"]]
        }

        m = mocker.MagicMock()
        m.values().get().execute.return_value = new_value

        mocker.patch.object(
            mock_instance,
            "sheet",
            new=m,
        )

        mock_instance.add_clock_out_entry_to_timesheet(mock_clock_out_entry)

        m.values().update.assert_called_with(
            spreadsheetId=mock_instance.volunteer_timesheet_id,
            range="Sheet1!C3:D3",
            body={
                "values": [
                    [
                        mock_clock_out_entry,
                        "=C3-B3",
                    ]
                ]
            },
            valueInputOption="USER_ENTERED",
        )

    def test_check_master_log_with_volunteer_sheet(
        self, mock_instance, mocker: MockerFixture
    ):
        mocker.patch(
            "helpers.google_services.SheetsOperations.get_all_sheets"
        ).return_value = [
            {
                "properties": {
                    "title": "asdfasdf",
                }
            },
            {
                "properties": {
                    "title": "Test Volunteer Name",
                }
            },
        ]

        assert mock_instance.check_master_log() is True

    def test_check_master_log_without_volunteer_sheet(
        self, mock_instance, mocker: MockerFixture
    ):
        mocker.patch(
            "helpers.google_services.SheetsOperations.get_all_sheets"
        ).return_value = [
            {
                "properties": {
                    "title": "asdfasdf",
                }
            }
        ]

        assert mock_instance.check_master_log() is False

    def test_check_master_log_no_sheets(self, mock_instance, mocker: MockerFixture):
        mocker.patch(
            "helpers.google_services.SheetsOperations.get_all_sheets"
        ).return_value = []

        assert mock_instance.check_master_log() is False

    def test_create_odv_sheet_in_master(self, mock_instance, mocker: MockerFixture):
        m = mocker.MagicMock()
        m.batchUpdate().execute.return_value = {
            "replies": [
                {
                    "addSheet": {
                        "properties": {
                            "title": "Test Volunteer Name",
                            "sheetId": 12345678,
                        }
                    }
                }
            ]
        }

        mocker.patch.object(
            mock_instance,
            "sheet",
            new=m,
        )

        mocker.patch(
            "helpers.google_services.SheetsOperations.batch_update_new_master_sheet"
        ).return_value = mocker.Mock()

        mock_instance.create_odv_sheet_in_master_spreadsheet()

        m.batchUpdate.assert_called_with(
            spreadsheetId=mock_instance.master_sheet_id,
            body={
                "requests": [
                    {
                        "addSheet": {
                            "properties": {"title": mock_instance.volunteer_name}
                        }
                    }
                ]
            },
        )

        mock_instance.batch_update_new_master_sheet.assert_called_with(
            mock_instance.master_sheet_id, 12345678, mock_instance.volunteer_name
        )
