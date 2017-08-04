import bottlenose
import bitly_api
from lxml import etree
from util import hook, http

@hook.api_key('amazon')
@hook.command('amazon')
@hook.command('a')
def amazon(inp, api_key=None):
    if api_key is None or 'AWS_KEY' not in api_key or 'SECRET_KEY' not in api_key or 'ASSOCIATE_TAG' not in api_key:
       return "missing API key"

    amazon = bottlenose.Amazon(api_key['AWS_KEY'], api_key['SECRET_KEY'], api_key['ASSOCIATE_TAG'], Region='US')
    response = amazon.ItemSearch(Keywords=inp, SearchIndex='All')

    NS = '{http://webservices.amazon.com/AWSECommerceService/2013-08-01}'

    root = etree.fromstring(response)

    error = root.find('.//' + NS + 'Error')
    if error is not None:
        errorMsg = error.find(NS + 'Message').text
        return errorMsg

    item = root.find('.//' + NS + 'Item')  # First item in results
    url = item.find(NS + 'DetailPageURL').text

    itemAttributes = item.find(NS + 'ItemAttributes')
    title = itemAttributes.find(NS + 'Title').text

    if 'bitly' not in api_key:
        return title + ": " + url

    bitly = bitly_api.Connection(access_token=api_key['bitly'])
    bitlyResponse = bitly.shorten(url)
    shortUrl = bitlyResponse['url']

    return title + ": " + shortUrl
