from app import *
from config import *
from db import *

class WatchlistForm(BaseModel):
		player_id: int

class AutodraftForm(BaseModel):
		player_id: int
		action: str

def get_watchlist_ids(yahoo_league_id, team_key):
	database = db.DB()
	sql = f"""
		SELECT w.player_id, w.autodraft
		FROM watchlist w 
		INNER JOIN {YAHOO_PLAYER_DB} y 
			ON y.player_id = w.player_id 
		WHERE yahoo_league_id = %s 
		AND team_key = %s
	"""
	database.cur.execute(sql, (yahoo_league_id, team_key))
	players = database.cur.fetchall()

	watchlist = []
	autodraft_list = []
	for player in players:
		if player[1] == True:
			autodraft_list.append((player[0]))
		else:
			watchlist.append(player[0])
	return {'success': True, 'players': watchlist, 'autodraft_list': autodraft_list}

def add_player_to_watchlist(yahoo_league_id, team_key, player_id):
	database = db.DB()
	sql = "INSERT INTO watchlist(yahoo_league_id, team_key, player_id) VALUES(%s, %s, %s)"
	print(sql)
	database.cur.execute(sql, (yahoo_league_id, team_key, player_id))
	database.connection.commit()
	return util.return_true()

def remove_player_from_watchlist(yahoo_league_id, team_key, player_id):
	database = db.DB()
	sql = "DELETE FROM watchlist WHERE yahoo_league_id = %s AND team_key = %s AND player_id = %s"
	print(sql)
	database.cur.execute(sql, (yahoo_league_id, team_key, player_id))
	database.connection.commit()
	return util.return_true()

def toggle_player_on_watchlist(yahoo_league_id, team_key, player_id, action):
	database = db.DB()
	sql = "UPDATE watchlist SET autodraft = %s WHERE yahoo_league_id = %s AND team_key = %s AND player_id = %s"
	status = action == "add"
	database.cur.execute(sql, (status, yahoo_league_id, team_key, player_id))
	database.connection.commit()
	return util.return_true()
