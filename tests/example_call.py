from config import INTERNAL_API_KEY

example_call = {
    "version": "2.0",
    "routeKey": "$default",
    "rawPath": "/",
    "rawQueryString": "",
    "headers": {
        "content-length": "174",
        "content-type": "application/json",
        "accept-encoding": "gzip, deflate",
        "accept": "*/*",
        "user-agent": "Openpath/Rules Engine"
    },
    "requestContext": {
        "accountId": "anonymous",
        "http": {
            "method": "POST",
            "path": "/",
            "protocol": "HTTP/1.1",
            "userAgent": "Openpath/Rules Engine"
        },
        "requestId": "41397b3c-6126-42fd-8de3-b3386a010c4d",
        "routeKey": "$default",
        "stage": "$default",
        "time": "30/Jan/2024:05:13:48 +0000",
        "timeEpoch": 1706591628865
    },
    "body": f'''{{
        "userId": "3562272",
        "timestamp": "1706596070",
        "entryId": "Instructors Locker",
        "apiKey": "{INTERNAL_API_KEY}"
    }}''',
    "isBase64Encoded": False
}
