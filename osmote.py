'''
Documentation, License etc.

@package osmote
'''

from urllib.parse import urlparse, parse_qs
import feedparser




FEED_URL = 'http://osmose.openstreetmap.fr/%s/byuser/%s.rss'

lang = 'en'
user = 'jonycoo'

url = FEED_URL%(lang, user)
feed = feedparser.parse(url)

for i in range(len(feed)):
    par = parse_qs(urlparse(feed.entries[i].link).fragment)
    lat = par['lat'][0]
    lon = par['lon'][0]
    print(lat + ';' + lon)
    

    



