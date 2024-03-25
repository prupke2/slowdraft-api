from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import Union, List
from oauth import *
from oauth.web_token import *
from random import randint
import config
import os
import sys
import json
from models.league import *
from models.players import *
from models.forum import *
from models.status import *
from models.draft import *
from models.watchlist import *
from models.team import *
from models.rules import *
from models.emails import *
from models.pd import *
from models.doc import *
import models.chat
from yahoo_api import *
import db
import datetime
import psycopg2

app = FastAPI()

origins = [
    "https://slowdraft.vercel.app",
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


manager = models.chat.SocketManager()


@app.get("/health")
def health():
    return 200


@app.websocket("/chat")
async def chat(
    websocket: WebSocket,
    user: Union[str, None] = Query(default=None)
):
    if user:
        print(f"websocket user: {user}")
        await manager.connect(websocket, user)
        user_list = await manager.get_connected_users()
        response = {
            "user": user,
            "status": "connected",
            "users": user_list
        }
        print(f"response: {response}")
        await manager.broadcast(response)
        try:
            while True:
                data = await websocket.receive_json()
                # if data is not None:
                print(f"ws data: {data}")
                await manager.broadcast(data)
        except WebSocketDisconnect as e:
            print(f"WebSocketDisconnect: {e}")
            manager.disconnect(websocket, user)
            await manager.broadcast_user_disconnect(user)
        # except ConnectionClosed as e:
        #     print(f"ConnectionClosed: {e}")
        #     manager.disconnect(websocket, user)
        #     await manager.broadcast_user_disconnect(user)
        # except websockets.exceptions.ConnectionClosed as e:
        #     print(f"websockets ConnectionClosed: {e}")
        #     manager.disconnect(websocket, user)
        #     await manager.broadcast_user_disconnect(user)
        # except ConnectionClosedOK as e:
        #     print(f"ConnectionClosedOK: {e}")
        #     pass
        # except websockets.exceptions.ConnectionClosedOK as e:
        #     print(f"websockets ConnectionClosedOK: {e}")
        #     pass
        # except ConnectionClosedError as e:
        #     print(f"Connection Closed Error: {e}")
        #     manager.disconnect(websocket, user)
        #     await manager.broadcast_user_disconnect(user)
        # except websockets.exceptions.ConnectionClosedError as e:
        #     print(f"websockets Connection Closed Error: {e}")
        #     manager.broadcast_user_disconnect(user)
        #     await manager.disconnect(websocket, user)
        except Exception as e:
            print(f"Unknown error for {websocket}, {user}: {e}")
            manager.disconnect(websocket, user)
            await manager.broadcast_user_disconnect(user)

@app.get("/login/{code}")
def login(code: str):
    print('At login route')
    
    return oauth_login(code)


@app.post('/select_league')
def league_selection(league: SelectLeague, authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return select_league(user, league.league_key)


@app.get('/check_for_updates')
async def check_for_updates_with_user_and_league(authorization: str = Header(None)):
    try:
      user = get_user_from_auth_token(authorization)
      print(f"Getting updates for {user['team_name']} ({user['team_key']})")
      return get_updates_with_league(user['yahoo_league_id'], user['team_key'], user['draft_id'])
    except Exception as e:
      if 'error' in user:
        print(f"Error in check_for_updates: {user['error']}, status: {user['status']}")
        return util.return_error(user['error'], user['status'])
      print(f"Error in check_for_updates: {e}")
      return util.return_error('unknown')

@app.get('/get_db_players')
# @exception_handler
async def get_players_from_db(authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return get_db_players(user['draft_id'])


@app.get('/get_db_players_new')
# @exception_handler
async def get_players_from_db(position: str = 'skaters', authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return get_db_players_new(user['draft_id'], position)


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


@app.post('/create_post')
async def create_post(post: ForumPostForm, authorization: str = Header(None)):
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


# ------------------------ Watchlist routes ------------------------

@app.get('/get_watchlist')
# @check_if_admin
async def get_watchlist(authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return get_watchlist_ids(user['yahoo_league_id'], user['team_key'])

@app.post('/add_to_watchlist')
# @check_if_admin
async def add_to_watchlist(post: WatchlistForm, authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return add_player_to_watchlist(user['yahoo_league_id'], user['team_key'], post.player_id)


@app.post('/remove_from_watchlist')
# @check_if_admin
async def remove_from_watchlist(post: WatchlistForm, authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return remove_player_from_watchlist(user['yahoo_league_id'], user['team_key'], post.player_id)


# -------------------------- Draft routes --------------------------


@app.get('/get_draft')
# @exception_handler
async def get_dps(authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return get_draft(user['draft_id'], user['team_key'])


@app.get('/draft/{player_id}')
# @exception_handler
async def draft_player(player_id, authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return make_pick(user['draft_id'], player_id, user['team_key'])



# -------------------------- Admin routes --------------------------


@app.post('/make_pick')
# @exception_handler
# @check_if_admin
async def draft_player_admin(post: MakePickForm, authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return make_pick(user['draft_id'], post.player_id, post.team_key)


@app.post('/update_pick')
# @exception_handler
# @check_if_admin
async def update_pick(post: UpdatePickForm, authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return change_pick(post.team_key, post.overall_pick, user['yahoo_league_id'], user['draft_id'])


@app.post('/update_pick_enablement')
# @exception_handler
# @check_if_admin
async def toggle_pick(post: TogglePickForm, authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return toggle_pick_enabled(post.overall_pick, user['draft_id'])


@app.post('/insert_player')
# @exception_handler
# @check_if_admin
async def insert_player(post: InsertPlayerForm, authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return insert_db_player(post.name, post.player_id, post.team, post.positions, user['draft_id'])


@app.post('/add_keeper_player')
# @exception_handler
# @check_if_admin
async def add_keeper_player(post: AddKeeperPlayerForm, authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return add_keeper(post.team_key, post.player_id, user['draft_id'])


@app.post('/add_new_pick')
# @exception_handler
# @check_if_admin
async def add_new_pick(post: AddNewPickForm, authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return add_pick_to_draft(user['draft_id'], user['yahoo_league_id'], post.team_key)


@app.post('/create_draft')
# @exception_handler
# @check_if_admin
def create_draft(post: CreateNewDraftForm, authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return create_new_draft(user, post.teams, post.rounds, False, post.team_order)

# -------------------------- Doc routes --------------------------

@app.get('/get_doc_url')
def get_doc_url(authorization: str = Header(None)):
    user = get_user_from_auth_token(authorization)
    return get_url(user)


# ____________________________________________________


@app.on_event("startup")
async def startup_event():
    if 'client_id' in os.environ:
        config.client_id = os.environ['client_id']
        config.client_secret = os.environ['client_secret']
        config.redirect_uri = "https://slowdraft.vercel.app"
        # config.pubnub_publish_key = os.environ['pubnub_publish_key']
        # config.pubnub_subscribe_key = os.environ['pubnub_subscribe_key']
        # config.SENDGRID_KEY = os.environ['SENDGRID_KEY']

        # get Yahoo league credentials
        config.league_key = os.environ['game_key'] + ".l." + os.environ['yahoo_league_id']
        config.yahoo_league_id = os.environ['yahoo_league_id']
        config.draft_id = os.environ['draft_id']
        config.game_key = os.environ['game_key']

        # get email and pd creds
        config.from_email = os.environ['from_email']
        config.pd_api = os.environ['pd_api']

        # get doc config
        config.url = os.environ['url']

        # get DB config
        config.host = os.environ['POSTGRES_HOST']
        config.user = os.environ['POSTGRES_USER']
        config.password = os.environ['POSTGRES_PASSWORD']
        config.db = os.environ['POSTGRES_DB']

        database = psycopg2.connect(
          host=os.environ['POSTGRES_HOST'],
          database=os.environ['POSTGRES_DB'],
          user=os.environ['POSTGRES_USER'],
          password=os.environ['POSTGRES_PASSWORD']
        )

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
        config.draft_id = credentials.draft_id
        config.game_key = credentials.game_key

        # get email and pd creds
        config.from_email=credentials.from_email
        config.pd_api=credentials.pd_api

        # get doc config
        config.url = credentials.url

        # get local DB credentials
        config.host, config.user, config.password, config.db = credentials.get_local_DB()

        config.SENDGRID_KEY = credentials.SENDGRID_KEY
