# IMDb lookup plugin by Ghetto Wizard (2011).

from util import hook, http
import re

# http://www.imdb.com/title/tt1853728/
# http://www.imdb.com/title/tt3385516/?ref_=vi_tt_t_hm_hp
IMDB_URL_REGEX = (r'imdb.com/title/(tt[0-9]+)', re.I)

def format_omdb_response(content):
    if content['Response'] == 'Movie Not Found':
        return 'movie not found'
    elif content['Response'] == 'True':
        content['URL'] = 'http://www.imdb.com/title/%(imdbID)s' % content

        out = '\x02%(Title)s\x02 (%(Year)s) (%(Genre)s): %(Plot)s'
        if content['Runtime'] != 'N/A':
            out += ' \x02%(Runtime)s\x02.'
        if content['imdbRating'] != 'N/A' and content['imdbVotes'] != 'N/A':
            out += ' \x02%(imdbRating)s/10\x02 with \x02%(imdbVotes)s\x02 votes.'
        out += ' %(URL)s'
        return out % content
    else:
        return 'unknown error'

@hook.regex(*IMDB_URL_REGEX)
def imdb_link(match):
    '''Respond to imdb URL'''
    return format_omdb_response(http.get_json("http://www.omdbapi.com/", i=match.group(1)))

@hook.command
def imdb(inp):
    '''.imdb <movie> -- gets information about <movie> from IMDb'''
    return format_omdb_response(http.get_json("http://www.omdbapi.com/", t=inp))
