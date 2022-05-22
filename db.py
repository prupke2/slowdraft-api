import os
import pymysql.cursors
import config
import app


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
