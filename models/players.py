from app import *
from config import *
import yahoo_api
import db
import datetime
import os

# Form for searching players
# class PlayerSearchForm(Form):
# 	player_search = StringField('Player', [validators.Length(min=1, max=50)])
# 	# position = SelectField('Position')
# 	showdrafted = BooleanField('showdrafted')



class InsertPlayerForm(BaseModel):
		name: str
		player_id: int
		team: str
		positions: list



def insert_db_player(name, player_id, team, positions_array, draft_id):
	separator = " / "
	positions_string = separator.join(positions_array)
	player_key = "453.p." + str(player_id)
	database = db.DB()
	query = f"INSERT INTO {YAHOO_PLAYER_DB}(name, player_id, player_key, team, position, prospect) VALUES (%s, %s, %s, %s, %s, 1)"
	database.cur.execute(query, (name, player_id, player_key, team, positions_string))
	database.connection.commit()

	table = "latest_player_db_update"
	if positions_string == 'G':
		table = "latest_goalie_db_update"

	util.update(table, draft_id)
	return util.return_true()

def get_db_players(draft_id):
	# Gets the player list from the current year and the stats from the previous year
	database = db.DB()

	query = f"""
			SELECT DISTINCT
						(SELECT DISTINCT u.username FROM users u WHERE u.team_key = ut.team_key) AS "user", 
						ut.team_key,
						y2.name,
						y2.team,
						y2.player_id,
						y2.player_key,
						y2.position AS "position",
						y2.prospect AS "prospect",
						y2.careerGP AS "careerGP",
						y2.headshot AS "headshot",
						y2.ir,
						y2.average_pick,
						y2.percent_drafted,
						CASE 
							WHEN w.player_id = y2.player_id THEN true
							ELSE false
						END AS "watched",
						{GOALIE_STAT_COLUMNS},
 						{SKATER_STAT_COLUMNS}
			FROM {YAHOO_PLAYER_DB} y2
			LEFT JOIN user_team ut 
				ON ut.player_id = y2.player_id 
				AND ut.draft_id = {draft_id}
			LEFT JOIN {YAHOO_PLAYER_DB_PREVIOUS_YEAR} y1
				ON y2.player_id = y1.player_id
			LEFT JOIN watchlist w
				ON y2.player_id = w.player_id
		"""
	
	database.dict_cur.execute(query)
	players = database.dict_cur.fetchall()
	player_array = []
	for player in players:
		player_array.append(player)
	
	return {'success': True, 'players': players}

