from time import strptime
from calendar import timegm
from util import hook, http, timesince


@hook.regex(r'vimeo.com/([0-9]+)')
def vimeo_url(match):
    info = http.get_json('http://vimeo.com/api/v2/video/%s.json'
                         % match.group(1))

    if info:
        info[0]['upload_date_since'] = timesince.timesince(
            timegm(strptime(info[0]['upload_date'], '%Y-%m-%d %H:%M:%S'))
        )
        return ("\x02%(title)s\x02 - length \x02%(duration)ss\x02 - "
                "\x02%(stats_number_of_likes)s\x02 likes - "
                "\x02%(stats_number_of_plays)s\x02 plays - "
                "\x02%(upload_date_since)s ago\x02 by \x02%(user_name)s\x02"
                % info[0])
