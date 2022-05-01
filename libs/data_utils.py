# -*- coding: UTF-8 -*-
#

"""Functions to process data"""

from __future__ import absolute_import, unicode_literals

import re
from xbmc import Actor
from collections import namedtuple
from .utils import url_fix, logger
from . import cache, tsdb

try:
    from typing import Optional, Text, Dict, List, Any  # pylint: disable=unused-import
    from xbmcgui import ListItem  # pylint: disable=unused-import
    InfoType = Dict[Text, Any]  # pylint: disable=invalid-name
except ImportError:
    pass

TAG_RE = re.compile(r'<[^>]+>')

# Regular expressions are listed in order of priority.
SHOW_ID_REGEXPS = [r'(thesportsdb)\.com/league/(\d+)']

CLEAN_PLOT_REPLACEMENTS = (
    ('<b>', '[B]'),
    ('</b>', '[/B]'),
    ('<i>', '[I]'),
    ('</i>', '[/I]'),
    ('</p><p>', '[CR]'),
)

UrlParseResult = namedtuple(
    'UrlParseResult', ['provider', 'show_id'])


def _clean_plot(plot):
    # type: (Text) -> Text
    """Replace HTML tags with Kodi skin tags"""
    for repl in CLEAN_PLOT_REPLACEMENTS:
        plot = plot.replace(repl[0], repl[1])
    plot = TAG_RE.sub('', plot)
    return plot


def _set_cast(episode_info, vtag):
    # type: (InfoType, ListItem) -> ListItem
    """Save rosters info to list item"""
    hometeam = {'idTeam': episode_info.get('idHomeTeam'),
                'strName': episode_info.get('strHomeTeam')}
    awayteam = {'idTeam': episode_info.get('idAwayTeam'),
                'strName': episode_info.get('strAwayTeam')}
    cast = []
    order = 1
    for team in [hometeam, awayteam]:
        if team['idTeam'] and team['strName']:
            players = tsdb.load_roster_info(team['idTeam'], team['strName'])
            if not players:
                continue
            for player in players:
                person = {'name': player.get('strPlayer', ''),
                          'role': '%s - %s' % (player.get('strPosition', ''), team['strName']),
                          'order': order, }
                thumb = None
                rawthumb = player.get('strThumb')
                if rawthumb:
                    thumb = url_fix(rawthumb)
                cast.append(
                    Actor(person['name'], person['role'], person['order'], thumb))
                order = order + 1
    if cast:
        vtag.setCast(cast)


def _add_season_info(show_info, vtag):
    # type: (InfoType, ListItem) -> ListItem
    """Add info for league seasons"""
    season_list = tsdb.load_season_info(show_info.get('idLeague', '0'))
    if not season_list:
        return []
    seasons = []
    for season in season_list:
        season_name = season.get('strSeason')
        if season_name:
            season_num = int(season_name[:4])
            logger.debug(
                'adding information for season %s to list item' % season_name)
            if vtag:
                vtag.addSeason(season_num, season_name)
            seasons.append({'season_num': season_num,
                           'season_name': season_name})
    return seasons


def _set_artwork(images, list_item):
    vtag = list_item.getVideoInfoTag()
    fanart_list = []
    for image_type, image in images:
        if image:
            theurl = url_fix(image)
            if image_type == 'fanart':
                fanart_list.append({'image': theurl})
            else:
                previewurl = theurl + '/preview'
                vtag.addAvailableArtwork(
                    theurl, art_type=image_type, preview=previewurl)
    if fanart_list:
        list_item.setAvailableFanart(fanart_list)
    return list_item


def set_episode_artwork(episode_info, list_item):
    """Set available images for a show"""
    images = []
    images.append(('thumb', episode_info.get('strThumb')))
    images.append(('thumb', episode_info.get('strFanart')))
    images.append(('fanart', episode_info.get('strFanart')))
    images.append(('fanart', episode_info.get('strThumb')))
    return _set_artwork(images, list_item)


def set_show_artwork(show_info, list_item):
    """Set available images for a show"""
    images = []
    images.append(('fanart', show_info.get('strFanart1')))
    images.append(('fanart', show_info.get('strFanart2')))
    images.append(('fanart', show_info.get('strFanart3')))
    images.append(('fanart', show_info.get('strFanart1')))
    images.append(('poster', show_info.get('strPoster')))
    images.append(('banner', show_info.get('strBanner')))
    return _set_artwork(images, list_item)


