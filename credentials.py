"""
Generate decrypted credentials from AWS KMS.
"""


from base64 import b64decode
import os
import boto3


ENCRYPTED_OP_APIKEY = os.environ['O_APIkey']
ENCRYPTED_OP_APIUSER = os.environ['O_APIuser']

ENCRYPTED_MASTER_LOG_SPREADSHEET_ID = os.environ['MASTER_LOG_SPREADSHEET_ID']
ENCRYPTED_TEMPLATE_SHEET_ID = os.environ['TEMPLATE_SHEET_ID']
ENCRYPTED_PARENT_FOLDER_ID = os.environ['PARENT_FOLDER_ID']

ENCRYPTED_PRIV_SA = os.environ['PRIV_SA']
ENCRYPTED_KEY_FILE = os.environ['KEY_FILE']

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

priv_sa = boto3.client('kms').decrypt(
    CiphertextBlob=b64decode(ENCRYPTED_PRIV_SA),
    EncryptionContext={'LambdaFunctionName': os.environ['AWS_LAMBDA_FUNCTION_NAME']}
)['Plaintext'].decode('utf-8')

key_file = boto3.client('kms').decrypt(
    CiphertextBlob=b64decode(ENCRYPTED_KEY_FILE),
    EncryptionContext={'LambdaFunctionName': os.environ['AWS_LAMBDA_FUNCTION_NAME']}
)['Plaintext'].decode('utf-8')
