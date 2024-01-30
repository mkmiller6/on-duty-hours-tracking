import json
import pytest

from lambda_function import handler
from config import INTERNAL_API_KEY
from tests.example_call import example_call


expected = {"userId":"7385407","timestamp":"1706630094","entryId":"Instructors Locker","apiKey":f"{INTERNAL_API_KEY}"}

@pytest.mark.parametrize("event_input, expected_output", [(example_call, expected)])
def test_handler(event_input, expected_output):
    assert json.loads(event_input.get("body")) == expected_output
    assert handler(event_input, None) is None
