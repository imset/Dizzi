from os.path import isfile
from sqlite3 import connect, OperationalError
from apscheduler.triggers.cron import CronTrigger
import ast
import re
import emojis

DB_PATH = "./data/db/database.db"
BUILD_PATH = "./data/db/build.sql"

cxn = connect(DB_PATH, check_same_thread=False)
cur = cxn.cursor()

def with_commit(func):
    def inner(*args, **kwargs):
        func(*args, **kwargs)
        commit()
    return inner
    
@with_commit
def build():
    if isfile(BUILD_PATH):
        scriptexec(BUILD_PATH)

def commit():
    cxn.commit()
    
def autosave(sched):
    sched.add_job(commit, CronTrigger(second=0))
    
def close():
    cxn.close()
    
def field(command, *values):
    cur.execute(command, tuple(values))
    if (fetch := cur.fetchone()) is not None:
        return fetch[0]
    
def record(command, *values):
    cur.execute(command, tuple(values))
    return cur.fetchone()

def records(command, *values):
    cur.execute(command, tuple(values))
    return cur.fetchall()
    
def column(command, *values):
    cur.execute(command, tuple(values))
    return [item[0] for item in cur.fetchall()]
    
def execute(command, *values):
    cur.execute(command, tuple(values))

def multiexec(command, valueset):
    cur.executemany(command, valueset)
    
def scriptexec(path):
    with open(path, "r", encoding="utf-8") as script:
        cur.executescript(script.read())

#custom - try to add a column
def addcolumn(table, column, dflt):
    try:
        cur.execute(f"ALTER TABLE {table} ADD COLUMN `{column}` int DEFAULT {dflt}")
    except:
        pass

#custom - returns the user's emote dictionary for the emoji tracking system
'''
def emotedict(userid, guildid) -> dict:
    uguild = f"{userid}.{guildid}"
    userredict = ast.literal_eval(db.field("SELECT reactiondict FROM reactioncounter WHERE UserGuildID = ?", uguild))
    return userredict
'''