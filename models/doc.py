from app import *
import db
import config

def get_url(user):
	if user['yahoo_league_id'] == config.yahoo_league_id:
		return {'success': True, 'url': config.url}
	return util.return_error('There is no doc for this league.')
