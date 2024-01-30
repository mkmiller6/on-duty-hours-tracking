from config import INTERNAL_API_KEY

example_call = {
    "version": "2.0",
    "routeKey": "$default",
    "rawPath": "/",
    "rawQueryString": "",
    "headers": {
        "content-type": "application/json",
        "accept-encoding": "gzip, deflate",
        "accept": "*/*",
        "user-agent": "Openpath/Rules Engine",
    },
    "requestContext": {
        "accountId": "anonymous",
        "http": {
            "method": "POST",
            "path": "/",
            "protocol": "HTTP/1.1",
            "userAgent": "Openpath/Rules Engine",
        },
        "routeKey": "$default",
        "stage": "$default",
        "time": "30/Jan/2024:15:54:52 +0000",
        "timeEpoch": 1706630092598,
    },
    "body": f'{{"userId":"7385407","timestamp":"1706630094","entryId":"Instructors Locker","apiKey":"{INTERNAL_API_KEY}"}}',
    "isBase64Encoded": False,
}
