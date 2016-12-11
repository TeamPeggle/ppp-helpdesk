import re
from cookielib import Cookie
from util import hook, http, timesince

def format_comment(data):
    if not data:
        return None

    if data['over_18']:
        data['nsfw_tag'] = '- \x034NSFW\x0f'
    else:
        data['nsfw_tag'] = ''

    data['time_ago'] = timesince.timesince(data['created_utc'])

    return (
        "\x02{title:s}\x02 (\x0307{ups:d}\x0f|\x0312{downs:d}\x0f) "
        "- {time_ago:s} ago by {author:s} to /r/{subreddit:s} - {num_comments:d} comments{nsfw_tag:s}"
    ).format(**data)

    return data

def format_subreddit(data):
    if not data:
        return None

    if data['over18']:
        data['nsfw_tag'] = '- \x034NSFW\x0f'
    else:
        data['nsfw_tag'] = ''

    if data['quarantine']:
        data['quarantine_tag'] = ' - QUARANTINED '
    else:
        data['quarantine_tag'] = ''

    data['time_ago'] = timesince.timesince(data['created_utc'])

    return (
        "\x02/r/{display_name} - {description:s}\x02 - {subscribers:d} subscribers "
        "- created {time_ago:s} ago {nsfw_tag:s}{quarantine_tag:s}"
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

def info_by_reddit_subreddit(subreddit):
    url = 'http://www.reddit.com/r/%s/about.json' % (subreddit)

    data = http.get_json(url)

    return format_subreddit(data['data'])


@hook.regex(r'reddit.com/r/([^/]+)/comments/([^/]+)')
def link_reddit_comments(match):
    return info_by_reddit_id('t3', match.group(2))

@hook.regex(r'reddit.com/r/([^/]+)$')
def link_reddit_subreddit(match):
    return info_by_reddit_subreddit(match.group(1))
