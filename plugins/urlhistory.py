import math
import time

from util import hook, urlnorm, timesince, http

title_length = 80

expiration_period = 60 * 60 * 24  # 1 day

ignored_urls = [urlnorm.normalize("http://google.com")]

# We have a bunch of much better plugins to handle these
ignored_title_urls = [
    'vine.co/',
    'reddit.com',
    'imdb.com',
    'liveleak.com',
    'twitter.com',
    'youtube.com',
    'vimeo.com',
    'tinyurl.com',
    'rottentomatoes.com',
    'steampowered.com',
    'steamcommunity.com',
    '//t.co',
    'youtu.be/',
    'yooouuutuuube'
]

def db_init(db):
    db.execute("create table if not exists urlhistory"
               "(chan, url, nick, time)")
    db.commit()


def insert_history(db, chan, url, nick):
    db.execute("insert into urlhistory(chan, url, nick, time) "
               "values(?,?,?,?)", (chan, url, nick, time.time()))
    db.commit()


def get_history(db, chan, url):
    db.execute("delete from urlhistory where time < ?",
               (time.time() - expiration_period,))
    return db.execute("select nick, time from urlhistory where "
                      "chan=? and url=? order by time desc", (chan, url)).fetchall()

def get_title(url):
    for ignored_url in ignored_title_urls:
        if ignored_url in url:
            return None

    try:
        html = http.get_html(url)
        title = html.xpath('/html/head/title')[0]
        title = title.text.strip()
    except:
        return None

    return (title[:title_length] + '..') if len(title) > title_length else title

def nicklist(nicks):
    nicks = sorted(dict(nicks), key=unicode.lower)
    if len(nicks) <= 2:
        return ' and '.join(nicks)
    else:
        return ', and '.join((', '.join(nicks[:-1]), nicks[-1]))

def format_reply(url, history):
    title = get_title(url)

    if not history:
        return title

    last_nick, recent_time = history[0]
    last_time = timesince.timesince(recent_time)

    hour_span = math.ceil((time.time() - history[-1][1]) / 3600)
    hour_span = '%.0f hours' % hour_span if hour_span > 1 else 'hour'

    hlen = len(history)
    ordinal = ["once", "twice", "%d times" % hlen][min(hlen, 3) - 1]

    if len(dict(history)) == 1:
        last = "last linked %s ago" % last_time
    else:
        last = "last linked by %s %s ago" % (last_nick, last_time)

    if title:
        title = "%s - " % (title)
    else:
        title = ""

    return "%sthat url has been posted %s in the past %s by %s (%s)." % (title, ordinal,
                                                                       hour_span, nicklist(history), last)
@hook.regex(r'([a-zA-Z]+://|www\.)[^ ]+')
def urlinput(match, nick='', chan='', db=None, bot=None):
    db_init(db)
    url = urlnorm.normalize(match.group().encode('utf-8'))
    if url not in ignored_urls:
        url = url.decode('utf-8')
        history = get_history(db, chan, url)
        insert_history(db, chan, url, nick)

        inp = match.string.lower()

        for name in dict(history):
            if name.lower() in inp:  # person was probably quoting a line
                return               # that had a link. don't remind them.

        return format_reply(url, history)