def add_main_show_info(list_item, show_info, full_info=True):
    # type: (ListItem, InfoType, bool) -> ListItem
    """Add main show info to a list item"""
    vtag = list_item.getVideoInfoTag()
    showname = show_info.get('strLeague')
    plot = _clean_plot(show_info.get('strDescriptionEN', ''))
    vtag.setTitle(showname)
    vtag.setOriginalTitle(showname)
    vtag.setTvShowTitle(showname)
    vtag.setPlot(plot)
    vtag.setPlotOutline(plot)
    vtag.setMediaType('tvshow')
    vtag.setEpisodeGuide(str(show_info['idLeague']))
    vtag.setYear(int(show_info.get('intFormedYear', '')[:4]))
    vtag.setPremiered(show_info.get('dateFirstEvent', ''))
    if full_info:
        vtag.setUniqueID(show_info.get('idLeague'),
                         type='tsdb', isDefault=True)
        vtag.setGenres([show_info.get('strSport', '')])
        tvrights = show_info.get('strTvRights', '')
        if tvrights:
            studios = tvrights.split('\r\n')
            if studios:
                vtag.setStudios(studios)
        vtag.setCountries([show_info.get('strCountry', '')])
        list_item = set_show_artwork(show_info, list_item)
        show_info['seasons'] = _add_season_info(show_info, vtag)
        cache.cache_show_info(show_info)
#        _set_cast(show_info['credits']['cast'], vtag)
    else:
        image = show_info.get('strPoster')
        if image:
            theurl = url_fix(image)
            previewurl = theurl + '/preview'
            vtag.addAvailableArtwork(
                theurl, art_type='poster', preview=previewurl)
    logger.debug(
        'adding sports league information for %s to list item' % showname)
    return list_item


def add_episode_info(list_item, episode_info, full_info=True):
    # type: (ListItem, InfoType, bool) -> ListItem
    """Add episode info to a list item"""
    season = episode_info.get('strSeason', '0000')[:4]
    episode = episode_info.get('strEpisode', '0')
    title = episode_info.get('strEvent', 'Episode ' + episode)
    vtag = list_item.getVideoInfoTag()
    vtag.setSeason(int(season))
    vtag.setEpisode(int(episode))
    vtag.setMediaType('episode')
    air_date = episode_info.get('dateEvent')
    if air_date:
        vtag.setFirstAired(air_date)
        if not full_info:
            title = '%s.%s.%s' % (episode_info.get(
                'strLeague', ''), air_date.replace('-', ''), title)
    vtag.setTitle(title)
    if full_info:
        vtag.setTitle(title)
        raw_plot = episode_info.get('strDescriptionEN')
        if raw_plot:
            plot = _clean_plot(episode_info.get('strDescriptionEN', ''))
            vtag.setPlot(plot)
            vtag.setPlotOutline(plot)
        if air_date:
            vtag.setPremiered(air_date)
        list_item = set_episode_artwork(episode_info, list_item)
        _set_cast(episode_info, vtag)
    logger.debug('adding episode information for S%sE%s - %s to list item' %
                 (season, episode, title))
    return list_item


def parse_nfo_url(nfo):
    # type: (Text) -> Optional[UrlParseResult]
    """Extract show ID from NFO file contents"""
    sid_match = None
    for regexp in SHOW_ID_REGEXPS:
        logger.debug('trying regex to match service from parsing nfo:')
        logger.debug(regexp)
        show_id_match = re.search(regexp, nfo, re.I)
        if show_id_match:
            logger.debug('match group 1: ' + show_id_match.group(1))
            logger.debug('match group 2: ' + show_id_match.group(2))
            if show_id_match.group(1) == "thesportsdb":
                sid_match = UrlParseResult(
                    show_id_match.group(1), show_id_match.group(2))
                break
    return sid_match


def parse_media_id(title):
    title = title.lower()
    if title.startswith('tt') and title[2:].isdigit():
        # IMDB ID works alone because it is clear
        return {'type': 'imdb_id', 'title': title}
    # IMDB ID with prefix to match
    elif title.startswith('imdb/tt') and title[7:].isdigit():
        # IMDB ID works alone because it is clear
        return {'type': 'imdb_id', 'title': title[5:]}
    elif title.startswith('tmdb/') and title[5:].isdigit():  # TVDB ID
        return {'type': 'tmdb_id', 'title': title[5:]}
    elif title.startswith('tvdb/') and title[5:].isdigit():  # TVDB ID
        return {'type': 'tvdb_id', 'title': title[5:]}
    return None
