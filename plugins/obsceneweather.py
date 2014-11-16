"obscene weather"

from util import hook, http

@hook.command(autohelp=False)
def fweather(inp, chan='', nick='', reply=None, db=None):
    ".fweather <location> | @<nick> -- gets the effin weather"


    # this database is used by other plugins interested in user's locations,
    # like .near in tag.py
    db.execute(
        "create table if not exists location(chan, nick, loc, lat, lon, primary key(chan, nick))")

    if inp[0:1] == '@':
        nick = inp[1:].strip()
        loc = None
        dontsave = True
    else:
        loc = inp

        dontsave = loc.endswith(" dontsave")
        if dontsave:
            loc = loc[:-9].strip().lower()

    if not loc:  # blank line
        loc = db.execute(
            "select loc from location where chan=? and nick=lower(?)",
            (chan, nick)).fetchone()
        if not loc:
            try:
                # grab from old-style weather database
                loc = db.execute("select loc from weather where nick=lower(?)",
                                 (nick,)).fetchone()
            except db.OperationalError:
                pass    # no such table
            if not loc:
                return fweather.__doc__
        loc = loc[0]

    loc, _, state = loc.partition(', ')

    # Check to see if a lat, long pair is being passed. This could be done more
    # completely with regex, and converting from DMS to decimal degrees. This
    # is nice and simple, however.
    try:
        float(loc)
        float(state)

        loc = loc + ',' + state
        state = ''
    except ValueError:
        if state:
            state = http.quote_plus(state)
            state += '/'

        loc = http.quote_plus(loc)

    url = 'http://thefuckingweather.com/'
    query = '?where={state}{loc}'.format(state=state, loc=loc)

    url += query

    try:
        parsed_html = http.get_html(url)
    except IOError:
        return 'I CAN\'T PARSE THAT SHIT'

    info = {}

    result = parsed_html.xpath('//p[@class="large"] | //p[@class="remark"] | //p[@class="flavor"]')

    if not len(result):
        reply('I CAN\'T FIND THAT SHIT')
        return

    reply(' - '.join([ r.text_content() for r in result ]))
