" tell.py: written by sklnd in July 2009"
"       2010.01.25 - modified by Scaevolus"

import time

from util import hook, timesince


def db_init(db):
    "check to see that our db has the tell table and return a dbection."
    db.execute("create table if not exists tell"
               "(user_to, user_from, message, chan, time,"
               "primary key(user_to, message))")
    db.commit()

    return db


def get_tells(db, user_to):
    return db.execute("select user_from, message, time, chan from tell where"
                      " user_to=lower(?) order by time",
                      (user_to.lower(),)).fetchall()


@hook.singlethread
@hook.event('PRIVMSG')
def tellinput(paraml, input=None, pm=None, db=None):
    db_init(db)

    tells = get_tells(db, input.nick)

    if not tells:
        return

    for tell in tells:
        user_from, message, time, chan = tell
        past = timesince.timesince(time)

        reply = "%s said %s ago in %s: %s" % (user_from, past, chan, message)

        pm(reply)

    db.execute("delete from tell where user_to=lower(?)", (input.nick))
    db.commit()

@hook.command('note')
@hook.command
def tell(inp, nick='', chan='', db=None, conn=None, bot=None):
    ".tell <nick> <message> -- relay <message> to <nick> when <nick> is around"

    query = inp.split(' ', 1)

    if len(query) != 2:
        return tell.__doc__

    user_to = query[0].lower()
    message = query[1].strip()
    user_from = nick

    if chan.lower() == user_from.lower():
        chan = 'a pm'

    if user_to == user_from.lower():
        return "You can't send a message to yourself."

    db_init(db)

    queue_limit = bot.config.get('tell_limit', 5)

    if db.execute("select count() from tell where user_to=?",
                  (user_to,)).fetchone()[0] >= queue_limit:
        return "That person has too many things queued."

    try:
        db.execute("insert into tell(user_to, user_from, message, chan,"
                   "time) values(?,?,?,?,?)", (user_to, user_from, message,
                                               chan, time.time()))
        db.commit()
    except db.IntegrityError:
        return "Message has already been queued."

    return "I'll pass that along."
