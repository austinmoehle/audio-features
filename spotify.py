from collections import defaultdict
import json
import numpy as np
import csv as csv
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import rcParams
import matplotlib.cm as cm
import matplotlib as mpl
import datetime
import requests
from bs4 import BeautifulSoup


charts = {'all': 'hot-100',
          'dance': 'dance-electronic-songs',
          'rnb': 'r-b-hip-hop-songs',
          'pop': 'pop-songs',
          'country': 'country-songs',
          'rock': 'rock-songs',
          'latin': 'latin-songs'}

start_dates = {'all': '1960-01-02',
               'dance': '2013-01-26',
               'rnb': '1962-01-06',
               'pop': '1993-01-02',
               'country': '1962-01-06',
               'rock': '2010-01-02',
               'latin': '1987-01-03'}

chart_list = ['all', 'country', 'dance', 'latin', 'pop', 'rnb', 'rock']


class TokenError(Exception):
    pass


class AudioFeatures(object):
    """Object to handle building a dataframe of audio features."""

    def __init__(self, features, token=None, features_list=None):
        """Creates an AudioFeatures object.

        Parameters
        ----------
        features : pd.DataFrame
            DataFrame grouped by the `spotifyID`s of interest.
        token : str
            Access token for the Spotify API.
            Can be modified manually with `set_token(token)`.
        """
        self.token = token
        self.features = features
        self.features_list = (features_list or
            ['acousticness', 'analysis_url', 'danceability', \
             'duration_ms', 'energy', 'id', 'instrumentalness', \
             'key', 'liveness', 'loudness', 'mode', 'speechiness', \
             'tempo', 'time_signature', 'track_href', 'type', \
             'uri', 'valence'])
        for name in self.features_list:
            if name not in self.features:
                self.features[name] = 'NaN'
        self.start_loc = 0


    def get_features_for_index(self, index):
        """Retrieves audio features from Spotify's Web API and updates those columns in self.features.

        Parameters
        ----------
        index : int
            The index in `self.features` to look up in the Spotify API.
        """
        spotifyID = str(self.features.loc[index, 'ID'])
        token_error_message = "Access error: bad token"
        link = "https://api.spotify.com/v1/audio-features/" + spotifyID
        headers = {"Authorization": "Bearer " + self.token}
        text = requests.get(link, headers=headers).text
        row = None
        try:
            row = pd.read_json(text, typ='series', orient='records')
        except ValueError:
            logging.info('Index %d - no data from Spotify record' % index)
            return
        self.test = row
        try:
            row['id']
        except KeyError:
            msg = row[0]['message']
            logging.info("Retrieval error %s for index %i." % (msg, index)
            if 'token' in message.lower():
                raise TokenError('Bad token')
            else:
                return
        self.features.loc[index, row.index.get_values()] = row


    def get_features_for_id(self, spotifyID):
        """Retrieves audio features from Spotify's Web API and updates those columns in self.features.

        Parameters
        ----------
        spotifyID : str
            The spotifyID in `self.features` to look up in the Spotify API.
        """
        index = self.features[str(self.features['ID']) == spotifyID].index[0]
        self.get_features_for_index(index)


    def retrieve_features(self, start_loc=None, end_loc=None):
        """Retrieves audio features from Spotify's Web API for all IDs.

        Parameters
        ----------
        start_loc : int
            Location of the first ID to retrieve in the `features` DataFrame.
            Used to resume retrieval if a previous attempt was interrupted.
        end_loc : int
            Location of the last ID to retrieve (exclusive).
        """
        start_loc = start_loc or self.start_loc
        if end_loc is None:
            end_loc = self.features.shape[0]
        else:
            end_loc = min(end_loc, self.features.shape[0])
        if start_loc >= end_loc or start_loc < 0:
            raise IndexError("Starting index ('start_loc') invalid.")
        self.start_loc = start_loc
        for i in xrange(self.start_loc, end_loc):
            try:
                self.get_features_for_index(i)
                if i % 100 == 0:
                    logging.info("Index %d successful (continuing until index %d)" %
                                 (i, self.features.shape[0]))
                self.start_loc = i + 1
            except TokenError:
                self.start_loc = i
                logging.info('Bad token! Refresh using set_token() then run again.')
                return


    def set_token(self, token):
        """Set Spotify API access token manually.

        Parameters
        ----------
        token : str
            Spotify API access token.
        """
        self.token = token


    def set_token_cc(self, client_id, client_secret):
        """Set Spotify access token using client-credentials flow.

        Parameters
        ----------
        client_id     | <---Both from Spotify app registration.
        client_secret | <---
        """
        OAUTH_TOKEN_URL = 'https://accounts.spotify.com/api/token'
        auth_header = base64.b64encode(client_id + ':' + client_secret)
        headers = {'Authorization': 'Basic %s' % auth_header}
        payload = {'grant_type': 'client_credentials'}
        response = requests.post(OAUTH_TOKEN_URL, data=payload,
            headers=headers, verify=True)
        if response.status_code is not 200:
            logging.info('error: code not 200')
        token_info = response.json()
        logging.info(token_info)
