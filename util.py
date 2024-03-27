import db
import datetime
import config
import os

def return_true():
    return {"success": True}


def return_error(message, status=400):
    return {
        "success": False,
        "error": message,
        "status": status
    }


def update(table, draft_id):
    database = db.DB()
    query = f""" UPDATE updates
		SET {table} = %s
		WHERE draft_id = %s
	"""
    database.cur.execute(query, (datetime.datetime.utcnow(), draft_id))
    database.connection.commit()
    return


def get_last_row_inserted(table, column):
    database = db.DB()
    database.cur.execute(f"SELECT MAX({column}) FROM {table};")
    max = database.cur.fetchone()
    return max[f'MAX({column})']


def set_config():
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
