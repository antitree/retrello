from trello import TrelloClient
from trello import ResourceUnavailable
import sqlite3
import time
import datetime
import json


## STRUCT of card with plus builtin

# Import json tasklist for repeating
# frequency, board, list, name, description, estimation, due-date, assigned

# check what cards need to be repeated
DEBUG = False

def main():
    # Check SQLite DB for records
    # select * from db where time < time+(freq)
    conn, cur = db_setup()
    results = cur.execute('SELECT name FROM sqlite_master WHERE type="table"')
    boards = results.fetchall()
    conn.close()
    for b in boards:
        board = b[0]
        conn, cur = db_setup()
        results = cur.execute('SELECT * FROM ' + board)
        records = results.fetchall()
        conn.close()
        # if last_time < frequency then make new card
        current = time.time()
        #print(current)
        day = 8640000
        week = day * 7
        month = day * 30
        for record in records:
            card = set_card(record)
            if card["freq"] == "Daily" and card["last"] < (current - day):
                card["due"] = datetime.datetime.now() + datetime.timedelta(days=1)
                add_card(card, board)
            elif card["freq"] == "Weekly" and card["last"] < (current - week):
                card["due"] = datetime.datetime.now() + datetime.timedelta(days=7)
                add_card(card, board)
            elif card["freq"] == "Monthly" and card["last"] < (current - month):
                card["due"] = datetime.datetime.now() + datetime.timedelta(days=30)
                add_card(card, board)
            elif DEBUG:
                card["due"] = datetime.datetime.now() + datetime.timedelta(days=60)
                add_card(card,board)
            else:
                print("%s: Does not need adding" % card["name"])
    conn.close()

def set_card(record):
    card = dict()
    if DEBUG:
        card["list"] = "TestList"
    else:
        card["list"] = record[0]
    card["name"] = record[1]
    card["desc"] = record[2]
    card["freq"] = record[3]
    card["last"] = record[4]
    card["plus"] = record[5]
    card["due"] = None
    return card

def add_card(card, board):
    client = trello_auth()
    try:
        tboard = next(x for x in client.list_boards() if x.name == board)
        print(tboard.id)
    except ResourceUnavailable as err:
        print(err)
        print("Sleeping")
        for i in range(15):
            print('.'),
            time.sleep(1)
        return False

    try:
        tlist = next(x for x in tboard.all_lists() if x.name == card["list"])
    except ResourceUnavailable as err:
        print(err)
        print("Sleeping")
        for i in range(15):
            print('.'),
            time.sleep(1)
        return False
    if card["due"]:
        newdue = card["due"].strftime("%Y-%m-%d")
    else:
        newdue = "null"
    print newdue

    try:
        newcard = tlist.add_card(card["name"], desc=card["desc"],due=newdue)
    except ResourceUnavailable as err:
        print(err)
        print("Sleeping")
        for i in range(15):
            print('.'),
            time.sleep(1)
        return False

    try:
        newcard.comment(card["plus"])
        if DEBUG:
            delete_card(newcard)
    except ResourceUnavailable as err:
        print(err)
        print("Sleeping")
        for i in range(15):
            print('.'),
            time.sleep(1)
        return False
    print("Card added...")
    update_last(card, board)
    return True

def delete_card(card):
    card.set_closed(True)

def update_last(card, board):
    conn, cur = db_setup()
    newtime = time.time()
    sql = 'UPDATE ' + board + ' SET Last=? WHERE List=? AND Name=? AND Desc=?'
    cur.execute(sql, (newtime, card["list"], card["name"], card["desc"]))
    conn.commit()
    conn.close()


def db_setup():
    conn = sqlite3.connect('retrello.db')
    cur = conn.cursor()
    return conn, cur


def trello_auth():
    try:
        f = open("CREDS", 'r')
    except:
        print("Missing CREDS file")
    creds = json.load(f)
    client = TrelloClient(
        api_key=creds["api_key"],
        api_secret=creds["api_secret"],
        token=creds["oauth_token"],
        token_secret=creds["oauth_token_secret"])
    return client

if __name__ == '__main__':
    main()
