from typing import Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Union
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

origins = [
    "https://slowdraft.netlify.app",
    "http://localhost:3000",
    "http://0.0.0.0:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/login/{code}")
def login(code: str):
    return oauth_login(code)


@app.post('/select_league')
async def league_selection(league: SelectLeague, authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return select_league(user, league.league_key)


@app.get('/check_for_updates')
async def check_for_updates_with_user_and_league(authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    print(f"Getting updates for {user['team_name']} ({user['team_key']})")
    return get_updates_with_league(user['yahoo_league_id'], user['team_key'])


@app.get('/get_db_players')
# @exception_handler
async def get_players_from_db(position: str = 'skaters', authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return get_db_players(user['draft_id'], position)


@app.get('/get_teams')
# @exception_handler
async def get_teams(authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    if 'draft_id' not in user:
        return util.return_error('no_draft_id')
    return get_teams_from_db(user['draft_id'])

# -------------------------- Forum & Rules routes --------------------------


@app.get('/get_forum_posts')
async def forum(authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return get_forum_posts(user['yahoo_league_id'])


@app.post('/new_forum_post')
async def post_to_forum(post: ForumPostForm, authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return new_forum_post(post, user)


@app.post('/edit_post')
async def update_post(post: ForumPostForm, authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return update_forum_post(user, post)


@app.get("/view_post_replies/{post_id}")
async def view_forum_post_replies(post_id: int, authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return get_post_replies(user['yahoo_league_id'], post_id)


@app.get('/get_all_rules')
async def get_all_rules(authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return get_rules(user['yahoo_league_id'])


@app.post('/create_rule')
# @check_if_admin
async def create_rule(post: RulePostForm, authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return new_rule(post, user)


@app.post('/edit_rule')
# @check_if_admin
async def edit_rule(post: RulePostForm, authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return update_rule(post, user)


@app.get('/get_draft')
# @exception_handler
async def get_dps(authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return get_draft(user['draft_id'], user['team_key'])

# ____________________________________________________


@app.on_event("startup")
async def startup_event():
    if 'client_id' in os.environ:
        config.client_id = os.environ['client_id']
        config.client_secret = os.environ['client_secret']
        config.redirect_uri = "https://slowdraft.netlify.app"
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
