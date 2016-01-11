import re

from time import strptime
from calendar import timegm
from util import hook, http, timesince

@hook.regex(r'liveleak.com/view\?(?:.+&)?i=([a-z0-9]{3}_[0-9]{10})')
def liveleak_url(match):
	try:
		doc = http.get_html('http://mobile.liveleak.com/view?ajax=1&p=1&i=%s' % match.group(1))
	except HTTPError:
		return 'error connecting to liveleak'

	if doc.get_element_by_id('body_text') is None or doc.get_element_by_id('item_info_%s' % match.group(1)) is None:
		# This means that the video URL was invalid
		return

	info = {};
	info['description'] = doc.find_class('section_title')[0].text_content().strip()

	info_text = doc.get_element_by_id('item_info_%s' % match.group(1)).text_content()

	info['section'] = re.search('In: ((?:[^ ]+\s)+)\s{6}', info_text).group(1).strip()
	info['username'] = re.search('By: ((?:[^ ]+\s)+)\s{6}', info_text).group(1).strip()
	info['upload_date_since'] = re.search('Added: (.+?)\s*(?:Occurred On|By):', info_text).group(1).strip()
	info['views_count'] = int(re.search('Views: (\d+)', info_text).group(1).strip())

	if u'ago' in info['upload_date_since']:
		info['upload_date_since'] = re.sub('ago', '', info['upload_date_since']).strip()
	else:
		info['upload_date_since'] = timesince.timesince(
			timegm(
				strptime(
					info['upload_date_since'], '%b'
				)
			)
		)

	return ("\x02%(description)s\x02 in \x02%(section)s\x02 - "
			 "\x02%(views_count)d\x02 views - "
			 "\x02%(upload_date_since)s ago\x02 by \x02%(username)s\x02"
			 % info)
