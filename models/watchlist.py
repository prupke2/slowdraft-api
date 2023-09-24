from app import *
from config import *
from db import *

class WatchlistForm(BaseModel):
		player_id: int

def get_watchlist_ids(yahoo_league_id, team_key):
	database = db.DB()
	sql = f"""
		SELECT w.player_id 
		FROM watchlist w 
		INNER JOIN {YAHOO_PLAYER_DB} y 
			ON y.player_id = w.player_id 
		WHERE yahoo_league_id = %s 
		AND team_key = %s
	"""
	database.cur.execute(sql, (yahoo_league_id, team_key))
	players = database.cur.fetchall()

	watchlist = []
	for player in players:
		watchlist.append(player[0])
	return {'success': True, 'players': watchlist}

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
