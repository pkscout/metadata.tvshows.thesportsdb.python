# -*- coding: UTF-8 -*-
#
# pylint: disable=missing-docstring

import json
import sys
import urllib.parse
from xbmcaddon import Addon

ADDON = Addon()

try:
    source_params = dict(urllib.parse.parse_qsl(sys.argv[2]))
except IndexError:
    source_params = {}
source_settings = json.loads(source_params.get('pathSettings', '{}'))

ENABTRAILER = source_settings.get(
    'enab_trailer', ADDON.getSettingBool('enab_trailer'))
PLAYERSOPT = source_settings.get(
    'players_opt', ADDON.getSettingString('players_opt')).lower()
VERBOSELOG = source_settings.get(
    'verboselog', ADDON.getSettingBool('verboselog'))
