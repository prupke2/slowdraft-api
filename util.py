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

def valid_2XX_response(response):
    return response.status_code >= 200 and response.status_code <= 203

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
