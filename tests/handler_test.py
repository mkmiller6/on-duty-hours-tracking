import pytest
import json

from lambda_function import handler
from config import INTERNAL_API_KEY


event_json = f"""
{{
  "body": {{
    "userId": "3562272",
    "timestamp": "1706570376",
    "entryId": "124165",
    "apiKey": {INTERNAL_API_KEY}
  }}
}}
"""

expected = {
  "body": {
    "userId": "3562272",
    "timestamp": "1706570376",
    "entryId": "124165",
    "apiKey": INTERNAL_API_KEY
  }
}

@pytest.mark.parametrize("event_input, expected", [(event_json, expected)])
def test_handler(event_input, expected):
    assert json.loads(event_input).get("body") == expected.get("body")