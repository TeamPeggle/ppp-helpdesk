import re
from urllib import urlencode
from cookielib import Cookie
from util import hook, http

@hook.regex(r'steamcommunity.com/(profiles)/([0-9]+)')
@hook.regex(r'steamcommunity.com/(id)/([A-Za-z0-9]+)')
def link_steam_user(match):
    if match.group(1) == 'profiles':
        url = 'http://steamcommunity.com/profiles/%d' % match.group(2)
    elif match.group(1) == 'id':
        url = 'http://steamcommunity.com/id/%s' % match.group(2)
    else:
        return None

    try:
        doc = http.get_html(url)
    except:
        return None

    name = doc.find_class('profile_header_summary')[0].find_class('persona_name')[0].text_content().strip()
    name = name.replace('This user has also played as:', '').strip()

    level = doc.find_class('persona_level')[0].text_content().strip()

    game_status = doc.find_class('profile_in_game_header')[0].text_content().strip()

    if game_status == 'Currently Offline':
        game_status = doc.find_class('profile_in_game_name')[0].text_content().strip()

    if game_status == 'Currently In-Game':
        game_status = 'Playing %s' % doc.find_class('profile_in_game_name')[0].text_content().strip()

    game_count = 0

    profile_counts = doc.find_class('profile_count_link')

    for count in profile_counts:
        count_text = count.text_content().strip()
        if count_text.startswith('Games'):
            game_count = int(count_text[5:].strip())


    message = "\x02%s\x02 - %s - %s - %d games" % (name, game_status, level, game_count)

    bans = doc.find_class('profile_ban')

    if (len(bans) > 0):
        bans = bans[0].text_content().split('|')[0].strip()

        message += " - %s" % bans

    return message


@hook.regex(r'store.steampowered.com/app/([0-9]+)')
def link_steam_app(match):
    url = 'http://store.steampowered.com/app/%d' % int(match.group(1))
    age_check_url = 'http://store.steampowered.com/app/%d/agecheck' % int(match.group(1))

    # Cookie(
    #    version, name, value, port, port_specified, domain, domain_specified,
    #    domain_initial_dot, path, path_specified, secure, expiry, comment, comment_url, rest)
    age_gate_cookie = Cookie(
        None, 'mature_content', '1', '80', '80', 'store.steampowered.com', 'store.steampowered.com',
        None, '/', '/', False, '2147483600', None, None, None, None
    )

    http.jar.set_cookie(age_gate_cookie)

    try:
        doc = http.get_html(
            url,
            cookies=True
        )
    except http.HTTPError, e:
        return None

    try:
        title = doc.find_class('apphub_AppName')[0].text_content().strip()
    except:
        return None

    try:
        rating = doc.find_class('game_review_summary')[0].text_content().strip()
    except:
        rating = 'Unknown'

    try:
        if len(doc.find_class('discount_original_price')) > 0:
            full_price = doc.find_class('discount_original_price')[0].text_content()
            full_price = full_price.strip()

            discount_price = doc.find_class('discount_final_price')[0].text_content()
            discount_price = discount_price.strip()

            discount_percent = doc.find_class('discount_pct')[0].text_content()
            discount_percent = discount_percent.strip()

            price = '\x0307%s\x0f (%s discount off %s)' % (discount_price, discount_percent, full_price)
        else:
            price = doc.find_class('game_purchase_price')[0].text_content().strip()
    except:
        price = 'Unknown'

    try:
        # Limit to only 5 tags
        tags = doc.find_class('app_tag')[0:5]

        # Remove the '+' add button tag
        tags = [ tag for tag in tags if not 'add_button' in tag.get('class') ]

        # Get element Text content / Strip the text
        tags = [ tag.text_content().strip() for tag in tags ]

        if len(tags) > 0:
            tags = ' - %s' % (', '.join(tags))
    except:
        tags = ''

    return '\x02%s\x02 - %s - User rating is %s%s' % (title, price, rating, tags)

@hook.command
def steam(inp):
    url = 'http://store.steampowered.com/search?%s' % urlencode({ 'term': inp })

    try:
        doc = http.get_html(
            url,
            cookies=True
        )
    except http.HTTPError, e:
        return None

    try:
        app_url = doc.find_class('search_result_row')[0].attrib['href'].strip()
    except:
        return 'app not found'

    match = re.search(r'store.steampowered.com/app/([0-9]+)', app_url)

    if not match:
        return None

    return '%s - https://store.steampowered.com/app/%d' % (link_steam_app(match), int(match.group(1)))