def get_players(sortby, sortdir, position, player_search, offset):
	LEAGUE_URL = YAHOO_BASE_URL + "league/" + os.environ['league_key']
	# all_free_agents = yahoo_request(YAHOO_BASE_URL + "league/" + os.environ['league_key'] + "/players;status=FA;count=22")
	if player_search != '':
		player_query = yahoo_api.yahoo_request(LEAGUE_URL + '/players;search=' + str(player_search))
	else:
		player_query = yahoo_api.yahoo_request(LEAGUE_URL + "/players?status=A&position=" + position + "&sort=" + str(sortby) \
		+ "&sdir=" + str(sortdir) + "&start=" + str(offset) + "&count=25;sorttype=season")

	if player_query == False:
			return util.return_error("token_error")
	# print("\n\nQUERY: " + str(player_query))

	skaters = []
	goalies = []
	# loops through the players and stores player info in new arrays
	try:
		for player in player_query['fantasy_content']['league']['players']['player']:
			player_data = {}
			player_data['player_id'] = player['player_id']
			player_data['player_key'] = str(player['player_key'])
			player_data['name'] = player['name']['full']
			player_data['team'] = player['editorial_team_abbr']
			player_data['position'] = player['eligible_positions']

			if player['display_position'] == 'G':
				goalies.append(player_data)
			else:
				skaters.append(player_data)
	except:
		player_data = {}
		try:
			player_data['player_id'] = player_query['fantasy_content']['league']['players']['player']['player_id']
			player_data['player_key'] = str(player_query['fantasy_content']['league']['players']['player']['player_key'])
			player_data['name'] = player_query['fantasy_content']['league']['players']['player']['name']['full']
			player_data['team'] = player_query['fantasy_content']['league']['players']['player']['editorial_team_abbr']	
			player_data['position'] = player_query['fantasy_content']['league']['players']['player']['eligible_positions']['position']

			if player['display_position'] == 'G':
				goalies.append(player_data)
			else:
				skaters.append(player_data)
		except:
			flash("No players found." , "danger")		
			
	if skaters == []:	
		skater_stats=''
	else:	
		skater_keys = yahoo_api.organize_player_keys(skaters)
		MY_PLAYERS_URL = YAHOO_BASE_URL + "players;player_keys=" + skater_keys + "/stats;date=2018"
		my_skater_stats = yahoo_api.yahoo_request(MY_PLAYERS_URL)
		# print("\n\nPlayers: " + str(skaters))
		# print("\n\nPlayer stats: " + str(my_skater_stats))
		skater_stats = yahoo_api.organize_stat_data(my_skater_stats)

	if goalies == []:
		goalie_stats = ''
	else:			
		goalie_keys = yahoo_api.organize_player_keys(goalies)
		MY_GOALIES_URL = YAHOO_BASE_URL + "players;player_keys=" + goalie_keys + "/stats;date=2018"
		my_goalie_stats = yahoo_api.yahoo_request(MY_GOALIES_URL)
		# print("\n\nGoalies: " + str(goalies))
		# print("\n\nGoalie URL: " + str(MY_GOALIES_URL))
		# print("\n\nGoalie stats: " + str(my_goalie_stats))
		# goalie_stats = my_goalie_stats
		goalie_stats = yahoo_api.organize_stat_data(my_goalie_stats)
	# except:
	# 	flash('No players found.', 'danger')
	# 	return '', '', '', ''

	return skaters, skater_stats, goalies, goalie_stats

def getPlayersFromDBAndYahoo(sortby, sortdir, position, player_search, offset):
	skaters, goalies = getDBPlayers(sortby, sortdir, position, player_search, offset)

	if skaters == []:	
		skater_stats = ''
		skater_info = ''
	else:	
		skater_keys = yahoo_api.organize_player_keys(skaters)
		skater_info = organizePlayerInfo(skater_keys)
		print("INFO: " + str(skater_info))

		MY_PLAYERS_URL = YAHOO_BASE_URL + "players;player_keys=" + skater_keys + "/stats;date=2018"
		my_skater_stats = yahoo_api.yahoo_request(MY_PLAYERS_URL)
		# print("\n\nPlayers: " + str(skaters))
		# print("\n\nPlayer stats: " + str(my_skater_stats))
		skater_stats = yahoo_api.organize_stat_data(my_skater_stats)
		# for skater in skater_info:
		# 	for skater_stat in skater_stats:
		# 		if skater_stat['player_id'] == skater['player_id']:
		# 			skater_stats.append(skater['position'])

	if goalies == []:
		goalie_stats = ''
		goalie_info = ''
	else:			
		goalie_info = organizePlayerInfo(goalies)
		goalie_keys = yahoo_api.organize_player_keys(goalies)
		MY_GOALIES_URL = YAHOO_BASE_URL + "players;player_keys=" + goalie_keys + "/stats;date=2018"
		my_goalie_stats = yahoo_api.yahoo_request(MY_GOALIES_URL)
		# print("\n\nGoalies: " + str(goalies))
		# print("\n\nGoalie URL: " + str(MY_GOALIES_URL))
		# print("\n\nGoalie stats: " + str(my_goalie_stats))
		# goalie_stats = my_goalie_stats
		goalie_stats = yahoo_api.organize_stat_data(my_goalie_stats)
	return skaters, skater_info, skater_stats, goalies, goalie_info, goalie_stats

		