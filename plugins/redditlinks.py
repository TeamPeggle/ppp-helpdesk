import re
from cookielib import Cookie
from util import hook, http, timesince

def format_comment(data):
    if not data:
        return None

    if data['over_18']:
        data['nsfw_tag'] = '\x0306NSFW\x0f - '
    else:
        data['nsfw_tag'] = ''

    data['time_ago'] = timesince.timesince(data['created_utc'])

    return (
        "{nsfw_tag:s}\x02{title:s}\x02 (\x0307{ups:d}\x0f|\x0312{downs:d}\x0f) "
        "- {time_ago:s} ago by {author:s} to /r/{subreddit:s} - {num_comments:d} comments"
    ).format(**data)

    return data

def info_by_reddit_id(type, id):
    url = 'http://www.reddit.com/by_id/%s_%s.json' % (type, id)

    data = http.get_json(url)

    if type == 't3':
        children = data['data']['children']

        if len(children) == 0:
            return None

        return format_comment(children[0]['data'])

    return data

@hook.regex(r'reddit.com/r/([A-Za-z0-9]+)/comments/([a-z0-9A-Z]+)')
def link_reddit_comments(match):
    return info_by_reddit_id('t3', match.group(2))
