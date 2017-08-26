# (c) onethinglab.com
# Parse web archive history of iTunes pages for well-known applications 

import os
import json
import urllib.request
import urllib.parse
import urllib.error
import re
from time import strptime
from collections import namedtuple, defaultdict
from pprint import pprint
from bs4 import BeautifulSoup


WEB_ARCHIVE_SEARCH_URL = "https://web.archive.org/cdx/search/cdx?"
WEB_ARCHIVE_URL = "https://web.archive.org/web/"
APPS_ITUNES_URL = {
    "Facebook": "https://itunes.apple.com/us/app/facebook/id284882215",
    "Messenger": "https://itunes.apple.com/us/app/messenger/id454638411",
    "Youtube": "https://itunes.apple.com/us/app/youtube-watch-videos-music-and-live-streams/id544007664?mt=8",
    "Instagram": "https://itunes.apple.com/us/app/instagram/id389801252",
    "Skype": "https://itunes.apple.com/us/app/skype-for-iphone/id304878510?mt=8",
    "WhatsApp Messenger": "https://itunes.apple.com/us/app/whatsapp-messenger/id310633997"
    "Google Maps": "https://itunes.apple.com/us/app/google-maps-navigation-transit/id585027354?mt=8",
    "Twitter": "https://itunes.apple.com/us/app/twitter/id333903271",
    "Netflix": "https://itunes.apple.com/us/app/netflix/id363590051",
    "Spotify Music": "https://itunes.apple.com/us/app/spotify-music/id324684580",
    "Snapchat": "https://itunes.apple.com/us/app/snapchat/id447188370",
    "Gmail": "https://itunes.apple.com/us/app/gmail-email-by-google-secure-fast-organized/id422689480?mt=8",
    "Uber": "https://itunes.apple.com/us/app/uber/id368677368",
    "Amazon Shopping": "https://itunes.apple.com/us/app/amazon-shopping-made-easy/id297606951?mt=8",
    "Pinterest": "https://itunes.apple.com/us/app/pinterest/id429047995",
    "Google Chrome": "https://itunes.apple.com/us/app/google-chrome-the-fast-and-secure-web-browser/id535886823?mt=8",
    "Firefox": "https://itunes.apple.com/us/app/firefox-web-browser/id989804926?mt=8",
    "Yelp": "https://itunes.apple.com/us/app/yelp-nearby-restaurants-shopping-services/id284910350?mt=8",
    "Microsoft Outlook": "https://itunes.apple.com/us/app/microsoft-outlook-email-and-calendar/id951937596?mt=8"
}

# default output folder
OUTPUT_FOLDER = "./apps_stats"

REGEX_UPDATED = "(?P<updated_date>[A-Z][a-z]{2}\s\d\d,\s\d\d\d\d)"
REGEX_APP_SIZE = "(?P<app_size>\d+.\d+\sMB)"

def get_history_for_page(root_url):
    params = {'output': 'json',
              'showDupeCount': 'true',
              'url': root_url}
    url = WEB_ARCHIVE_SEARCH_URL + urllib.parse.urlencode(params)
    history = None
    try:
        req = urllib.request.urlopen(url)
        if req is not None:
            history = json.loads(req.read().decode(
                req.headers.get_content_charset('utf-8')))
        else:
            print("Request object for {} is empty".format(url))
    except urllib.error.URLError as e:
        print ("Can't access {} due to {}".format(url, e.reason))
    return history

def parse_time_stamp(time_stamp):
    fmt = "%Y%m%d%H%M%S"
    tm = None
    try:
        tm = strptime(time_stamp, fmt)
    except ValueError as e:
        print("Can't parse {} time stamp due to {}".format(time_stamp, str(e)))
    return tm

def get_archive_pages(root_url):
    history = get_history_for_page(root_url)
    # first item in response list - name of fields
    Fields = namedtuple("Fields", history[0])
    field_params = {v: i for i, v in enumerate(history[0])}
    fields = Fields(**field_params)
    snapshots = dict()

    for item in history[1:]:
        if item[fields.statuscode] == '200':
            tm = parse_time_stamp(item[fields.timestamp])
            timestamp = tm.tm_year, tm.tm_mon, tm.tm_mday
            # get only the latest snapshot for current date
            snapshots[timestamp] = WEB_ARCHIVE_URL + item[fields.timestamp] + \
                 "/" + item[fields.original]
    return snapshots.values()

APPS_SIZE_STATS = defaultdict(list)

for app_name, app_url in APPS_ITUNES_URL.items():
    print("# Processing APP: {}".format(app_name))

    app_stats = list()
    archive_pages = get_archive_pages(app_url)
    count = len(archive_pages)
    for current, page_url in enumerate(archive_pages):
        try:
            req = urllib.request.urlopen(page_url)
            if req is not None:
                print("Processing page #{}/{} ...".format(current + 1, count))
                content = req.read().decode(req.headers.get_content_charset('utf-8'))
                updated = re.search(REGEX_UPDATED, content)
                app_size = re.search(REGEX_APP_SIZE, content)
                if updated and app_size:
                    app_stats.append((updated.groupdict()["updated_date"],
                        app_size.groupdict()["app_size"]))
                else:
                    print("Can't regexp in {} for {}".format(page_url,
                        "updated_date" if updated is None else "app_size"))
            else:
                print("Request object for {} is empty".format(page_url))
        except urllib.error.URLError as e:
            print ("Can't access {} due to {}".format(page_url, e.reason))
    output = OUTPUT_FOLDER + app_name + ".json"
    with open(output, "w") as fp:
        print("Saving {} stats to {} ...".format(app_name, output))
        json.dump(app_stats, fp)
