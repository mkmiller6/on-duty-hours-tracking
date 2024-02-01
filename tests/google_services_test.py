#pylint: disable=missing-docstring
#pylint: disable=redefined-outer-name

import pytest
from pytest_mock import MockerFixture

from googleapiclient.discovery import Resource

from helpers.google_services import (
    get_folder_id,
    SlideshowOperations,
)


@pytest.fixture
def access_token(mocker: MockerFixture):
    token = mocker.Mock()

    token.return_value = "asdkfasfdlkjasl;dkfj"

    return token


@pytest.fixture
def build(mocker: MockerFixture):
    build = mocker.Mock()

    build_return_value = mocker.MagicMock(spec=Resource)

    build.return_value = build_return_value

    return build


def test_get_folder_id_with_file(access_token, build, mocker: MockerFixture):
    mocker.patch(
        "helpers.google_services.get_access_token",
    ).return_value = access_token

    mocker.patch("helpers.google_services.build").return_value = build

    mocker.patch("helpers.google_services.asmbly_drive_file_search").return_value = {
        "files": [
            {
                "id": "123",
                "name": "On Duty Timesheets",
                "mimeType": "application/vnd.google-apps.folder",
            }
        ]
    }

    assert get_folder_id("On Duty Timesheets") == {
        "id": "123",
        "name": "On Duty Timesheets",
        "mimeType": "application/vnd.google-apps.folder",
    }


def test_get_folder_id_no_file(access_token, build, mocker: MockerFixture):
    mocker.patch(
        "helpers.google_services.get_access_token",
    ).return_value = access_token

    mocker.patch("helpers.google_services.build").return_value = build

    mocker.patch("helpers.google_services.asmbly_drive_file_search").return_value = {
        "files": []
    }

    assert get_folder_id("On Duty Timesheets") == {}


