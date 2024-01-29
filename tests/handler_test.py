import pytest

from lambda_function import handler

@pytest.mark.parametrize("event", [
    {
        "path": "/",
        "httpMethod": "GET",
        "headers": {},
        "queryStringParameters": {},
        "pathParameters": None,
        "stageVariables": None,
        "requestContext": {},
        "body": None,
        "isBase64Encoded": False
    }
])

def test_handler(event):
    assert handler(event, None)
