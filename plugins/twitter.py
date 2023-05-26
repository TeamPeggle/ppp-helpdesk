from __future__ import unicode_literals

import random
import re
from urllib.parse import quote, urlencode
from time import strptime, time
from calendar import timegm
from util import timesince
import json

from util import hook, http
import datetime

from lxml import html

from http.cookiejar import Cookie

# This is a public key that's hard-coded into the twitter client
PUBLIC_AUTHORIZATION_HEADER = 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs=1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA'
GUEST_TOKEN_TTL = 10800
TWITTER_TWEET_GRAPHQL_URL = 'https://twitter.com/i/api/graphql/miKSMGb2R1SewIJv2-ablQ/TweetDetail'

DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.8.1.6) ' \
             'Gecko/20070725 Firefox/2.0.0.6'

def text_content(html_string):
    return html.fromstring(html_string).text_content()

def format_tweet(time, screen_name, text):
    since = '%s ago' % timesince.timesince(
        timegm(
            strptime(time, '%a %b %d %H:%M:%S +0000 %Y')
        )
    )

    return "%s by \x02%s\x02: %s" % (since, screen_name, text)

def get_guest_token(url):
  # Technically this can be memoized for 10800 seconds but I'm currently way too lazy
  
  html_text_content = http.get(
    url,
    cookies=True,
    headers={
      'Referer': url,
			'Accept-Language': 'en-US,en;q=0.5',
      'User-Agent': DEFAULT_USER_AGENT
    }
  )

  match = re.search(
    r'document\.cookie="gt=(\d+); Max-Age=(\d+); Domain=\.twitter\.com; Path=/; Secure"',
    html_text_content
  )

  if not match:
    return None

  return match[1]

def ensure_guest_token_cookie(url = 'https://twitter.com/'):
  guest_token = get_guest_token(url)

  if guest_token:
      guest_token_cookie = Cookie(
        0, 'gt', guest_token, '443', '443', '.twitter.com', '.twitter.com',
        None, '/', '/', False, time() + GUEST_TOKEN_TTL, None, None, None, None
      )

      http.get_cookie_jar().set_cookie(guest_token_cookie)
  return guest_token

def get_twitter_status(status_id):
  tweet_url = f'https://twitter.com/i/web/status/{status_id}'
  guest_token = ensure_guest_token_cookie(tweet_url)
  
  paginationVariables = {
    'focalTweetId': status_id,
    'cursor': None,
    'referrer': 'tweet',
    'with_rux_injections': False,
    'includePromotedContent': True,
    'withCommunity': True,
    'withQuickPromoteEligibilityTweetFields': True,
    'withBirdwatchNotes': False,
    'withVoice': True,
    'withV2Timeline': True,
  }
  variables = paginationVariables.copy()
  del variables['cursor'], variables['referrer']
  features = {
    'rweb_lists_timeline_redesign_enabled': False,
    'blue_business_profile_image_shape_enabled': True,
    'responsive_web_graphql_exclude_directive_enabled': True,
    'verified_phone_label_enabled': False,
    'creator_subscriptions_tweet_preview_api_enabled': False,
    'responsive_web_graphql_timeline_navigation_enabled': True,
    'responsive_web_graphql_skip_user_profile_image_extensions_enabled': False,
    'tweetypie_unmention_optimization_enabled': True,
    'vibe_api_enabled': True,
    'responsive_web_edit_tweet_api_enabled': True,
    'graphql_is_translatable_rweb_tweet_is_translatable_enabled': True,
    'view_counts_everywhere_api_enabled': True,
    'longform_notetweets_consumption_enabled': True,
    'tweet_awards_web_tipping_enabled': False,
    'freedom_of_speech_not_reach_fetch_enabled': True,
    'standardized_nudges_misinfo': True,
    'tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled': False,
    'interactive_text_enabled': True,
    'responsive_web_text_conversations_enabled': False,
    'longform_notetweets_rich_text_read_enabled': True,
    'longform_notetweets_inline_media_enabled': False,
    'responsive_web_enhance_cards_enabled': False,
  }

  params = {'variables': variables, 'features': features}

  query_params = {k: json.dumps(v, separators = (',', ':')) for k, v in params.items()}

  payload = http.get_json(
    TWITTER_TWEET_GRAPHQL_URL,
    cookies=True,
    headers={
      'User-Agent': DEFAULT_USER_AGENT,
      'Authorization': PUBLIC_AUTHORIZATION_HEADER,
      'Referer': tweet_url,
			'Accept-Language': 'en-US,en;q=0.5',
      'x-guest-token': guest_token
    },
    query_params=query_params
  )

  for instruction in payload['data']['threaded_conversation_with_injections_v2']['instructions']:
    if instruction['type'] != 'TimelineAddEntries':
      continue

    for entry in instruction['entries']:
      if entry['entryId'] == f'tweet-{status_id}' and entry['content']['entryType'] == 'TimelineTimelineItem' and entry['content']['itemContent']['itemType'] == 'TimelineTweet':
        tweet = entry['content']['itemContent']['tweet_results']['result']

        result = tweet['legacy']
        result['user'] = tweet['core']['user_results']['result']['legacy']
        return result      

@hook.command
def twitter(inp):
    ".twitter <user>/<user> <n>/<id>/#<search>/#<search> <n> -- " \
        "get <user>'s last/<n>th tweet/get tweet <id>/do <search>/get <n>th <search> result"

    getting_id = False
    doing_search = False
    index_specified = False

    if re.match(r'^\d+$', inp):
        try:
            tweet = get_twitter_status(inp)
        except http.HTTPError as e:
            errors = {
                400: 'bad request (ratelimited?)',
                401: 'unauthorized',
                403: 'forbidden',
                404: 'invalid tweet id',
                500: 'twitter is broken',
                502: 'twitter is down ("getting upgraded")',
                503: 'twitter is overloaded (lol, RoR)',
            }

            if e.code in errors:
                return 'error: ' + errors[e.code]
            return 'error: unknown %s' % e.code
    
        getting_id = True
    else:
        return 'elon is a genius businessman and knows how to run a company.  40k is a reasonable price for access to an API they run anyway.  sometimes I eat soap because it smells so good'

    if doing_search:
        try:
            tweet = tweet["statuses"]
            if not index_specified:
                index = random.randint(0, len(tweet) - 1)
        except KeyError:
            return 'error: no results'

    if not getting_id:
        try:
            tweet = tweet[index]
        except IndexError:
            return 'error: not that many tweets found'

    if 'retweeted_status' in tweet:
        rt = tweet["retweeted_status"]
        rt_text = text_content(rt["full_text"])
        text = "RT @%s %s" % (rt["user"]["screen_name"], rt_text)
    else:
        text = text_content(tweet["full_text"])\

    text = text.replace('\n', ' ')
    screen_name = tweet["user"]["screen_name"]
    time = tweet["created_at"]

    return format_tweet(time, screen_name, text)


@hook.regex(r'https?://(mobile\.)?twitter.com/(#!/)?([_0-9a-zA-Z]+)/status/(?P<id>\d+)')
def show_tweet(match):
    return twitter(match.group('id'))
