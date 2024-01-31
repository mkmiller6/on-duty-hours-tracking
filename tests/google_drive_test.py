import pytest
from pytest_mock import MockerFixture
from googleapiclient.http import HttpMock, HttpMockSequence

from helpers.google_drive import (
    get_access_token,
    get_folder_id,
    batch_update_new_sheet,
    batch_update_copied_spreadsheet,
    SlideshowOperations
)

def test_batch_update_copied_spreadsheet():
    pass
