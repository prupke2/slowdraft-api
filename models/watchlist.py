from app import *
from config import *
from db import *

class WatchlistForm(BaseModel):
		player_id: int

def get_watchlist():
	database = db.DB()
	sql = f"SELECT DISTINCT w.player_id, y.* FROM watchlist w INNER JOIN {YAHOO_PLAYER_DB} y ON y.player_id = w.player_id \
			WHERE yahoo_league_id = %s AND user_id = %s"
	database.cur.execute(sql, (session['yahoo_league_id'], session['user_id']))
	players = database.cur.fetchall()
	skaters = []
	goalies = []
	for player in players:
		if player['position'] == "G":
			goalies.append(player)
		else:
			skaters.append(player)
			
	return skaters, goalies

def get_watchlist_ids():
	database = db.DB()
	sql = f"SELECT w.player_id FROM watchlist w INNER JOIN {YAHOO_PLAYER_DB} y ON y.player_id = w.player_id WHERE yahoo_league_id = %s AND user_id = %s"
	database.cur.execute(sql, (session['yahoo_league_id'], session['user_id']))
	players = database.cur.fetchall()
	print("\n\nPlayers: " + str(players))
	watchlist = []
	for player in players:
		watchlist.append(player['player_id'])
		
	return watchlist

def add_player_to_watchlist(yahoo_league_id, team_key, player_id):
	database = db.DB()
	sql = "INSERT INTO watchlist(yahoo_league_id, user_id, player_id) VALUES(%s, %s, %s)"
	print(sql)
	database.cur.execute(sql, (session['yahoo_league_id'], session['user_id'], id))
	database.connection.commit()
	# return True

def remove_player_from_watchlist(yahoo_league_id, team_key, player_id):
	database = db.DB()
	sql = "DELETE FROM watchlist WHERE yahoo_league_id = %s AND user_id = %s AND player_id = %s"
	print(sql)
	database.cur.execute(sql, (session['yahoo_league_id'], session['user_id'], id))
	database.connection.commit()
