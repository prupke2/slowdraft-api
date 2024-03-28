import os
import config
import app
import psycopg2
import psycopg2.extras

# Uncomment out the lines below when scraping
# import credentials
# config.host, config.user, config.password, config.db = credentials.get_local_DB()
# config.league_key = credentials.game_key + ".l." + credentials.yahoo_league_id
# os.environ['yahoo_league_id'] = credentials.yahoo_league_id
# config.league_id = credentials.league_id
# os.environ['draft_id'] = credentials.draft_id
# os.environ['client_id'] = credentials.consumer_key
# os.environ['client_secret'] = credentials.consumer_secret
# os.environ['redirect_uri'] = "oob"

class DB(object):

    def __init__(self):
        self.connection = psycopg2.connect(
            host=os.environ['host'],
            user=os.environ['user'],
            password=os.environ['password'],
            database=os.environ['db']
        )
        self.cur = self.connection.cursor()
        self.dict_cur = self.connection.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
