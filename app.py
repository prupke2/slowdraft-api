from typing import Optional
from fastapi import FastAPI
from pydantic import BaseModel
from oauth import *
from oauth.web_token import *
from random import randint
import time
import config
import os
import sys
import json
from models.league import *
from models.players import *
from models.forum import *
from models.status import *
from models.draft import *
from models.team import *
from models.rules import *
from models.emails import *
from yahoo_api import *
import db
import datetime
import pymysql

app = FastAPI()

class SelectLeague(BaseModel):
    league_key: str

@app.get("/login/{code}")
def login(code: str):
    return oauth_login(code)

@app.post('/select_league')
# @exception_handler
async def league_selection(league_key: SelectLeague, authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return select_league(user, league_key.league_key)

@app.on_event("startup")
async def startup_event():
    # app.run(use_reloader=True, port=5000, threaded=True, debug=True)
    if 'client_id' in os.environ:
        config.client_id = os.environ['client_id']
        config.client_secret = os.environ['client_secret']
        config.redirect_uri = "https://slowdraft.onrender.com"
        config.pubnub_publish_key = os.environ['pubnub_publish_key']
        config.pubnub_subscribe_key = os.environ['pubnub_subscribe_key']
        config.SENDGRID_KEY = os.environ['SENDGRID_KEY']

        # get Yahoo league credentials
        # config.league_key = os.environ['game_key'] + \
        #     ".l." + os.environ['yahoo_league_id']
        # config.draft_id = os.environ['draft_id']

        # get DB config
        config.host = os.environ['MYSQL_HOST']
        config.user = os.environ['MYSQL_USER']
        config.password = os.environ['MYSQL_PASSWORD']
        config.db = os.environ['MYSQL_DB']
        database = db.DB()

        # config.yahoo_league_id = [os.environ['yahoo_league_id']]
        # config.league_id = os.environ['league_id']
        # config.draft_id = os.environ['draft_id']
    else:
        import credentials
        app.secret_key = credentials.SECRET_KEY
        # get Yahoo Oauth credentials
        config.client_id = credentials.consumer_key
        config.client_secret = credentials.consumer_secret
        config.redirect_uri = "oob"

        # get Yahoo league credentials
        config.league_key = credentials.game_key + ".l." + credentials.yahoo_league_id
        config.yahoo_league_id = credentials.yahoo_league_id
        config.league_id = credentials.league_id
        config.draft_id = credentials.draft_id

        # get Pubnub credentials (for chat)
        config.pubnub_publish_key = credentials.pubnub_publish_key
        config.pubnub_subscribe_key = credentials.pubnub_subscribe_key

        # get local DB credentials
        config.host, config.user, config.password, config.db = credentials.get_local_DB()
        database = db.DB()

        config.SENDGRID_KEY = credentials.SENDGRID_KEY

    # @app.before_request
    # def force_https():
    #     if request.endpoint in app.view_functions and not request.is_secure:
    #         return redirect(request.url.replace('http://', 'https://'))
