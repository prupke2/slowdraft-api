from app import *
import db
import config
import os

def get_url(user):
	if user['yahoo_league_id'] == os.environ['yahoo_league_id']:
		return {'success': True, 'url': os.environ['url']}
	return util.return_error('There is no doc for this league.')
