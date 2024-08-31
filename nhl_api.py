from app import *
from db import *

def get_nhl_id_from_db(player_id):
    # TODO: build a replacement for getting nhl_id from nhl's api
    database = db.DB()
    sql = "SELECT nhl_id FROM yahoo_db_23_24 WHERE player_id = %s"
    database.cur.execute(sql, [player_id])
    player = database.cur.fetchone()
    if player:
        return player[0]
    return None

def get_career_gp(nhl_id):
    PLAYER_DATA_ENDPOINT = f"https://api-web.nhle.com/v1/player/{nhl_id}/landing"
    response = requests.get(PLAYER_DATA_ENDPOINT)

    if response.status_code >= 200 and response.status_code <= 203:
        result = response.json()        
        if "careerTotals" in result:
            if "regularSeason" in result["careerTotals"]:
                if "gamesPlayed" in result["careerTotals"]["regularSeason"]:
                    return result["careerTotals"]["regularSeason"]["gamesPlayed"]
    return None
