########### ATXHS NeonCRM & Discourse API Integrations ############
#      Neon API docs - https://developer.neoncrm.com/api-v2/     #
#################################################################
import os

from pprint import pformat
from base64 import b64encode
import requests
import logging

if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None:
    from credentials import O_APIkey, O_APIuser
else:
    from config import O_APIkey, O_APIuser

### OpenPath Account Info
O_auth      = f'{O_APIuser}:{O_APIkey}'
#Asmbly is OpenPath org ID 5231
O_baseURL   = 'https://api.openpath.com/orgs/5231'
O_signature = b64encode(bytearray(O_auth.encode())).decode()
O_headers   = {'Authorization': f'Basic {O_signature}', 'Accept': 'application/json', "Content-Type": "application/json"}


####################################################################
# Get a single OpenPath user by OpenPath ID
####################################################################
def getUser(opId:int):
    url = O_baseURL + f'/users/{opId}'
    response = requests.get(url, headers=O_headers)

    if (response.status_code != 200):
        raise ValueError(f'Get {url} returned status code {response.status_code}')

    return response.json().get("data")


####################################################################
# Given an OpenPath ID, return group membership
####################################################################
def getGroupsById(id):
    if not id:
        return []

    url = O_baseURL + f'/users/{id}/groups'
    response = requests.get(url, headers=O_headers)

    if (response.status_code != 200):
        raise ValueError(f'Get {url} returned status code {response.status_code}')

    return response.json().get("data")

####################################################################
# fetch all credentials for given OpenPath ID
####################################################################
def getCredentialsForId(id:int):
    #this should be a pretty thorough check for sane argument
    assert(int(id) > 0)

    url = O_baseURL + f'''/users/{id}/credentials?offset=0&sort=id&order=asc'''
    response = requests.get(url, headers=O_headers)
    if (response.status_code != 200):
        raise ValueError(f'Get {url} returned status code {response.status_code}')

    return response.json().get("data")
