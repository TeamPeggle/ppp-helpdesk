import random
import re
from time import strptime, strftime
from urllib import quote

from util import http, hook

import twitter

@hook.api_key('twitter')
@hook.command('btc', autohelp=False)
@hook.command('bitcoin', autohelp=False)
@hook.command('bit', autohelp=False)
@hook.command(autohelp=False)
def buttcoin(inp, api_key=None):
    ".bitcoin -- gets current exchange rate for bitcoins from BTC-e"
    data = http.get_json("https://btc-e.com/api/2/btc_usd/ticker")

    data['ticker']['buttcoin'] = twitter.twitter("buttcoin", api_key)

    return (
        "USD/BTC: \x0307{buy:.0f}\x0f - High: \x0307{high:.0f}\x0f"
        " - Low: \x0307{low:.0f}\x0f - Volume: {vol_cur:.0f}"
        "  ---  {buttcoin:s}"
    ).format(**data['ticker'])
