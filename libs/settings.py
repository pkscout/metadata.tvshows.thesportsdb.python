# -*- coding: UTF-8 -*-
#
# pylint: disable=missing-docstring

import json
import sys
import urllib.parse
from xbmcaddon import Addon

ADDON = Addon()
base_url = 'https://www.thesportsdb.com/api/v1/json/863583675235/{}'
SEARCH_URL = base_url.format('all_leagues.php')
SHOW_URL = base_url.format('lookupleague.php')
SEASON_URL = base_url.format('search_all_seasons.php')
EVENTLIST_URL = base_url.format('eventsseason.php')
EPISODE_URL = base_url.format('lookupevent.php')
HEADERS = (
    ('User-Agent', 'Kodi sports events scraper by pkscout; contact pkscout@kodi.tv'),
    ('Accept', 'application/json'),
)

try:
    source_params = dict(urllib.parse.parse_qsl(sys.argv[2]))
except IndexError:
    source_params = {}
source_settings = json.loads(source_params.get('pathSettings', '{}'))

VERBOSELOG = source_settings.get(
    'verboselog', ADDON.getSettingBool('verboselog'))
