from app import *
import db
# from models import emails
from models import pd
from models import status
from config import YAHOO_PLAYER_DB
import config
import json

class MakePickForm(BaseModel):
		player_id: int
		team_key: str


class UpdatePickForm(BaseModel):
		team_key: str
		overall_pick: int


class TogglePickForm(BaseModel):
		overall_pick: int


class AddNewPickForm(BaseModel):
		team_key: str


class CreateNewDraftForm(BaseModel):
		teams: list
		rounds: int
		team_order: list


def create_new_draft(user, teams, rounds, snake_draft, team_order):
	database = db.DB()
	delete_existing_draft_if_exists(database, user)
	yahoo_league_id = user['yahoo_league_id']
	sql = """
		INSERT INTO draft (yahoo_league_id, draft_start_time_utc, is_live, is_snake_draft, is_over, 
											rounds, per_pick, current_pick, keeper_total, keeper_goalies)
		VALUES (%s, '2023-09-16 13:00:00', 0, %s, 0, 
						%s, 1, 1, 10, 2)
		RETURNING draft_id;
	"""
	is_snake_draft = 1 if snake_draft is True else 0
	database.cur.execute(sql, (yahoo_league_id, is_snake_draft, rounds))
	draft_id_query = database.cur.fetchone()
	draft_id = draft_id_query[0]
	database.connection.commit()
	color_codes = ["#ffffff", "#33358c", "#6dbc69", "#000000", "#c80707", "#f85df9", "#4064f9", "#dc930c", "#99f2a3", "#b9f860", "#26d092", "#44aaaf"]

	set_users(database, user['yahoo_team_id'], teams, yahoo_league_id, color_codes)
	print("users set")
	set_draft_order(database, draft_id, yahoo_league_id, user['team_key'], team_order)
	print("draft order set")
	set_draft_picks(database, draft_id, rounds, snake_draft)
	print("draft picks set")
	set_updates_table(database, yahoo_league_id, draft_id)
	print("updates table set")

	if user['draft_id'] is not None:
		return {'success': True}

	new_web_token = replace_temp_token_with_web_token(user, draft_id, color_codes)
	return {'success': True, 'web_token': new_web_token}

def delete_existing_draft_if_exists(database, user):
	draft_id = user['draft_id']
	print(f"Deleting draft_id: {draft_id}")
	if draft_id is None:
		return
	else:
		try:
			sql = "DELETE FROM draft_order WHERE yahoo_league_id = %s"
			database.cur.execute(sql, (user['yahoo_league_id']))
			database.connection.commit()
			print("deleted draft_order")

			sql = "DELETE FROM draft_picks WHERE draft_id = %s"
			database.cur.execute(sql, (user['draft_id']))
			database.connection.commit()
			print("deleted draft_picks")

			sql = "DELETE FROM updates WHERE draft_id = %s"
			database.cur.execute(sql, (draft_id))
			database.connection.commit()
			print("deleted updates")

			sql = "DELETE FROM draft WHERE draft_id = %s"
			database.cur.execute(sql, (user['draft_id']))
			database.connection.commit()
			print("deleted draft")

			sql = "DELETE FROM users WHERE yahoo_league_id = %s"
			database.cur.execute(sql, (user['yahoo_league_id']))
			database.connection.commit()
			print("deleted users")

		except Exception as e:
			print(f"Error deleting draft: {e}")
		return

def set_users(database, yahoo_team_id, teams, yahoo_league_id, color_codes):
	sql = """
		INSERT INTO users(
			name, email, username, yahoo_league_id, yahoo_team_id, team_key, color, role
		)
		VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
	"""
	for team in teams:
		role = 'admin' if team['yahoo_team_id'] == yahoo_team_id else 'user'
		color = color_codes[int(team['yahoo_team_id']) - 1]
		database.cur.execute(sql, ( \
			team['user'], team['email'], team['team_name'], yahoo_league_id, team['yahoo_team_id'], team['team_key'], color, role \
		))
		database.connection.commit()
	return

def set_draft_order(database, draft_id, yahoo_league_id, team_key, team_order):
	sql = """
	INSERT INTO draft_order(draft_id, yahoo_league_id, draft_order, team_key)
	VALUES (%s, %s, %s, %s);
	"""
	team_key_base = team_key[0:team_key.rfind('.')+1]
	for team in team_order:
		database.cur.execute(sql, (draft_id, yahoo_league_id, team['order'], team_key_base + team['id']))
		database.connection.commit()
	return

