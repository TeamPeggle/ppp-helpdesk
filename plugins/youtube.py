from __future__ import unicode_literals

from builtins import str
import re
import time
from calendar import timegm
from util import hook, http, timesince


youtube_re = (
    r"(?:youtube.*?(?:v=|/v/|/shorts/)|youtu\.be/|yooouuutuuube.*?id=)" "([-_a-z0-9]+)",
    re.I,
)

BASE_URL = "https://www.googleapis.com/youtube/v3/"
INFO_URL = BASE_URL + "videos?part=snippet,contentDetails,statistics&hl=en"
SEARCH_API_URL = BASE_URL + "search"
VIDEO_URL = "https://youtu.be/%s"


def get_video_description(vid_id, api_key):
    j = http.get_json(INFO_URL, id=vid_id, key=api_key)

    if not j["pageInfo"]["totalResults"]:
        return

    j = j["items"][0]

    duration = j["contentDetails"]["duration"].replace("PT", "").lower()

    published = j["snippet"]["publishedAt"].replace(".000Z", "Z")
    published = time.strptime(published, "%Y-%m-%dT%H:%M:%SZ")
    published_since = timesince.timesince(timegm(published))

    views = 0
    likes = 0
    dislikes = 0

    if "statistics" in j:
        views = group_int_digits(j["statistics"].get("viewCount", 0), ",")
        likes = j["statistics"].get("likeCount", 0)
        dislikes = j["statistics"].get("dislikeCount", 0)

    channel_title = j["snippet"]["channelTitle"]
    title = j["snippet"]["title"]
    if "localized" in j["snippet"]:
        title = j["snippet"]["localized"].get("title") or title

    out = (
        "\x02{title}\x02 - length \x02{duration}\x02 - "
        "{likes}\u2191{dislikes}\u2193 - "
        "\x02{views}\x02 views - "
        "published \x02{published_since}\x02 ago by \x02{channel_title}\x02"
    ).format(
        title=title,
        duration=duration,
        likes=likes,
        dislikes=dislikes,
        views=views,
        published_since=published_since,
        channel_title=channel_title
    )

    if "rating" in j:
        out += " - rated \x02%.2f/5.0\x02 (%d)" % (j["rating"],
                                                   j["ratingCount"])

    if "contentRating" in j:
        out += " - \x034NSFW\x02"

    return out


def group_int_digits(number, delimiter=" ", grouping=3):
    base = str(number).strip()
    builder = []
    while base:
        builder.append(base[-grouping:])
        base = base[:-grouping]
    builder.reverse()
    return delimiter.join(builder)


@hook.api_key("google")
@hook.regex(*youtube_re)
def youtube_url(match, api_key=None):
    return get_video_description(match.group(1), api_key)


@hook.api_key("google")
@hook.command("yt")
@hook.command("y")
@hook.command
def youtube(inp, api_key=None):
    ".youtube <query> -- returns the first YouTube search result for <query>"

    params = {
        "key": api_key,
        "fields": "items(id(videoId))",
        "part": "snippet",
        "type": "video",
        "maxResults": "1",
        "q": inp,
    }

    j = http.get_json(SEARCH_API_URL, **params)

    if "error" in j:
        return "error while performing the search"

    results = j.get("items")

    if not results:
        return "no results found"

    vid_id = j["items"][0]["id"]["videoId"]

    return get_video_description(vid_id, api_key) + " - " + VIDEO_URL % vid_id
