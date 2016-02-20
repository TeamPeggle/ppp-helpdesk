import random, string

from util import hook, http


frinkiac_url = "https://frinkiac.com/"
frinkiac_search_url = "https://frinkiac.com/api/search"
frinkiac_caption_url = "https://frinkiac.com/api/caption"

@hook.command
def frink(inp):
    ".frink <query> -- searches Frinkiac for Simpsons quotes"

    steamed_hams = http.get_json(frinkiac_search_url, q=inp)

    if not steamed_hams:
        return "no cromulent quotes found"
    
    if(len(steamed_hams) > 10):
        steamed_hams = steamed_hams[:10]

    SKIIIINNER = random.choice(steamed_hams)
    episode = SKIIIINNER['Episode']
    timestamp = SKIIIINNER['Timestamp']
    
    aurora_borealis = http.get_json(frinkiac_caption_url, e=episode, t=timestamp)
    
    leader_beans = []
    
    for skinner_excuse in aurora_borealis['Subtitles']:
        leader_beans.append(skinner_excuse['Content'])
    
    ah_superintendent_chalmers = string.join(leader_beans)
    if len(ah_superintendent_chalmers) > 250:
        ah_superintendent_chalmers = ah_superintendent_chalmers[:250] + "..."
    what_a_pleasant_surprise = frinkiac_url + 'caption/%s/%s' % (episode, timestamp)

    return "\"%s\" %s" % (ah_superintendent_chalmers, what_a_pleasant_surprise)
