import config
import base64
import requests
from app import *
import models.status
import models.league
from .web_token import *
import util
import json
import os

def get_access_token(code):
    # This function takes the 7 digit code from the user and attempts to get a yahoo access token
    # If successful, the access and refresh tokens are returned
    base64_token = base64.b64encode((os.environ['client_id'] + ':' + os.environ['client_secret']).encode())    
    token = base64_token.decode("utf-8")
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'Authorization': 'Basic ' + str(token),
    }
    data = {
        'grant_type': 'authorization_code',
        'code': str(code),
        'client_id': os.environ['client_id'],
        'client_secret': os.environ['client_secret'],
        'redirect_uri': str(os.environ['redirect_uri'])
    }
    response = requests.post(config.GET_TOKEN_URL, headers=headers, data=data)
    print("\nResponse: " + str(response))
    print(str(response.json()))
    return response


def refresh_access_token(refresh_token, client_id, client_secret, redirect_uri):
    # Oauth access tokens expire after one hour
    # If it is expired, this function uses the refresh token stored in the session to get a new one
    print("Refreshing access token...")
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': redirect_uri,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token'
    }
    response = requests.post(config.GET_TOKEN_URL, data)
    if util.valid_2XX_response(response):
        token_response = response.json()
        config.access_token = token_response['access_token']
        config.refresh_token = token_response['refresh_token']
        return util.return_true()
    else:
        msg = json.loads(response.content.decode())
        print("Error getting token. ")
        print("HTTP Code: %s" % response.status_code)
        print("HTTP Response: \n%s" % msg)

        return {
            'success': False,
            'error': msg['error'],
            'status': response.status_code
        }


def oauth_login(code):
    if code == '' or code is None:
        return {
                    'success': False,
                    'error': 'No code provided',
                    'status': 400
                }

    response = get_access_token(code)

    if util.valid_2XX_response(response):
        token_response = response.json()
        try:
            register_attempt = models.league.register_leagues(token_response['access_token'], token_response['refresh_token'])
            return register_attempt
        except Exception as e:
            print(f"\nError setting team sessions: {e}\n")
            util.return_error('no_team_found')

    else:
        print(f"Login error. {response}.")
        print(f"Response: {response.status_code}. Error: {response.text}.")
        return {
            'success': False,
            'error': str(response),
            'status': response.status_code
        }
