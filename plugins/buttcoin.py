import random
import re
from time import strptime, strftime
from urllib import quote
import unicodedata

from util import http, hook

import twitter

@hook.api_key('twitter')
@hook.command('btc', autohelp=False)
@hook.command('bitcoin', autohelp=False)
@hook.command('bit', autohelp=False)
@hook.command(autohelp=False)
def buttcoin(inp, api_key=None):
    ".bitcoin -- gets current exchange rate for bitcoins"

    inp = inp or 'USD'
    inp = inp.upper()

    data = http.get_json("https://blockchain.info/ticker")

    if inp in data:
      data = data[inp]
      data['currency'] = inp
    else:
      return 'Invalid currency'

    buttcoin = twitter.twitter("buttcoin", api_key)

    buttcoin = unicodedata.normalize('NFKD', buttcoin)
    buttcoin = buttcoin.encode('ascii', 'replace')

    data['buttcoin'] = buttcoin
    
    return (
        "{currency:s}/BTC: \x0307{symbol:s}{last:.2f}\x0f "
        " - High: \x0307{symbol:s}{buy:.2f}\x0f"
        " - Low: \x0307{symbol:s}{sell:.2f}\x0f"
        "  ---  {buttcoin:s}"
    ).format(**data)
