from app import *
from config import *
import yahoo_api
import db
import config
import os

class AddKeeperPlayerForm(BaseModel):
		team_key: str
		player_id: int


def get_teams_from_db(draft_id):
	database = db.DB()
	print(f"draft_id in get_teams_from_db: {draft_id}")
	sql = f"""
			SELECT 	u.yahoo_team_id, 
							u.username,
							u.team_key,
							ut.is_keeper, 
							y2.name, 
							y2.team, 
							y2.position, 
							y2.prospect, 
							y2.player_id, 
							y2.headshot,
							{GOALIE_STAT_COLUMNS},
							{SKATER_STAT_COLUMNS},
							(	SELECT overall_pick
								FROM draft_picks dp
								WHERE draft_id = %s
								AND player_id = ut.player_id
							) AS "overall_pick"
			FROM user_team ut
			JOIN {YAHOO_PLAYER_DB} y2
					ON y2.player_id = ut.player_id
			LEFT JOIN {YAHOO_PLAYER_DB_PREVIOUS_YEAR} y1 -- join used to get stats
					ON y1.player_id = ut.player_id
			JOIN users u ON ut.team_key = u.team_key
			WHERE draft_id = %s
			ORDER BY u.yahoo_team_id, array_position(array[
				'LW', 'C', 'RW', 'RW/C', 'RW/LW', 'C/LW/RW', 'C/LW', 'C/RW',
				'LW/RW', 'LW/C', 'LW/D', 'D/LW', 'RW/D', 'D/RW', 'D', 'G'
			], y2.position);
			"""
	database.dict_cur.execute(sql, (draft_id, draft_id))
	teams = database.dict_cur.fetchall()
	return {'success': True, 'teams': teams}

def get_yahoo_team(team_id):
	ROSTER_URL = YAHOO_BASE_URL + "team/" + os.environ['league_key'] + ".t." + team_id + "/roster"
	roster = yahoo_api.yahoo_request(ROSTER_URL)
	if roster == '':
		return '','','','';	

	my_skaters = []
	my_goalies = []
	return roster['fantasy_content']['team']['name']		

def get_yahoo_team_players(team_id):
 
	ROSTER_URL = f"{YAHOO_BASE_URL}/team/{os.environ['league_key']}.t.{str(team_id)}/roster"
	roster = yahoo_api.yahoo_request(ROSTER_URL)
	if roster == '':
		return '','','','';	

	my_skaters = []
	my_goalies = []
	team = roster['fantasy_content']['team']['name']
	for player in roster['fantasy_content']['team']['roster']['players']['player']:
		player_data = {}
		player_data['player_id'] = str(player['player_id'])
		prospect, careerGP, NHLid = yahoo_api.checkIfProspect(player_data['player_id'])
		player_data['prospect'] = prospect
		player_data['careerGP'] = careerGP
		player_data['NHLid'] = NHLid
		player_data['player_key'] = player['player_key']
		player_data['name'] = player['name']['full']
		player_data['team'] = player['editorial_team_abbr']
		player_data['position'] = player['eligible_positions']
		if player['position_type'] == 'G':
			my_goalies.append(player_data)
		else:
			my_skaters.append(player_data)

	skater_keys = yahoo_api.organize_player_keys(my_skaters)	
	goalie_keys = yahoo_api.organize_player_keys(my_goalies)	

	# print("\n\nGOALIE KEYS: " + goalie_keys)

	MY_SKATERS_URL = YAHOO_BASE_URL + "players;player_keys=" + skater_keys + "/stats;date=2018"
	my_skater_stats = yahoo_api.yahoo_request(MY_SKATERS_URL)

	MY_GOALIES_URL = YAHOO_BASE_URL + "players;player_keys=" + goalie_keys + "/stats;date=2018"
	my_goalie_stats = yahoo_api.yahoo_request(MY_GOALIES_URL)

	skater_stats = yahoo_api.organizeStatData(my_skater_stats)
	goalie_stats = yahoo_api.organizeStatData(my_goalie_stats)

	return team, my_skaters, skater_stats, my_goalies, goalie_stats

def check_if_keepers(team_id):
	database = db.DB()
	sql = """
		SELECT player_id 
		FROM user_team ut 
		INNER JOIN users u 
			ON u.team_key = ut.team_key 
		WHERE u.yahoo_team_id = %s 
		AND ut.draft_id = %s
	"""
	database.cur.execute(sql, (team_id, session['draft_id']))
	return database.cur.fetchall()	

def check_validity_of_keepers(keys):
	database = db.DB()
	sql = f"SELECT * FROM {YAHOO_PLAYER_DB} WHERE player_id IN (" + keys + ")"
	result = database.cur.execute(sql)
	keepers = database.cur.fetchall()
	goalies = 0
	nonProspects = 0
	total = 0
	errors = ""
	for player in keepers:
		total += 1
		if player['prospect'] == '0':
			nonProspects += 1
		if player['position'] == 'G':
			goalies += 1
	if total >=11 or nonProspects >= 8 or goalies >= 3:
		errors = "Unable to save keepers:"		
		if total >= 11:
			errors += " Too many keepers saved (maximum 10)."	
		if nonProspects >= 8:
			errors += " Too many non-prospect keepers selected: you must keep at least 3 prospects."	
		if goalies >= 3:
			errors += " Too many goalie keepers selected: you may only keep two goalies."
		print
		return errors, False
	else:
		return keepers, True		


def add_keeper(team_key, player_id, draft_id):
	database = db.DB()
	sql = "INSERT INTO user_team(team_key, draft_id, player_id, is_keeper) VALUES(%s, %s, %s, %s)"
	result = database.cur.execute(sql, (team_key, draft_id, player_id, 1))
	database.connection.commit()
	util.update('latest_team_update', draft_id)
	util.update('latest_player_db_update', draft_id)
	util.update('latest_goalie_db_update', draft_id)
	return util.return_true()
