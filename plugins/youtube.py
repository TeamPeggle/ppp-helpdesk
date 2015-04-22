import re
import time

import locale
from urllib import urlencode
from calendar import timegm
from util import hook, http, timesince
from datetime import timedelta

ISO8601_PERIOD_REGEX = re.compile(
    r"^(?P<sign>[+-])?"
    r"P(?!\b)"
    r"(?P<years>[0-9]+([,.][0-9]+)?Y)?"
    r"(?P<months>[0-9]+([,.][0-9]+)?M)?"
    r"(?P<weeks>[0-9]+([,.][0-9]+)?W)?"
    r"(?P<days>[0-9]+([,.][0-9]+)?D)?"
    r"((?P<separator>T)(?P<hours>[0-9]+([,.][0-9]+)?H)?"
    r"(?P<minutes>[0-9]+([,.][0-9]+)?M)?"
    r"(?P<seconds>[0-9]+([,.][0-9]+)?S)?)?$"
)

YOUTUBE_URL_REGEX = (r'(?:youtube.*?(?:v=|/v/)|youtu\.be/|yooouuutuuube.*?id=)([-_a-z0-9]+)', re.I)

BASE_URL = 'https://www.googleapis.com/youtube/v3/'
VIDEO_API_URL = BASE_URL + 'videos?%s'
SEARCH_API_URL = BASE_URL + 'search?%s'
VIDEO_URL = 'http://youtube.com/watch?v=%s'

def youtube_iso8601_duration_to_seconds(duration_string):
    match = ISO8601_PERIOD_REGEX.match(duration_string)

    if not match:
        return None

    groups = match.groupdict()

    for key, val in groups.items():
        if key not in ('separator', 'sign'):
            if val is None:
                groups[key] = "0n"
            groups[key] = float(groups[key][:-1].replace(',', '.'))

    if groups["years"] > 0 and groups["months"] > 0:
        # This is not accurate!  Months and years are variable length
        # However, we shouldn't really EVER be getting them as video durations
        # so this should be close enough in those weird cases..
        groups["days"] += groups["years"] * 365
        groups["days"] += groups["months"] * 30

    ret = timedelta(
        days=groups["days"],
        hours=groups["hours"],
        minutes=groups["minutes"],
        seconds=groups["seconds"],
        weeks=groups["weeks"]
    )

    if groups["sign"] == '-':
        ret = timedelta(0) - ret

    return int(ret.total_seconds())

def youtube_search(search_term, api_key):
    if search_term:
        search_term = search_term.encode('utf8')

    request_data = {
        'key': api_key,
        'part': 'id',
        'maxResults': 1,
        'type': 'video',
        'q': search_term
    }

    j = http.get_json(SEARCH_API_URL % (urlencode(request_data)))

    if 'error' in j:
        return None

    if j['pageInfo']['totalResults'] == 0 or 'items' not in j:
        return None

    return j['items'][0]['id']['videoId']

def youtube_video_description(vid_id, api_key):
    request_data = {
        'key': api_key,
        'part': 'snippet,contentDetails,statistics',
        'maxResults': 1,
        'type': 'video',
        'id': vid_id
    }

    j = http.get_json(VIDEO_API_URL % urlencode(request_data))

    if j['pageInfo']['totalResults'] == 0 or 'items' not in j:
        return None

    j = j['items'][0]

    out = '\x02%s\x0F' % j['snippet']['title']

    if 'duration' in j['contentDetails']:
        length = youtube_iso8601_duration_to_seconds(j['contentDetails']['duration'])
        out += ' - length \x02'
        if length / 3600:
           out += '%dh ' % (length / 3600)
        if length / 60:
           out += '%dm ' % (length / 60 % 60)
        out += "%ds" % (length % 60)
        out += "\x02"

    if 'viewCount' in j['statistics']:
        out += ' - \x02%s\x0F views' % locale.format('%d', int(j['statistics']['viewCount']), grouping=True)

    if 'publishedAt' in j['snippet']:
        upload_time_since = timesince.timesince(
            timegm(
                time.strptime(j['snippet']['publishedAt'], "%Y-%m-%dT%H:%M:%S.000Z")
            )
        )

        upload_time = time.strptime(j['snippet']['publishedAt'], "%Y-%m-%dT%H:%M:%S.000Z")

        out += ' - \x02%s\x0F ago by \x02%s\x0F' % (upload_time_since, j['snippet']['channelTitle'])

    if 'contentRating' in j['contentDetails']:
        if 'ytRating' in j['contentDetails']['contentRating']:
            if j['contentDetails']['contentRating']['ytRating'] == 'ytAgeRestricted':
                out += ' - \x02\x034NSFW\x0F'

    return out

@hook.api_key('google')
@hook.regex(*YOUTUBE_URL_REGEX)
def youtube_url(match, api_key=None):
    return youtube_video_description(match.group(1), api_key)

@hook.api_key('google')
@hook.command('yt')
@hook.command('y')
@hook.command
def youtube(inp, api_key=None):
    '.youtube <query> -- returns the first YouTube search result for <query>'

    vid_id = youtube_search(inp, api_key)

    if not vid_id:
        return 'No videos matched your search query'

    vid_url = VIDEO_URL % vid_id

    return youtube_video_description(vid_id, api_key) + " - " + vid_url