def set_draft_picks(database, draft_id, rounds, snake):
	overall_pick_count = 1
	sql = "SELECT DISTINCT u.team_key, d.draft_order FROM draft_order d INNER JOIN users u ON d.team_key = u.team_key WHERE d.draft_id = %s ORDER BY draft_order;"
	user_count = database.cur.execute(sql, [draft_id])
	users = database.cur.fetchall()
	print("Setting picks...\n")
	for round in range(1, int(rounds) + 1):
		if snake == True:
			if (round > 1):
				# since the snake draft starts at the end of the round, this jumps it up a round
				overall_pick_count += user_count
				if round % 2 == 0:
					overall_pick_count -=1
				else:
					overall_pick_count +=1
		for user in users:
			sql = "INSERT INTO draft_picks(draft_id, team_key, overall_pick, round) VALUES(%s, %s, %s, %s)"
			database.cur.execute(sql, [draft_id, user[0], overall_pick_count, round])
			database.connection.commit()
			if (snake == True) and (round % 2 == 0):
				overall_pick_count -= 1
			else:
				overall_pick_count += 1

def set_updates_table(database, yahoo_league_id, draft_id):
	sql = """INSERT INTO updates(
						latest_draft_update, latest_team_update, latest_forum_update, latest_player_db_update,
						latest_rules_update, latest_goalie_db_update, yahoo_league_id, draft_id
					) 
						VALUES(%s, %s, %s, %s, %s, %s, %s, %s)
				"""
	now = str(datetime.datetime.utcnow())
	database.cur.execute(sql, (now, now, now, now, now, now, yahoo_league_id, draft_id))
	database.connection.commit()
	return
# def delete_league_and_picks(draft_id, yahoo_league_id):
# 	database = db.DB()
# 	sql = "DELETE FROM draft_order WHERE draft_id=%s"
# 	database.cur.execute(sql, draft_id)

# 	sql = "DELETE FROM draft_picks WHERE draft_id=%s"
# 	database.cur.execute(sql, draft_id)

# 	sql = "DELETE FROM user_team WHERE draft_id=%s"
# 	database.cur.execute(sql, draft_id)

# 	sql = "DELETE FROM updates WHERE draft_id=%s"
# 	database.cur.execute(sql, draft_id)

# 	sql = "DELETE FROM draft WHERE draft_id=%s"
# 	database.cur.execute(sql, draft_id)
# 	database.connection.commit()

# 	return {'success': True}


def get_draft(draft_id, team_key):
	database = db.DB()
	sql = """
			SELECT current_pick, 
			to_char(draft_start_time_utc, 'YYYY/MM/DD HH24:MI:SS') as draft_start_time_utc, 
			is_live, 
			is_snake_draft, 
			is_over
			FROM draft 
			WHERE draft_id = %s"""
	database.dict_cur.execute(sql, [draft_id])
	draft = database.dict_cur.fetchone()
	sql = f"""
			SELECT d.*, 
			u.yahoo_team_id, u.username, u.team_key, y.player_id, y.name AS player_name, y.prospect, y.careerGP, y.team, y.position, y.headshot
			FROM draft_picks d 
			INNER JOIN users u 
				ON u.team_key = d.team_key
		 	LEFT JOIN {YAHOO_PLAYER_DB} y 
				ON y.player_id = d.player_id 
			WHERE d.draft_id = %s
			ORDER BY overall_pick
		"""
	database.dict_cur.execute(sql, [draft_id])
	draft_picks = database.dict_cur.fetchall()
	current_pick = get_current_pick_info(draft['current_pick'], draft_id)
	database.dict_cur.execute("SELECT drafting_now FROM users WHERE team_key=%s", [team_key])
	result = database.dict_cur.fetchone()
	drafting_now = result['drafting_now']

	return {
		'success': True,
		'draft': draft,
		'drafting_now': drafting_now, 
		'picks': draft_picks,
		'current_pick': current_pick
	}

def get_all_users():
	database = db.DB()
	sql = "SELECT u.* FROM users u INNER JOIN draft d ON d.league_id = u.league_id \
						  WHERE u.league_id = %s AND d.draft_id=%s"
	database.cur.execute(sql, (session['league_id'], session['draft_id']))
	users = database.cur.fetchall()	
	return users