class TestSlideshowOperations:
    @pytest.fixture
    def drive_service(self, mocker: MockerFixture):
        drive_service = mocker.Mock()

        drive_service.files.return_value = mocker.Mock(spec=Resource)

        return drive_service

    @pytest.fixture
    def volunteer_name(self):
        return "Test Volunteer Name"

    @pytest.fixture(autouse=True)
    def add_slide(self):
        return None

    @pytest.fixture(autouse=True)
    def trash_slide(self):
        return None

    @pytest.fixture
    def mock_get_folder_id_with_both_folders(self, mocker: MockerFixture):
        mock_results = mocker.Mock().side_effect = [
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

        return mock_results

    @pytest.fixture
    def mock_get_folder_id_with_volunteer_folder(self, mocker: MockerFixture):
        mock_results = mocker.Mock().side_effect = [
            {},
            {
                "id": "456",
                "name": "Volunteer Slides",
                "mimeType": "application/vnd.google-apps.folder",
            },
        ]

        return mock_results

    @pytest.fixture
    def mock_get_folder_id_with_slideshow_folder(self, mocker: MockerFixture):
        mock_results = mocker.Mock().side_effect = [
            {
                "id": "123",
                "name": "____LobbyTV",
                "mimeType": "application/vnd.google-apps.folder",
            },
            {},
        ]

        return mock_results

    @pytest.fixture
    def mock_get_folder_id_with_no_folder(self, mocker: MockerFixture):
        mock_results = mocker.Mock().side_effect = [
            {},
            {},
        ]

        return mock_results

    @pytest.fixture
    def slideshow_operations_with_slideshow_folder(
        self,
        drive_service,
        volunteer_name,
        mock_get_folder_id_with_slideshow_folder,
        mocker: MockerFixture,
    ):
        mocker.patch(
            "helpers.google_services.get_folder_id"
        ).side_effect = mock_get_folder_id_with_slideshow_folder

        return SlideshowOperations(drive_service, volunteer_name)

    @pytest.fixture
    def slideshow_operations_with_volunteer_folder(
        self,
        drive_service,
        volunteer_name,
        mock_get_folder_id_with_volunteer_folder,
        mocker: MockerFixture,
    ):
        mocker.patch(
            "helpers.google_services.get_folder_id"
        ).side_effect = mock_get_folder_id_with_volunteer_folder

        return SlideshowOperations(drive_service, volunteer_name)

    @pytest.fixture
    def slideshow_operations_with_both_folders(
        self,
        drive_service,
        volunteer_name,
        mock_get_folder_id_with_both_folders,
        mocker: MockerFixture,
    ):
        mocker.patch(
            "helpers.google_services.get_folder_id"
        ).side_effect = mock_get_folder_id_with_both_folders

        return SlideshowOperations(drive_service, volunteer_name)

    @pytest.fixture
    def slideshow_operations_with_no_folders(
        self,
        drive_service,
        volunteer_name,
        mock_get_folder_id_with_no_folder,
        mocker: MockerFixture,
    ):
        mocker.patch(
            "helpers.google_services.get_folder_id"
        ).side_effect = mock_get_folder_id_with_no_folder

        return SlideshowOperations(drive_service, volunteer_name)

    @pytest.fixture
    def slide_search_no_results(self):
        return {"files": []}

    @pytest.fixture
    def slide_search_with_results(self):
        return {
            "files": [
                {
                    "id": "789",
                    "name": "Test Volunteer Name",
                    "mimeType": "application/vnd.google-apps.file",
                }
            ]
        }

    def test_add_volunteer_to_slideshow_with_both_folders_with_results(
        self,
        slideshow_operations_with_both_folders,
        slide_search_with_results,
        mocker: MockerFixture,
    ):
        mocker.patch(
            "helpers.google_services.SlideshowOperations.slide_search"
        ).return_value = slide_search_with_results

        mocker.patch(
            "helpers.google_services.SlideshowOperations.add_slide"
        )

        slideshow_operations_with_both_folders.add_volunteer_to_slideshow()

        slideshow_operations_with_both_folders.slide_search.assert_called_once_with(
            "Test Volunteer Name",
            slideshow_operations_with_both_folders.volunteer_slides_folder_id
        )

        assert slideshow_operations_with_both_folders.volunteer_slides_folder_id == "456"

        slideshow_operations_with_both_folders.add_slide.assert_called_once_with(
            "789"
        )

    def test_add_volunteer_to_slideshow_with_both_folders_no_results(
        self,
        slideshow_operations_with_both_folders,
        slide_search_no_results,
        mocker: MockerFixture,
        caplog
    ):
        mocker.patch(
            "helpers.google_services.SlideshowOperations.slide_search"
        ).return_value = slide_search_no_results

        mocker.patch(
            "helpers.google_services.SlideshowOperations.add_slide"
        )

        slideshow_operations_with_both_folders.add_volunteer_to_slideshow()

        slideshow_operations_with_both_folders.slide_search.assert_called_once_with(
            "Test Volunteer Name",
            slideshow_operations_with_both_folders.volunteer_slides_folder_id
        )

        assert slideshow_operations_with_both_folders.volunteer_slides_folder_id == "456"

        slideshow_operations_with_both_folders.add_slide.assert_not_called()

        assert (
            "No slide for Test Volunteer Name, consider adding them"
            in caplog.text
        )

    def test_add_volunteer_to_slideshow_with_only_slideshow_folder(
        self,
        slideshow_operations_with_slideshow_folder,
        mocker: MockerFixture,
        caplog
    ):

        mocker.patch(
            "helpers.google_services.SlideshowOperations.add_slide"
        )

        mocker.patch(
            "helpers.google_services.SlideshowOperations.slide_search"
        )

        result = slideshow_operations_with_slideshow_folder.add_volunteer_to_slideshow()

        slideshow_operations_with_slideshow_folder.slide_search.assert_not_called()

        slideshow_operations_with_slideshow_folder.add_slide.assert_not_called()

        assert (
            "Folder 'Volunteer Slides' not found"
            in caplog.text
        )

        assert result is None

    def test_add_volunteer_to_slideshow_with_only_volunteer_folder_with_results(
        self,
        slideshow_operations_with_volunteer_folder,
        slide_search_with_results,
        mocker: MockerFixture,
    ):
        mocker.patch(
            "helpers.google_services.SlideshowOperations.slide_search"
        ).return_value = slide_search_with_results

        mocker.patch(
            "helpers.google_services.SlideshowOperations.add_slide"
        )

        slideshow_operations_with_volunteer_folder.add_volunteer_to_slideshow()

        slideshow_operations_with_volunteer_folder.slide_search.assert_called_once_with(
            "Test Volunteer Name",
            slideshow_operations_with_volunteer_folder.volunteer_slides_folder_id
        )

        assert slideshow_operations_with_volunteer_folder.volunteer_slides_folder_id == "456"

        slideshow_operations_with_volunteer_folder.add_slide.assert_called_once_with(
            "789"
        )

    def test_add_volunteer_to_slideshow_with_only_volunteer_folder_no_results(
        self,
        slideshow_operations_with_volunteer_folder,
        slide_search_no_results,
        mocker: MockerFixture,
        caplog
    ):
        mocker.patch(
            "helpers.google_services.SlideshowOperations.slide_search"
        ).return_value = slide_search_no_results

        mocker.patch(
            "helpers.google_services.SlideshowOperations.add_slide"
        )

        slideshow_operations_with_volunteer_folder.add_volunteer_to_slideshow()

        slideshow_operations_with_volunteer_folder.slide_search.assert_called_once_with(
            "Test Volunteer Name",
            slideshow_operations_with_volunteer_folder.volunteer_slides_folder_id
        )

        assert slideshow_operations_with_volunteer_folder.volunteer_slides_folder_id == "456"

        slideshow_operations_with_volunteer_folder.add_slide.assert_not_called()

        assert (
            "No slide for Test Volunteer Name, consider adding them"
            in caplog.text
        )

    def test_remove_volunter_from_slideshow_with_both_folders_with_results(
        self,
        slideshow_operations_with_both_folders,
        slide_search_with_results,
        mocker: MockerFixture,
    ):
        mocker.patch(
            "helpers.google_services.SlideshowOperations.slide_search"
        ).return_value = slide_search_with_results

        mocker.patch(
            "helpers.google_services.SlideshowOperations.trash_slide"
        )

        slideshow_operations_with_both_folders.remove_volunteer_from_slideshow()

        slideshow_operations_with_both_folders.slide_search.assert_called_once_with(
            "Test Volunteer Name",
            slideshow_operations_with_both_folders.slideshow_folder_id
        )

        assert slideshow_operations_with_both_folders.slideshow_folder_id == "123"

        slideshow_operations_with_both_folders.trash_slide.assert_called_once_with(
            "789"
        )

    def test_remove_volunteer_from_slideshow_with_both_folders_no_results(
        self,
        slideshow_operations_with_both_folders,
        slide_search_no_results,
        mocker: MockerFixture,
    ):
        mocker.patch(
            "helpers.google_services.SlideshowOperations.slide_search"
        ).return_value = slide_search_no_results

        mocker.patch(
            "helpers.google_services.SlideshowOperations.trash_slide"
        )

        slideshow_operations_with_both_folders.remove_volunteer_from_slideshow()

        slideshow_operations_with_both_folders.slide_search.assert_called_once_with(
            "Test Volunteer Name",
            slideshow_operations_with_both_folders.slideshow_folder_id
        )

        assert slideshow_operations_with_both_folders.slideshow_folder_id == "123"

        slideshow_operations_with_both_folders.trash_slide.assert_not_called()

    def test_remove_volunteer_from_slideshow_with_only_volunteer_folder(
        self,
        slideshow_operations_with_volunteer_folder,
        mocker: MockerFixture,
        caplog
    ):
        mocker.patch(
            "helpers.google_services.SlideshowOperations.trash_slide"
        )

        mocker.patch(
            "helpers.google_services.SlideshowOperations.slide_search"
        )

        result = slideshow_operations_with_volunteer_folder.remove_volunteer_from_slideshow()

        slideshow_operations_with_volunteer_folder.trash_slide.assert_not_called()

        slideshow_operations_with_volunteer_folder.slide_search.assert_not_called()

        assert(
            "Folder '____LobbyTV' not found"
            in caplog.text
        )

        assert result is None

    def test_remove_volunteer_from_slideshow_with_only_slideshow_folder_with_results(
        self,
        slideshow_operations_with_slideshow_folder,
        slide_search_with_results,
        mocker: MockerFixture,
    ):
        mocker.patch(
            "helpers.google_services.SlideshowOperations.slide_search"
        ).return_value = slide_search_with_results

        mocker.patch(
            "helpers.google_services.SlideshowOperations.trash_slide"
        )

        slideshow_operations_with_slideshow_folder.remove_volunteer_from_slideshow()

        slideshow_operations_with_slideshow_folder.slide_search.assert_called_once_with(
            "Test Volunteer Name",
            slideshow_operations_with_slideshow_folder.slideshow_folder_id
        )

        assert slideshow_operations_with_slideshow_folder.slideshow_folder_id == "123"

        slideshow_operations_with_slideshow_folder.trash_slide.assert_called_once_with(
            "789"
        )

    def test_remove_volunteer_from_slideshow_with_only_slideshow_folder_no_results(
        self,
        slideshow_operations_with_slideshow_folder,
        slide_search_no_results,
        mocker: MockerFixture,
    ):
        mocker.patch(
            "helpers.google_services.SlideshowOperations.slide_search"
        ).return_value = slide_search_no_results

        mocker.patch(
            "helpers.google_services.SlideshowOperations.trash_slide"
        )

        slideshow_operations_with_slideshow_folder.remove_volunteer_from_slideshow()

        slideshow_operations_with_slideshow_folder.slide_search.assert_called_once_with(
            "Test Volunteer Name",
            slideshow_operations_with_slideshow_folder.slideshow_folder_id
        )

        assert slideshow_operations_with_slideshow_folder.slideshow_folder_id == "123"

        slideshow_operations_with_slideshow_folder.trash_slide.assert_not_called()
