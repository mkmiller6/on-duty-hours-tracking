"""
Generate decrypted credentials from AWS KMS.
"""


from base64 import b64decode
import os
import json
import boto3
from botocore.exceptions import ClientError


ENCRYPTED_OP_APIKEY = os.environ['O_APIkey']
ENCRYPTED_OP_APIUSER = os.environ['O_APIuser']

ENCRYPTED_MASTER_LOG_SPREADSHEET_ID = os.environ['MASTER_LOG_SPREADSHEET_ID']
ENCRYPTED_TEMPLATE_SHEET_ID = os.environ['TEMPLATE_SHEET_ID']
ENCRYPTED_PARENT_FOLDER_ID = os.environ['PARENT_FOLDER_ID']

ENCRYPTED_PRIV_SA = os.environ['PRIV_SA']
ENCRYPTED_INTERNAL_API_KEY = os.environ['INTERNAL_API_KEY']

def get_secret():

    secret_name = "google-timesheet-bot-private-key"
    region_name = "us-east-2"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    secret = get_secret_value_response['SecretString']

    return json.loads(secret)

# Decrypt code should run once and variables stored outside of the function
# handler so that these are decrypted once per container

O_APIkey = boto3.client('kms').decrypt(
    CiphertextBlob=b64decode(ENCRYPTED_OP_APIKEY),
    EncryptionContext={'LambdaFunctionName': os.environ['AWS_LAMBDA_FUNCTION_NAME']}
)['Plaintext'].decode('utf-8')

O_APIuser = boto3.client('kms').decrypt(
    CiphertextBlob=b64decode(ENCRYPTED_OP_APIUSER),
    EncryptionContext={'LambdaFunctionName': os.environ['AWS_LAMBDA_FUNCTION_NAME']}
)['Plaintext'].decode('utf-8')

MASTER_LOG_SPREADSHEET_ID = boto3.client('kms').decrypt(
    CiphertextBlob=b64decode(ENCRYPTED_MASTER_LOG_SPREADSHEET_ID),
    EncryptionContext={'LambdaFunctionName': os.environ['AWS_LAMBDA_FUNCTION_NAME']}
)['Plaintext'].decode('utf-8')

TEMPLATE_SHEET_ID = boto3.client('kms').decrypt(
    CiphertextBlob=b64decode(ENCRYPTED_TEMPLATE_SHEET_ID),
    EncryptionContext={'LambdaFunctionName': os.environ['AWS_LAMBDA_FUNCTION_NAME']}
)['Plaintext'].decode('utf-8')

PARENT_FOLDER_ID = boto3.client('kms').decrypt(
    CiphertextBlob=b64decode(ENCRYPTED_PARENT_FOLDER_ID),
    EncryptionContext={'LambdaFunctionName': os.environ['AWS_LAMBDA_FUNCTION_NAME']}
)['Plaintext'].decode('utf-8')

INTERNAL_API_KEY = boto3.client('kms').decrypt(
    CiphertextBlob=b64decode(ENCRYPTED_INTERNAL_API_KEY),
    EncryptionContext={'LambdaFunctionName': os.environ['AWS_LAMBDA_FUNCTION_NAME']}
)['Plaintext'].decode('utf-8')

priv_sa = boto3.client('kms').decrypt(
    CiphertextBlob=b64decode(ENCRYPTED_PRIV_SA),
    EncryptionContext={'LambdaFunctionName': os.environ['AWS_LAMBDA_FUNCTION_NAME']}
)['Plaintext'].decode('utf-8')

key_file = get_secret()
