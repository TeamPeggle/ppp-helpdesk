import re
 
from time import mktime, strptime
from util import hook, http, timesince
 
@hook.regex(r'vine.co/v/([A-Za-z0-9]+)')
def vine_url(match):
    page_html = http.get('http://vine.co/v/%s' % match.group(1))
 
    vine_post_matches = re.search(r'vine://post/([0-9]+)', page_html)
 
    if not vine_post_matches:
        return None
 
    post_id = vine_post_matches.group(1)
    
    info = http.get_json('http://api.vineapp.com/timelines/posts/%s' % post_id)

    if info['data']['count'] > 0 and info:
        info['data']['records'][0]['upload_date_since'] = timesince.timesince(
            mktime(strptime(info['data']['records'][0]['created'][:-7], '%Y-%m-%dT%H:%M:%S'))
        )
        info['data']['records'][0]['likes_count'] = info['data']['records'][0]['likes']['count']
        info['data']['records'][0]['loops_count'] = info['data']['records'][0]['loops']['count']
        
        return ("\x02%(description)s\x02 - "
                "\x02%(likes_count)d\x02 likes - "
                "\x02%(loops_count)d\x02 loops - "
                "\x02%(upload_date_since)s ago\x02 by \x02%(username)s\x02"
                % info['data']['records'][0])