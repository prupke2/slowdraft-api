import os
import pymysql.cursors
import config
import app

# Comment out the lines below when scraping
# import credentials
# config.host, config.user, config.password, config.db = credentials.get_local_DB()
# config.league_key = credentials.game_key + ".l." + credentials.yahoo_league_id
# config.yahoo_league_id = credentials.yahoo_league_id
# config.league_id = credentials.league_id
# config.draft_id = credentials.draft_id
# config.client_id = credentials.consumer_key
# config.client_secret = credentials.consumer_secret
# config.redirect_uri = "oob"

class DB(object):

    def __init__(self):
        self.connection = pymysql.connect(
            host=config.host,
            user=config.user,
            password=config.password,
            database=config.db,
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        self.cur = self.connection.cursor()
