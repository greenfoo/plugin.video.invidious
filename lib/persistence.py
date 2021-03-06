# -*- coding: utf-8 -*-


from __future__ import absolute_import, division, unicode_literals


import pickle

from collections import OrderedDict, defaultdict
from os.path import join, exists

from six import iterkeys, itervalues, iteritems
from six.moves.urllib.parse import unquote_plus, quote_plus

from utils import ListItem, getAddonProfile, getAddonId
from utils import buildUrl, localizedString, selectDialog, searchDialog


# utils ------------------------------------------------------------------------

def _dumpObject(obj, path):
    with open(path, "w+") as f:
        pickle.dump(obj, f, -1)

def _loadObject(path, default=None):
    if exists(path):
        with open(path, "r") as f:
            return pickle.load(f)
    return default


# feed -------------------------------------------------------------------------

_feed_path_ = join(getAddonProfile(), "feed.pickle")

def _dumpFeed(feed):
    return _dumpObject(feed, _feed_path_)

def _loadFeed():
    return _loadObject(_feed_path_, default=OrderedDict())


def addChannelToFeed(authorId, author):
    feed = _loadFeed()
    feed[authorId] = unquote_plus(author).decode("utf-8")
    _dumpFeed(feed)

def removeChannelsFromFeed():
    feed = _loadFeed()
    indices = selectDialog(list(itervalues(feed)), heading=30014, multi=True)
    if indices:
        keys = list(iterkeys(feed))
        for index in indices:
            del feed[keys[index]]
        _dumpFeed(feed)


def getFeed():
    return list(iterkeys(_loadFeed()))


# search history ---------------------------------------------------------------

class SearchQuery(object):

    _menus_ = [
        (30035, "RunScript({addonId},removeSearchQuery,{_type},{key})"),
        (30036, "RunScript({addonId},clearSearchHistory,{_type})")
    ]

    @classmethod
    def menus(cls, **kwargs):
        return [(localizedString(label).format(**kwargs),
                 action.format(addonId=getAddonId(), **kwargs))
                for label, action in cls._menus_]

    def __init__(self, _type, key, value):
        self.type = _type
        self.key = key
        self.value = value

    def item(self, url):
        return ListItem(
            self.value,
            buildUrl(url, action="search", type=self.type, q=self.value),
            isFolder=True,
            infos={"video": {"title": self.value, "plot": self.value}},
            contextMenus=self.menus(_type=self.type, key=self.key))


_search_history_path_ = join(getAddonProfile(), "search_history.pickle")

def _dumpSearchHistory(search_history):
    return _dumpObject(search_history, _search_history_path_)

def _loadSearchHistory():
    return _loadObject(_search_history_path_, default=defaultdict(OrderedDict))


def recordSearchQuery(_type, q):
    search_history = _loadSearchHistory()
    search_history[_type][quote_plus(q.encode("utf-8"))] = q
    _dumpSearchHistory(search_history)

def removeSearchQuery(_type, key):
    search_history = _loadSearchHistory()
    del search_history[_type][key]
    _dumpSearchHistory(search_history)

def clearSearchHistory(_type=None):
    search_history = _loadSearchHistory()
    if _type:
        search_history[_type].clear()
    else:
        search_history.clear()
    _dumpSearchHistory(search_history)


def newSearch(_type):
    q = searchDialog()
    if q:
        recordSearchQuery(_type, q)
        return q

def searchHistory(_type):
    return reversed([SearchQuery(_type, *item)
                     for item in iteritems(_loadSearchHistory()[_type])])

