from app import * 
import datetime
import db
from util import return_error


class ForumPostForm(BaseModel):
		id: Union[int, None]
		parent_id: Union[int, None]
		title: Union[str, None]
		body: str


def get_forum_posts(yahoo_league_id):	
	sql = """
		SELECT f.id, f.title, f.body, f.yahoo_team_id, f.team_key, f.create_date, f.update_date,
				u.username, u.role, u.color
		FROM forum f 
				INNER JOIN users u on u.yahoo_league_id = f.yahoo_league_id
		WHERE f.parent_id IS NULL
				AND f.yahoo_league_id = %s
				AND f.team_key = u.team_key
		ORDER BY update_date DESC
		"""

	database = db.DB()
	database.dict_cur.execute(sql, [yahoo_league_id])
	posts = database.dict_cur.fetchall()
	for post in posts:
		post['create_date'] = post['create_date'] - datetime.timedelta(minutes=int(float(0)))
		post['update_date'] = post['update_date'] - datetime.timedelta(minutes=int(float(0)))
	return {'success': True, 'posts': posts}

def get_forum_post(id):
	sql = "SELECT * FROM forum WHERE id = %s"	
	database = db.DB()
	database.dict_cur.execute(sql, [id])
	return {'success': True, 'post': database.dict_cur.fetchone()}

def get_post_replies(yahoo_league_id, post_id):
	database = db.DB()
	sql = """
		SELECT f.id, f.parent_id, f.create_date, f.update_date, f.body, f.title, f.team_key, u.yahoo_team_id, u.username, u.color
		FROM forum f 
		LEFT JOIN users u 
		ON u.team_key = f.team_key 
		WHERE f.yahoo_league_id=%s
		AND f.parent_id=%s
		 
	"""
	database.dict_cur.execute(sql, [yahoo_league_id, post_id])
	replies = database.dict_cur.fetchall()
	if replies is False:
		replies = []
	else:
		for reply in replies:
			reply['create_date'] = reply['create_date'] - datetime.timedelta(minutes=int(float(0)))
			reply['update_date'] = reply['update_date'] - datetime.timedelta(minutes=int(float(0)))
	return {"success": True, 	"id": post_id, "replies": replies }

def new_forum_post(post, user):
	now = datetime.datetime.utcnow()
	sql = "INSERT INTO forum(title, body, team_key, yahoo_league_id, create_date, update_date, parent_id, yahoo_team_id) \
			VALUES(%s, %s, %s, %s, %s, %s, %s, %s)"

	database = db.DB()
	database.cur.execute(sql, (post.title, post.body, user['team_key'], user['yahoo_league_id'], \
		now, now, post.parent_id, user['yahoo_team_id']))
	database.connection.commit()
	util.update('latest_forum_update', user['draft_id'])

	if post.parent_id is not None:
		update_parent_timestamp(post.parent_id)
	return util.return_true()

def update_forum_post(user, post):
	database = db.DB()
	sql = "UPDATE forum SET title=%s, body=%s, update_date = %s WHERE id=%s"
	database.cur.execute(sql, (post.title, post.body, datetime.datetime.utcnow(), post.id))
	database.connection.commit()
	if post.parent_id is not None:
		update_parent_timestamp(post.parent_id)

	util.update('latest_forum_update', user['draft_id'])
	return util.return_true()

def update_parent_timestamp(parent_id):
	database = db.DB()
	sql = "UPDATE forum SET update_date=%s WHERE id=%s"
	database.cur.execute(sql, (datetime.datetime.utcnow(), parent_id))
	database.connection.commit()
	return util.return_true()

def delete_forum_post(id):
	database = db.DB()
	sql = "DELETE FROM forum where id=%s"
	database.cur.execute(sql, id)	
	database.connection.commit()

	util.update('latest_forum_update', user['draft_id'])
	return util.return_true()   
