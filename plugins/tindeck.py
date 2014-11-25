from util import hook, http
import re

@hook.command(autohelp=False)
def tindeck(inp):
    ".tindeck <tindeck id>"

    data = {
        "title": "",
        "length": "",
        "upload_time_since": "never",
        "uploader": "unknown",
        "downloads": 0
    }

    track_details_regex = re.compile(r"b, (?P<duration>[0-9:]+), [^,]+, (?P<downloads>[0-9, ]+) downloads")
    uploaded_info_regex = re.compile(r"Shared by (?P<uploader>.+?) (?P<since>\d+ (?:years?|months?|weeks?|days?|hours?|minutes?|seconds)) ago")

    tindeck_html_document = http.get_html("http://tindeck.com/listen/%s" % inp)
    
    # Easier to get the title from the meta properties..
    data['title'] = next(e.attrib.get('content') for e in tindeck_html_document.findall('head/meta') if e.attrib.get('itemprop') == 'name')

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

    return (
        "\x02{title:s}\x02 - "
        "length \x02{length:s}\x02 - "
        "\x02{downloads:d}\x02 downloads - "
        "{upload_time_since:s} by \x02{uploader:s}\x02"
    ).format(**data)
    
    
@hook.regex(r'tindeck\.com/listen/([a-zA-Z0-9]+)')
def tindeck_url(match):
    return tindeck(match.group(1))