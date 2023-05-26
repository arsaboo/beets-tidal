"""
Adds Tidal support to the autotagger.
"""

import collections
import json
import re
import time
from datetime import datetime
from io import BytesIO

import confuse
import requests
import tidalapi
from beets import config, importer, ui
from beets.autotag.hooks import AlbumInfo, Distance, TrackInfo
from beets.dbcore import types
from beets.library import DateType
from beets.plugins import BeetsPlugin, get_distance
from PIL import Image


def extend_reimport_fresh_fields_item():
    """Extend the REIMPORT_FRESH_FIELDS_ITEM list from a plugin."""
    importer.REIMPORT_FRESH_FIELDS_ITEM.extend([
        'tidal_album_id', 'tidal_track_id', 'tidal_artist_id',
        'tidal_track_popularity', 'tidal_alb_popularity',
        'tidal_updated'])

class TidalPlugin(BeetsPlugin):
    data_source = 'Tidal'

    item_types = {
        'tidal_duration': types.INTEGER,
        'tidal_album_id': types.INTEGER,
        'tidal_track_id': types.INTEGER,
        'tidal_artist_id': types.INTEGER,
        'tidal_track_popularity': types.INTEGER,
        'tidal_alb_popularity': types.INTEGER,
        'tidal_updated': DateType(),
    }

    def __init__(self):
        super().__init__()
        self.config.add({
            'source_weight': 0.5,
        })
        extend_reimport_fresh_fields_item()

        # Adding defaults.
        config['tidal'].add({
            'tidal_attempts': 5,
            'tidal_sleep_interval': [5, 30],
            'tidal_session_file': 'tidal.json'})

        sessionfile = config["tidal"]["tidal_session_file"].get(
            confuse.Filename(in_app_dir=True))

        self.session = self.load_session(sessionfile)

        if not self.session:
            self._log.debug("JSON file corrupted or does not exist, \
                            performing simple OAuth login.")
            self.session = tidalapi.Session()
            self.session.login_oauth_simple()
            self.save_session(sessionfile)

    def load_session(self, sfile):
        self._log.debug(f"Loading tidal session from {sfile}")
        s = tidalapi.Session()
        try:
            with open(sfile, "r") as file:
                data = json.load(file)
                if s.load_oauth_session(data["token_type"],
                                        data["access_token"],
                                        data["refresh_token"],
                                        datetime.fromtimestamp(
                                            data["expiry_time"])):
                    return s
                else:
                    return None
        except FileNotFoundError:
            return None

    def save_session(self, sfile):
        self._log.debug(f"Saving tidal session to {sfile}")
        with open(sfile, "w") as file:
            json.dump({
                "token_type": self.session.token_type,
                "access_token": self.session.access_token,
                "refresh_token": self.session.refresh_token,
                "expiry_time": self.session.expiry_time.timestamp()},
                file, indent=2)

    def commands(self):
        """Add beet UI commands to interact with Tidal."""
        tidalsync_cmd = ui.Subcommand(
            'tidalsync', help=f'Update {self.data_source} views')
        tidalsync_cmd.parser.add_option(
            '-f', '--force', dest='force_refetch',
            action='store_true', default=False,
            help='re-download data when already present'
        )

        def func(lib, opts, args):
            items = lib.items(ui.decargs(args))
            self.tidalsync(items, ui.should_write(), opts.force_refetch)

        tidalsync_cmd.func = func
        return [tidalsync_cmd]

    def tidalsync(self, items, write, force):
        """Obtain track information from Tidal."""
        self._log.debug('Total {} tracks', len(items))

        for index, item in enumerate(items, start=1):
            self._log.info('Processing {}/{} tracks - {} ',
                           index, len(items), item)
            # If we're not forcing re-downloading for all tracks, check
            # whether the popularity data is already present
            if not force:
                if 'tidal_track_popularity' in item:
                    self._log.debug('Popularity already present for: {}',
                                    item)
                    continue
            try:
                tidal_track_id = item.tidal_track_id
            except AttributeError:
                self._log.debug('No track_id present for: {}', item)
                continue

            popularity = self.track_popularity(tidal_track_id)
            item['tidal_track_popularity'] = popularity
            item['spotify_updated'] = time.time()
            item.store()
            if write:
                item.try_write()

    def track_popularity(self, track_id):
        """Fetch a track popularity by its Tidal ID."""
        try:
            track_data = self.session.track(id)
        except Exception as e:
            self._log.debug('Track not found: {}. Error: {}',
                            track_id, format(e))
            return None
        popularity = track_data.popularity
        self._log.debug('Popularity of {} is {}', track_id, popularity)
        return popularity

    def album_distance(self, items, album_info, mapping):

        """Returns the album distance.
        """
        dist = Distance()
        if album_info.data_source == 'Tidal':
            dist.add('source', self.config['source_weight'].as_number())
        return dist

    def track_distance(self, item, track_info):

        """Returns the Tidal source weight and the maximum source weight
        for individual tracks.
        """
        return get_distance(
            data_source=self.data_source,
            info=track_info,
            config=self.config
        )

    def get_albums(self, query):
        """Returns a list of AlbumInfo objects for a Tidal search query.
        """
        # Strip non-word characters from query. Things like "!" and "-" can
        # cause a query to return no results, even if they match the artist or
        # album title. Use `re.UNICODE` flag to avoid stripping non-english
        # word characters.
        query = re.sub(r'(?u)\W+', ' ', query)
        # Strip medium information from query, Things like "CD1" and "disk 1"
        # can also negate an otherwise positive result.
        query = re.sub(r'(?i)\b(CD|disc)\s*\d+', '', query)
        albums = []
        self._log.debug('Searching Tidal for: {}', query)
        try:
            data = self.session.search(query, models=[tidalapi.album.Album])
        except Exception as e:
            self._log.debug('Invalid Search Error: {}'.format(e))
        if data.get('top_hit'):
            id = data.get('top_hit').id
            album_details = self.session.album(id)
            album_info = self.get_album_info(album_details)
            albums.append(album_info)
        return albums

    def get_tracks(self, query):
        """Returns a list of TrackInfo objects for a JioSaavn search query.
        """
        # Strip non-word characters from query. Things like "!" and "-" can
        # cause a query to return no results, even if they match the artist or
        # album title. Use `re.UNICODE` flag to avoid stripping non-english
        # word characters.
        query = re.sub(r'(?u)\W+', ' ', query)
        # Strip medium information from query, Things like "CD1" and "disk 1"
        # can also negate an otherwise positive result.
        query = re.sub(r'(?i)\b(CD|disc)\s*\d+', '', query)
        tracks = []
        self._log.debug('Searching Tidal for track: {}', query)
        try:
            data = self.session.search(query, models=[tidalapi.media.Track])
        except Exception as e:
            self._log.debug('Invalid Search Error: {}'.format(e))
        if data.get('top_hit'):
            id = data.get('top_hit').id
            song_details = self.session.track(id)
            song_info = self._get_track(song_details)
            tracks.append(song_info)
        return tracks

    def candidates(self, items, artist, release, va_likely, extra_tags=None):
        """Returns a list of AlbumInfo objects for JioSaavn search results
        matching release and artist (if not various).
        """
        if va_likely:
            query = release
        else:
            query = f'{release} {artist}'
        try:
            return self.get_albums(query)
        except Exception as e:
            self._log.debug('Tidal album search Error: {}'.format(e))
            return []

    def item_candidates(self, item, artist, title):
        """Returns a list of TrackInfo objects for Tidal search results
        matching title and artist.
        """
        query = f'{title} {artist}'
        try:
            return self.get_tracks(query)
        except Exception as e:
            self._log.debug('Tidal track search Error: {}'.format(e))
            return []

    def get_album_info(self, item):
        """Returns an AlbumInfo object for a Tidal album.
        """
        album = item.name.replace("&quot;", "\"")
        tidal_album_id = item.id
        artist_id = item.artist.id
        year = item.year
        popularity = item.popularity
        explicit = item.explicit
        if hasattr(item, 'isrc'):
            isrc = item.isrc
        else:
            isrc = None
        label = item.copyright
        url = item.image(1280)
        if self.is_valid_image_url(url):
            cover_art_url = url
        else:
            cover_art_url = None
        if item.release_date is not None:
            releasedate = item.release_date
            # get year from a datetime object
            year = releasedate.year
            month = releasedate.month
            day = releasedate.day
        else:
            year = None
            month = None
            day = None
        artists = item.artist.name
        all_tracks = self.session.album(tidal_album_id).tracks()
        tracks = []
        medium_totals = collections.defaultdict(int)
        for i, song in enumerate(all_tracks, start=1):
            track = self._get_track(song)
            track.index = i
            medium_totals[track.medium] += 1
            tracks.append(track)
        for track in tracks:
            track.medium_total = medium_totals[track.medium]
        return AlbumInfo(album=album,
                         album_id=tidal_album_id,
                         tidal_album_id=tidal_album_id,
                         artist=artists,
                         artist_id=artist_id,
                         tidal_artist_id=artist_id,
                         tidal_alb_popularity=popularity,
                         explicit=explicit,
                         isrc=isrc,
                         tracks=tracks,
                         year=year,
                         month=month,
                         day=day,
                         mediums=max(medium_totals.keys()),
                         data_source=self.data_source,
                         cover_art_url=cover_art_url,
                         label=label,
                         tidal_updated=time.time(),
                         )

    def _get_track(self, track_data):
        """Convert a Tidal song object to a TrackInfo object.
        """
        if track_data.duration:
            length = track_data.duration
        else:
            length = None
        print(track_data.id)
        # Get track information for Tidal tracks
        return TrackInfo(
            title=track_data.name.replace("&quot;", "\""),
            track_id=track_data.id,
            tidal_track_id=track_data.id,
            artist=track_data.artist.name,
            album=track_data.album.name.replace("&quot;", "\""),
            tidal_artist_id=track_data.artist.id,
            length=length,
            data_source=self.data_source,
            isrc=track_data.isrc,
            tidal_track_popularity=track_data.popularity,
            tidal_updated=time.time(),
        )

    def album_for_id(self, release_id):
        """Fetches an album by its Tidal ID and returns an AlbumInfo object
        """
        if "tidal.com" in release_id:
            release_id = release_id.split('/')[-1]
        self._log.debug('Searching for album {0}', release_id)
        try:
            album_details = self.session.album(release_id)
        except Exception:
            return None
        return self.get_album_info(album_details)

    def track_for_id(self, track_id):
        """Fetches a track by its Tidal ID and returns a TrackInfo object
        """
        if "tidal.com" in track_id:
            track_id = track_id.split('/')[-1]
        self._log.debug('Searching for track {0}', track_id)
        try:
            track_details = self.session.track(track_id)
        except Exception:
            return None
        return self._get_track(track_details)

    def is_valid_image_url(self, url):
        try:
            response = requests.get(url)
            Image.open(BytesIO(response.content))
            return True
        except Exception as e:
            self._log.debug('Invalid Image URL: {}'.format(e))
            return False
