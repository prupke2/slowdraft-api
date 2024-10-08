from app import *
from oauth.yahoo_oauth import *
import config
import requests
import xmltodict
import json
import oauth.yahoo_oauth
import util
import os

def yahoo_request(url, access_token=None, refresh_token=None, useJson=False):
    # pass in a Yahoo fantasy sports URL here
    token = config.access_token if config.access_token else access_token
    # print(f"token: {token}")
    refresh_token = config.refresh_token if config.refresh_token else refresh_token
    # print(f"refresh_token: {refresh_token}")
    header = "Bearer " + token
    url = url if useJson is False else url + '?format=json'
    print(f"Attempting to reach URL: {url}")
    response = requests.get(url, headers={'Authorization': header})

    if response.status_code == 200:
        print("Success! \n")
        if not useJson:
            return xmltodict.parse(response.content)
        else:
            return json.loads(response.content)
    # a 401 response is expected if the access token has expired.
    # if this happens, use the refresh token to get a new one
    elif response.status_code == 401 and (b"token_expired" or b"Invalid cookie" in response.content):
        print("Token Expired. Attempting to renew using refresh token.")
        refresh_attempts = 0
        # attempt to get a new token 3 times
        while refresh_attempts < 3:
            refresh_attempts += 1
            print("Attempt # " + str(refresh_attempts))
            attempt = oauth.yahoo_oauth.refresh_access_token(
                refresh_token, os.environ['client_id'], os.environ['client_secret'], os.environ['redirect_uri'])
            if attempt['success']:
                break
        # give up after 3 tries
        if not attempt['success']:
            return attempt
        # if refresh token is obtained, call the function again as it should work
        # now
        print("Success!")
        return yahoo_request(url, token, refresh_token, useJson)
    elif response.status_code == 400 and b"INVALID_REFRESH_TOKEN" in response.content:
        print("HERE")
        return response
    else:
        print("HTTP Code: %s" % response.status_code)
        print("HTTP Response: \n%s" % response.content)
        return response


def organize_player_info(player_keys):
    LEAGUE_URL = YAHOO_BASE_URL + "league/" + \
        os.environ['league_key'] + "/players;player_keys=" + player_keys
    players = []
    player_query = yahoo_request(LEAGUE_URL)
    if not player_query:
        return util.return_error("token_error")
    try:
        for player in player_query['fantasy_content']['league']['players']['player']:
            player_data = {}
            player_data['player_id'] = player['player_id']
            player_data['player_key'] = str(player['player_key'])
            player_data['name'] = player['name']['full']
            player_data['team'] = player['editorial_team_abbr']
            player_data['position'] = player['eligible_positions']
            players.append(player_data)
    except BaseException:
        player_data = {}
        try:
            player_data['player_id'] = player_query['fantasy_content']['league']['players']['player']['player_id']
            player_data['player_key'] = str(
                player_query['fantasy_content']['league']['players']['player']['player_key'])
            player_data['name'] = player_query['fantasy_content']['league']['players']['player']['name']['full']
            player_data['team'] = player_query['fantasy_content']['league']['players']['player']['editorial_team_abbr']
            player_data['position'] = player_query['fantasy_content']['league']['players']['player']['eligible_positions']['position']
            players.append(player_data)
        except BaseException:
            return []
    return players


def get_yteam(team_id):
    TEAM_URL = f"https://fantasysports.yahooapis.com/fantasy/v2/team/{os.environ['league_key']}.t.10"
    team_query = yahoo_request(TEAM_URL)
    print(f"team_query: {team_query}")
    return {team_query: team_query}


def add_player_analysis_data(player_stats, players):
    # takes an existing list of player stats and appends analysis stats to it
    analysis_data = []
    count = players['fantasy_content']['players']['count']
    try:
        for index in range(count):
            current_player_stats = player_stats[index]
            
            player_data = players['fantasy_content']['players'][f'{index}']
            player_id = player_data['player'][0][1]['player_id']
            player_analysis = player_data['player'][1]
            
            average_pick = player_analysis['draft_analysis'][0]['average_pick']
            percent_drafted = player_analysis['draft_analysis'][3]['percent_drafted']
            
            stat_data_average_pick = {
                'stat_id': 'average_pick',
                'player_id': player_id,
                'value': average_pick
            }
            analysis_data.append(stat_data_average_pick)

            stat_data_percent_drafted = {
                'stat_id': 'percent_drafted',
                'player_id': player_id,
                'value': percent_drafted
            }

            analysis_data.append(stat_data_percent_drafted)

    except BaseException as err:
        print(f'Error in add_player_analysis_data function: {err}')
        return []

    return analysis_data


def organize_stat_data(stats):
    # creates new arrays to hold all player stats
    # players = []
    player_stats = []
    # print("\n\nSTATS RECEIVED: " + str(stats))

    try:
        for stat_set in stats['fantasy_content']['players']['player']:
            # print("\n\nSTAT SET: " + str(stat_set))
            stat_list = stat_set['player_stats']['stats']['stat']

            for stat in stat_list:
                # creates a temporary dictionary for each player's stats which
                # is appended to player_stats[] after each loop
                stat_data = {}
                stat_data['stat_id'] = stat['stat_id']
                stat_data['value'] = stat['value']
                stat_data['player_id'] = stat_set['player_id']

                if stat_set['position_type'] == 'G':
                    stat_index = config.GOALIE_STAT_INDEX
                else:
                    stat_index = config.SKATER_STAT_INDEX
                    # stat_data['stat'] = 'GOALIE'
                for key in stat_index:
                    if key == str(stat_data['stat_id']):
                        stat_data['stat'] = stat_index[key]
                        player_stats.append(stat_data)
    except BaseException:  # this is performed if there is only one result.
        for stat in stats['fantasy_content']['players']['player']['player_stats']['stats']['stat']:
            # creates a temporary dictionary for each player's stats which is
            # appended to player_stats[] after each loop
            stat_data = {}
            stat_data['stat_id'] = stat['stat_id']
            stat_data['value'] = stat['value']
            stat_data['player_id'] = stats['fantasy_content']['players']['player']['player_id']
            if stats['fantasy_content']['players']['player']['position_type'] == 'G':
                stat_index = config.GOALIE_STAT_INDEX
            else:
                stat_index = config.SKATER_STAT_INDEX
            for key in stat_index:
                if key == str(stat_data['stat_id']):
                    stat_data['stat'] = stat_index[key]
                    player_stats.append(stat_data)

    return player_stats


def organize_player_keys(players):
    keys = ""
    # loops through each player key, separates them with commas, and concatenates them into a string
    # this is the required format to query multiple players in yahoo's API
    for key in players:
        keys += str(key['player_key'])
        keys += ","
    keys = keys[:-1]  # removes the last comma from the end
    return keys


def check_if_prospect(id):
    print("ID: " + str(id))
    database = db.DB()
    sql = f"SELECT prospect, careerGP, NHLid FROM {YAHOO_PLAYER_DB} WHERE player_id = %s"
    database.cur.execute(sql, [str(id)])
    player = database.cur.fetchone()
    # print(str(result))
    # print("prospect: " + str(prospect) + "\ncareerGP: " + str(careerGP))
    return player['prospect'], player['careerGP'], player['NHLid']