def change_pick(team_key, overall_pick, yahoo_league_id, draft_id):
	database = db.DB()
	now = datetime.datetime.utcnow()
	database.dict_cur.execute("SELECT * FROM draft_picks dp INNER JOIN users u ON u.team_key = dp.team_key \
					WHERE dp.overall_pick = %s AND draft_id=%s", (overall_pick, draft_id))
	old_user = database.dict_cur.fetchone()
	if old_user['drafting_now'] == True:
		# Make sure this user doesn't have any other active picks before settings drafting_now = True
		pick_check = database.dict_cur.execute("SELECT * FROM draft_picks WHERE draft_id = %s AND team_key = %s \
				AND pick_expires > %s AND overall_pick != %s AND player_id IS NULL",
					(draft_id, old_user['team_key'], now, overall_pick))
		if pick_check == 0:
			set_drafting_now(old_user['team_key'], False)

	database.cur.execute("UPDATE draft_picks SET team_key=%s WHERE overall_pick = %s AND draft_id=%s",
				(team_key, overall_pick, draft_id))
	database.connection.commit()

	util.update('latest_draft_update', draft_id)

	# check if the pick that was changed is the current pick - if it is, let the new user draft 
	database.dict_cur.execute("SELECT * FROM draft WHERE draft_id = %s", [draft_id])
	
	draft = database.dict_cur.fetchone()
	if overall_pick == draft['current_pick']:
		set_drafting_now(team_key, True)
	return util.return_true()

def toggle_pick_enabled(overall_pick, draft_id):
	database = db.DB()
	now = datetime.datetime.utcnow()
	database.dict_cur.execute("SELECT disabled FROM draft_picks WHERE overall_pick = %s AND draft_id=%s",
				(overall_pick, draft_id))	
	pick = database.dict_cur.fetchone()
	new_disabled_status = not pick["disabled"]
	database.cur.execute("UPDATE draft_picks SET disabled=%s WHERE overall_pick = %s AND draft_id=%s",
				(new_disabled_status, overall_pick, draft_id))
	database.connection.commit()

	# in case the current pick has just been disabled
	check_current_pick_in_draft(draft_id)
	util.update('latest_draft_update', draft_id)

	status = 'disabled' if new_disabled_status == True else 'enabled'

	return {'success': True, 'status': status}

def make_pick(draft_id, player_id, team_key):
	if check_if_taken(draft_id, player_id) == True:
		return return_error('This player has already been drafted.')
	pick = get_earliest_pick(draft_id, team_key)
	if pick is None:
		return return_error('You have no remaining picks.')
	commit_pick(draft_id, player_id, team_key, pick['overall_pick'])
	next_pick = check_next_pick(draft_id, pick['overall_pick'])
	if next_pick is None:
		set_drafting_now(team_key, False)
		return {
			"success": True, 
			"player": None, 
			"next_pick": None, 
			"drafting_again": False
		}
	if team_key == next_pick['team_key']:
		drafting_again = True
	else:
		drafting_again = False
		set_drafting_now(team_key, False)
		set_drafting_now(next_pick['team_key'], True)
		email_success = pd.pd_incident(next_pick['service_id'])
		if email_success != True:
			print(f"Error in pd_incident for user {next_pick['team_key']} with service ID {next_pick['service_id']}")
		# emails.next_pick_email(next_pick['email'])
	player_data = get_one_player_from_db(player_id)
	player = []
	player.extend((player_data['name'], ' ' + player_data['position'], ' ' + player_data['team']))
	return {'success': True, 'player': player, 'next_pick': next_pick, 'drafting_again': drafting_again}

def check_if_taken(draft_id, player_id):
	database = db.DB()
	sql = "SELECT player_id FROM user_team WHERE draft_id = %s AND player_id = %s"
	database.cur.execute(sql, (draft_id, player_id))
	result = database.cur.fetchone()
	print(f"result: {result}")
	if result is None:
		return False
	return True

def get_one_player_from_db(player_id):
	database = db.DB()
	sql = f"SELECT * FROM {YAHOO_PLAYER_DB} WHERE player_id = %s"
	database.dict_cur.execute(sql, [player_id])
	return database.dict_cur.fetchone()	

def get_earliest_pick(draft_id, team_key):
	database = db.DB()
	sql = """ SELECT d.*, u.name, u.email
			FROM draft_picks d
			INNER JOIN users u ON u.team_key = d.team_key
			WHERE player_id IS NULL
			AND d.draft_id = %s
			AND d.team_key = %s
			AND (d.disabled IS FALSE OR d.disabled IS NULL)
			ORDER BY d.overall_pick ASC
		"""
	database.dict_cur.execute(sql, (draft_id, team_key))
	return database.dict_cur.fetchone()

