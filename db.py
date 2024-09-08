import os
import config
import app
import psycopg2
import psycopg2.extras

# Uncomment out the lines below when scraping
# import credentials
# os.environ['POSTGRES_HOST'], os.environ['POSTGRES_USER'], os.environ['POSTGRES_PASSWORD'], os.environ['POSTGRES_DATABASE'] = credentials.get_local_DB()
# config.league_key = credentials.game_key + ".l." + credentials.yahoo_league_id
# os.environ['yahoo_league_id'] = credentials.yahoo_league_id
# os.environ['draft_id'] = credentials.draft_id
# os.environ['client_id'] = credentials.consumer_key
# os.environ['client_secret'] = credentials.consumer_secret
# os.environ['redirect_uri'] = "oob"

class DB(object):

    def __init__(self):
        self.connection = psycopg2.connect(
            host=os.environ['POSTGRES_HOST'],
            user=os.environ['POSTGRES_USER'],
            password=os.environ['POSTGRES_PASSWORD'],
            database=os.environ['POSTGRES_DATABASE']
        )
        self.cur = self.connection.cursor()
        self.dict_cur = self.connection.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
