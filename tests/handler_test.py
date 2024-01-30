import pytest
import json

from lambda_function import handler
from config import INTERNAL_API_KEY


event_json = f"""
{{
  "body": {{
    "userId": "3562272",
    "timestamp": "1706570376",
    "entry": "Instructors Locker",
    "apiKey": "{INTERNAL_API_KEY}"
  }}
}}
"""

expected = {
  "body": {
    "userId": "3562272",
    "timestamp": "1706570376",
    "entry": "Instructors Locker",
    "apiKey": INTERNAL_API_KEY
  }
}

event2 = f"""
{{
  "body": {{
    "userId": "3562272",
    "timestamp": "1706580000",
    "entry": "Clock Out",
    "apiKey": "{INTERNAL_API_KEY}"
  }}
}}
"""

expected2 = {
  "body": {
    "userId": "3562272",
    "timestamp": "1706580000",
    "entry": "Clock Out",
    "apiKey": INTERNAL_API_KEY
  }
}

@pytest.mark.parametrize("event_input, expected", [(event_json, expected), (event2, expected2)])
def test_handler(event_input, expected):
    assert json.loads(event_input).get("body") == expected.get("body")
    assert handler(json.loads(event_input), None) is None
