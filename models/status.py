import config
import base64
import requests
from app import *
import yahoo_api
import db
from collections import OrderedDict
import json
import os

def get_updates_with_league(yahoo_league_id, team_key, draft_id):
    if yahoo_league_id == None or team_key == None:
    	return {'success': False, 'updates': None, 'drafting_now': False}
    database = db.DB()
    database.dict_cur.execute(
        f"""
					SELECT u.latest_draft_update, u.latest_team_update, u.latest_forum_update, 
          				u.latest_player_db_update, u.latest_rules_update, u.latest_goalie_db_update, d.current_pick
          FROM updates u
					LEFT JOIN draft d
						ON u.draft_id = d.draft_id
          WHERE u.yahoo_league_id = {yahoo_league_id}
					AND u.draft_id = {draft_id}
        """)
    updates = database.dict_cur.fetchone()
    return {'success': True, 'updates': updates, 'drafting_now': check_if_drafting(database, team_key)}

def check_if_drafting(database, team_key):
    sql = "SELECT drafting_now FROM users WHERE team_key = %s"
    database.cur.execute(sql, [team_key])
    result = database.cur.fetchone()
    return result[0]

# Makes sure the draft session variable is set
def check_league(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'draft_id' not in session:
            database = db.DB()
            sql = "SELECT * FROM league WHERE yahoo_league_id = %s"
            league_id = str(os.environ['league_key'][-5:])
            result = database.cur.execute(sql, league_id)
            league = database.cur.fetchone()
            session['draft_id'] = league['most_recent_draft_id']

        return f(*args, **kwargs)
    return wrap


def set_team_sessions(league_key, team_query):
    my_team_data = {}

    my_team_data['yahoo_league_id'] = team_query['fantasy_content']['league']['league_id']
    teams = []
    for orderedDictTeam in team_query['fantasy_content']['league']['teams']['team']:
        team = dict(orderedDictTeam)
        team_data = {}
        # print("TEAM: " + str(team))
        team_data['yahoo_team_id'] = int(team['team_id'])
        team_data['team_key'] = team['team_key']
        team_data['user'] = team['managers']['manager']['nickname']
        team_data['team_name'] = team['name']
        team_data['team_logo'] = team['team_logos']['team_logo']['url']
        # team_data['waiver_priority'] = team['waiver_priority']

        # # some managers choose not to share their email, so this sets it to empty if that is the case
        try:
            team_data['email'] = team['managers']['manager']['email']
        except:
            team_data['email'] = ""

        if 'is_owned_by_current_login' in team:
            # if session['guid'] == team['managers']['manager']['guid']:
            my_team_data['yahoo_team_id'] = int(team['team_id'])
            my_team_data['logo'] = team['team_logos']['team_logo']['url']
            my_team_data['team_name'] = team['name']
            my_team_data['team_key'] = team['team_key']

            role, color, draft_id, current_pick, is_live = get_user(my_team_data['team_key'],
                            my_team_data['yahoo_league_id'])
            if is_live == None:
                is_live = False
                registered = False
                my_team_data['role'] = 'admin'
            else:
                my_team_data['role'] = role
                my_team_data['color'] = color
                my_team_data['draft_id'] = draft_id
                my_team_data['current_pick'] = current_pick
                is_live = is_live
                registered = True
        teams.append(team_data)
        print("success!")
    return teams, my_team_data, is_live, registered


def get_user(team_key, yahoo_league_id):
    database = db.DB()
    sql = """
		SELECT u.role, u.color, d.draft_id, d.current_pick, d.is_live
		FROM users u
		INNER JOIN draft d
			ON u.yahoo_league_id = d.yahoo_league_id
		WHERE team_key = %s
		AND d.yahoo_league_id = %s
	"""
    database.cur.execute(sql, (team_key, yahoo_league_id))
    return database.cur.fetchone()


def check_draft_status(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        database = db.DB()
        # draft.checkCurrentPickInDraft()
        sql = "SELECT * FROM draft d LEFT JOIN draft_picks dp ON d.draft_id = dp.draft_id WHERE d.draft_id = %s ORDER BY dp.overall_pick"
        database.cur.execute(sql, session['draft_id'])
        draft_info = database.cur.fetchone()
        if draft_info['is_live'] == 1:
            session['current_pick'] = draft.getCurrentPickInfo(
                draft_info['current_pick'])
        else:
            session['current_pick'] = 0

        draft_start_time = draft_info['draft_start_time_utc']
        if (draft_info['is_live'] == 0) and (draft_start_time < datetime.datetime.utcnow() and draft_info['is_over'] == 0):
            sql = "UPDATE draft SET is_live=1, current_pick = 1 WHERE draft_id = %s"
            database.cur.execute(sql, session['draft_id'])
            database.connection.commit()
            sql = "UPDATE users SET drafting_now = TRUE WHERE user_id = %s"
            database.cur.execute(sql, draft_info['user_id'])
            database.connection.commit()
        # print("IS OVER? : " + str(draft_info['is_over']))
        if draft_info['is_over'] == 1:
            session['current_pick'] = None
        return f(*args, **kwargs)
    return wrap
