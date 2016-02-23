from util import hook, http
import re

TINDECK_LISTEN_REGEX = re.compile(r'tindeck\.com/listen/([a-zA-Z0-9]+)')

def tindeck_id(id, include_url = False):
    data = {
        "url": "",
        "title": "",
        "length": "",
        "upload_time_since": "never",
        "uploader": "unknown",
        "downloads": 0
    }

    track_details_regex = re.compile(r"b, (?P<duration>[0-9:]+), [^,]+, (?P<downloads>[0-9, ]+) downloads")
    uploaded_info_regex = re.compile(r"Shared by (?P<uploader>.+?) (?P<since>\d+ (?:years?|months?|weeks?|days?|hours?|minutes?|seconds)) ago")

    tindeck_html_document = http.get_html("http://tindeck.com/listen/%s" % id)

    # Easier to get the title from the meta properties..
    data['title'] = next(e.attrib.get('content') for e in tindeck_html_document.findall('head/meta') if e.attrib.get('itemprop') == 'name')
    data['url'] = next(e.attrib.get('content') for e in tindeck_html_document.findall('head/meta') if e.attrib.get('property') == 'og:url')

    # And the site is such a terrible thing that it's easier to pull all text and match against that..
    tindeck_text = tindeck_html_document.text_content()

    track_details_match = track_details_regex.search(tindeck_text)
    uploaded_match = uploaded_info_regex.search(tindeck_text)

    if track_details_match:
        duration = track_details_match.group('duration')

        # Convert the duration to seconds..
        length = sum(int(x) * 60 ** i for i, x in enumerate(reversed(duration.split(':'))))

        # ..and then back to a human readable format that matches the other plugins
        data['length'] = ''
        if length / 3600:  # > 1 hour
            data['length'] += '%dh ' % (length / 3600)
        if length / 60:
            data['length'] += '%dm ' % (length / 60 % 60)
        data['length'] += "%ds" % (length % 60)

        data['downloads'] = int(track_details_match.group('downloads'))

    uploaded_match = uploaded_info_regex.search(tindeck_text)
    if uploaded_match:
        # this is already a relative time..
        # but maybe would be better to pull its title which is a full date
        data['upload_time_since'] = "\x02%s\x02 ago" % uploaded_match.group('since')
        data['uploader'] = uploaded_match.group('uploader')

    formatted_output = ""
    formatted_output += "\x02{title:s}\x02 - "
    formatted_output += "length \x02{length:s}\x02 - "
    formatted_output += "\x02{downloads:d}\x02 downloads - "
    formatted_output += "{upload_time_since:s} by \x02{uploader:s}\x02"

    if include_url:
        formatted_output += " - \x02{url:s}\x02"

    return (formatted_output).format(**data)

@hook.command(autohelp=False)
def tindeck(inp):
    ".tindeck <search parameters>"

    search_url = (
            "https://www.googleapis.com/customsearch/v1element?"
            "key=AIzaSyCVAXiUzRYsML1Pv6RwSG1gunmMikTzQqY&rsz=filtered_cse&num=1"
            "&hl=en&prettyPrint=false&source=gcsc&gss=.com&sig=432dd570d1a38625"
            "3361f581254f9ca1&cx=009861066249378011774:d9akxp2g2xi&googlehost=w"
            "ww.google.com&oq=test&gs_l=partner.12...0.0.2.2403.0.0.0.0.0.0.0.0"
            "..0.0.gsnos,n=13...0.0..1ac..25.partner..1.3.260.s-wnCSLs2j8"
    )

    inp = 'inurl:"http://tindeck.com/listen/" ' + inp

    search_result = http.get_json(http.prepare_url(search_url, { "q": inp }))

    unescapedUrl = search_result['results'][0]['unescapedUrl']

    match = TINDECK_LISTEN_REGEX.search(unescapedUrl)

    if not match:
        return "not found"

    return tindeck_id(match.group(1), True)

@hook.regex(TINDECK_LISTEN_REGEX)
def tindeck_url(match):
    return tindeck_id(match.group(1))