def commit_pick(draft_id, player_id, team_key, pick):
	database = db.DB()
	sql = """ UPDATE draft_picks
			SET player_id = %s, draft_pick_timestamp = %s
			WHERE overall_pick = %s
			AND draft_id = %s
	"""
	now = datetime.datetime.utcnow()
	database.cur.execute(sql, (player_id, now, pick, draft_id))
	database.connection.commit()
	sql = """ INSERT INTO user_team(draft_id, team_key, is_keeper, player_id)
			VALUES (%s, %s, 0, %s)
	"""
	database.cur.execute(sql, (draft_id, team_key, player_id))
	database.connection.commit()
	sql = """ UPDATE updates 
			SET latest_draft_update = %s, latest_team_update = %s, latest_player_db_update = %s, latest_goalie_db_update = %s
			WHERE draft_id = %s
	"""
	print(f"updating draft, team, db to now: {now}")
	database.cur.execute(sql, (now, now, now, now, draft_id))
	database.connection.commit()
	return util.return_true()

def check_next_pick(draft_id, pick):
	database = db.DB()
	sql = """ SELECT *
			FROM draft_picks d
			INNER JOIN users u ON u.team_key = d.team_key
			WHERE draft_id = %s
			AND overall_pick > %s
			AND disabled IS NOT TRUE
			ORDER BY overall_pick
		"""
	remainingPicks = database.dict_cur.execute(sql, (draft_id, pick))
	nextPick = database.dict_cur.fetchone()
	if nextPick is None:
		print("nextPick is none")
		check_current_pick_in_draft(draft_id)
	else:	
		print("Next pick: " + str(nextPick))
		if nextPick['pick_expires'] is None:
			sql = "UPDATE draft_picks d SET pick_expires = %s WHERE draft_pick_id = %s"
			now = datetime.datetime.utcnow()
			current_hour_utc = now.strftime("%H")

			# if the pick is made overnight (10pm to 9am ET), set the new pick expiry to the next day at 1pm ET
			if 2 <= int(current_hour_utc) < 13:
				pick_expiry = datetime.datetime(now.year, now.month, now.day, 17, 0, 0)
			else:
				pick_expiry = datetime.datetime.utcnow() + datetime.timedelta(hours = 4)
			database.cur.execute(sql, (pick_expiry, nextPick['draft_pick_id']))
			database.connection.commit()
			sql = "UPDATE draft SET current_pick=%s WHERE draft_id=%s"
			print("Query 2: " + str(sql))
			database.cur.execute(sql, (nextPick['overall_pick'], draft_id))
			database.connection.commit()
	return nextPick

def set_drafting_now(team_key, value):
	database = db.DB()
	sql = """
		UPDATE users
		SET drafting_now = %s
		WHERE team_key = %s
	"""
	database.cur.execute(sql, (value, team_key))
	database.connection.commit()
	return

def get_current_pick_info(pick, draft_id):
	database = db.DB()
	sql = "SELECT * FROM users u INNER JOIN draft_picks dp ON dp.team_key = u.team_key \
			WHERE dp.overall_pick = %s AND dp.draft_id = %s"

	database.dict_cur.execute(sql, (pick, draft_id))	
	current_pick = database.dict_cur.fetchone()
	return current_pick

def check_current_pick_in_draft(draft_id):
	database = db.DB()
	sql = """SELECT *
			FROM draft_picks d
			INNER JOIN users u ON u.team_key = d.team_key
			WHERE draft_id = %s
			AND pick_expires is NOT NULL
			AND player_id IS NULL
			AND disabled IS FALSE
			ORDER BY overall_pick DESC
		"""
	database.dict_cur.execute(sql, [draft_id])
	current_pick = database.dict_cur.fetchone()
	print("current: " + str(current_pick))
	if current_pick is None:
		sql = "UPDATE draft SET is_live=%s, is_over=%s WHERE draft_id=%s"
		database.cur.execute(sql, (0, 1, draft_id))
	else:
		sql = "UPDATE draft SET current_pick=%s WHERE draft_id=%s"
		pick = current_pick['overall_pick']
		print(f"pick: {pick}")
		database.cur.execute(sql, (pick, draft_id))
	database.connection.commit()
	return	

def add_pick_to_draft(draft_id, yahoo_league_id, team_key):
	database = db.DB()
	sql = """SELECT MAX(overall_pick) AS "last_pick"
		FROM draft_picks d
		WHERE draft_id = %s
	"""
	database.dict_cur.execute(sql, [draft_id])
	last_pick = database.dict_cur.fetchone()
	new_pick = last_pick['last_pick'] + 1
	sql = f"""
		INSERT INTO draft_picks(draft_id, round, overall_pick, team_key)
		VALUES(%s, %s, %s, %s)
	"""
	database.cur.execute(sql, (draft_id, 15, new_pick, team_key))
	database.connection.commit()

	util.update('latest_draft_update', draft_id)
	return util.return_true()
