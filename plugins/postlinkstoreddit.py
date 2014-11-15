from util import http,hook
import praw

@hook.regex(r'((http|ftp|https|gopher)://|www\.)[^ ]+')
def redditurlinput(match, nick='', chan='', reply=None, db=None, bot=None):
	r = praw.Reddit(user_agent='ppp-helpdesk/1.0 by edwardly')
	
	r.set_oauth_app_info(
		client_id=bot.config['api_keys']['reddit']['consumer'],
		client_secret=bot.config['api_keys']['reddit']['consumer_secret'],
		redirect_uri='http://127.0.0.1:65010/authorize_callback'
	)

	r.refresh_access_information(bot.config['api_keys']['reddit']['refresh_token'])

	posted_url = match.group(0)
	posted_title = posted_url
	
	try:
		posted_title = http.get_html(posted_url).find('.//title').text;
	except:
		pass

	try:
		r.submit(
			'partyprincesspalace',
			'<%s> %s' % (nick, posted_title),
			url=posted_url,
			resubmit=True,
			raise_captcha_exception=True
		)
	except praw.errors.InvalidCaptcha as e:
		print "!!!!!!!!!!!!!!!!!!!"
		print "Captcha detected.  NEED MORE UPVOTES!"
		print "!!!!!!!!!!!!!!!!!!!"