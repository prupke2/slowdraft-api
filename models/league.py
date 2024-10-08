from app import *
from config import *
from pydantic import BaseModel
import yahoo_api
import oauth.yahoo_oauth
import oauth.web_token
from models import status
import db
import util
import config
import os

class SelectLeague(BaseModel):
    league_key: str


def get_chat_token(role):
    # if role == "admin":
    #     token = os.environ["chat_token_admin"]
    # else:
    #     token = os.environ["chat_token_user"]
    return {
        'success': True,
        'token': os.environ["chat_token_admin"]
    }

def get_leagues(access_token, refresh_token):
    GET_LEAGUES_URL = YAHOO_BASE_URL + f'users;use_login=1/games;game_keys={os.environ["game_key"]}/leagues'
    try:
        leagues_query = yahoo_api.yahoo_request(GET_LEAGUES_URL, access_token, refresh_token, True)
        if leagues_query == False:
            return util.return_error("token_error")
        user = leagues_query['fantasy_content']['users']['0']['user']
        leagues = user[1]['games']['0']['game'][1]['leagues']
        league_count = leagues['count']
        if league_count == 0:
            return []
        league_list = []
        for i in range(league_count):
            league_list.append(leagues[str(i)]['league'][0])
        print(f'league_list: {league_list}')    
        return league_list
    except Exception as e:
        print(f"Error in get_leagues function: {e}")
        return []


def register_leagues(access_token, refresh_token):
    leagues = get_leagues(access_token, refresh_token)
    league_list, registered_count = check_league_registrations(leagues)
    # if registered_count == 1:
    league_key = get_registered_league(league_list)
    if league_key is None:
        return util.return_error('invalid_league', 403)
    team_query = get_teams_in_league(
        league_key, access_token, refresh_token)
    print(f'team_query: {team_query}')
    
    teams, my_team_data, is_live_draft, registered = status.set_team_sessions(
        league_key, team_query)
    web_token = oauth.web_token.generate_web_token(
        leagues, my_team_data, access_token, refresh_token)
    # else:
    #     my_team_data = None
    #     teams = None
    #     is_live_draft = None
    #     registered = registered_count > 0
    #     web_token = oauth.web_token.generate_temp_web_token(
    #         league_list, access_token, refresh_token)
    print(f"\nNEW LOGIN: {my_team_data}\n")

    return {
        'success': True,
        'pub': pubnub_publish_key,
        'sub': pubnub_subscribe_key,
        'league_list': league_list,
        'user': my_team_data,
        'teams': teams,
        'web_token': web_token,
        'is_live_draft': is_live_draft,
        'registered': registered
    }


def get_registered_league(league_list):
    for league in league_list:
        if league['league_key'] == os.environ['league_key']:
            return league['league_key']
    return None


def validate_league_key(league_list, league_key):
    for league in league_list:
        print(f"league['league_key']: {league['league_key']}")
        print(f"league_key: {league_key}")
        if league['league_key'] == league_key:
            return True
    return False


def check_league_registrations(leagues):
    database = db.DB()
    print(f"leagues: {leagues}")
    yahoo_league_id_list = [league['league_id'] for league in leagues]
    print(f"yahoo_league_id_list: {yahoo_league_id_list}")
    sql = f"""
			SELECT yahoo_league_id
			FROM yahoo_league
			WHERE yahoo_league_id IN ({str(yahoo_league_id_list)[1:-1]})
		"""
    print(f"sql: {sql}")
    database.dict_cur.execute(sql)
    leagues_query = database.dict_cur.fetchall()
    print(f"leagues_query: {leagues_query}")
    # print(f"type(leagues_query): {type(leagues_query)}")
    registered_leagues = []
    for i, league in enumerate(leagues_query):
        print(f"league: {league}")
        registered_leagues.append(league)
    for league in leagues:
        league['registered'] = int(league['league_id']) in registered_leagues
    print(f"\n\nLEAGUES: {leagues}\n\n")
    print(f"registered_leagues: {registered_leagues}")
    return leagues, len(registered_leagues)


def select_league(user, league_key):
    league_check = validate_league_key(user['leagues'], league_key)
    if league_check == False:
        util.return_error('invalid_league', 403)
    try:
        team_query = get_teams_in_league(
                league_key, user['access_token'], user['refresh_token'])
        if 'success' in team_query and team_query['success'] == False:
            return {
                'success': False,
                'error': team_query['error']
            }
        teams, my_team_data, is_live_draft, registered = status.set_team_sessions(
                league_key, team_query)
        print(f"\n\nmy_team_data: {my_team_data}")
        web_token = oauth.web_token.generate_web_token(
                user['leagues'], my_team_data, user['access_token'], user['refresh_token'])
        return {
            'success': True,
            'pub': pubnub_publish_key,
            'sub': pubnub_subscribe_key,
            'user': my_team_data,
            'teams': teams,
            'web_token': web_token,
            'is_live_draft': is_live_draft,
            'registered': registered
        }
    except Exception as e:
        print(f"Error in select_league: {e}")
        return util.return_error(e)


def get_teams_in_league(league_key, access_token, refresh_token):
    TEAM_URL = YAHOO_BASE_URL + "league/" + league_key + "/teams"
    try:
        team_query = yahoo_api.yahoo_request(
            TEAM_URL, access_token, refresh_token)
        if team_query == False:
            return util.return_error("token_error")
        return team_query
    except Exception as e:
        print(f"Error in get_teams_in_league: {e}")
        return util.return_error(e)
