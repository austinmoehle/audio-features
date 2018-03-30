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


def saturdays_in_year(year, day_list=[5]):
    """Returns list of Saturdays in the given year.

    Parameters
    ----------
    year: int
        The year to generate dates from.
    day_list: list (ints)
        Days of the week to be generated (default: 5=Saturday).

    Returns
    -------
    list of datetime.date objects
        List of generated dates.
    """
    if year == datetime.date.today().year:
        return saturdays_in_current_year()
    if year > datetime.date.today().year:
        raise ValueError('Year past current year')
    start_date = datetime.date(year, 1, 1)
    end_date = datetime.date(year, 12, 31)
    tmp_list = []
    date_list = []
    for x in xrange((end_date - start_date).days + 1):
        tmp_list.append(start_date + datetime.timedelta(days=x))
    for date_record in tmp_list:
        if date_record.weekday() in day_list:
            date_list.append(date_record)
    return date_list


def saturdays_in_current_year(day_list=[5]):
    """Returns list of Saturdays (up through today's date) in current year.

    Parameters
    ----------
    day_list: list of ints
        Weekdays to be generated (default: 5=Saturday).

    Returns
    -------
    list of datetime.date objects
        List of generated dates.
    """
    year = datetime.date.today().year
    start_date = datetime.date(year, 1, 1)
    end_date = datetime.date.today()
    tmp_list = []
    date_list = []
    for x in xrange((end_date - start_date).days + 1):
        tmp_list.append(start_date + datetime.timedelta(days=x))
    for date_record in tmp_list:
        if date_record.weekday() in day_list:
            date_list.append(date_record)
    return date_list


def saturdays_in_date_range(start_date, end_date, day_list=[5]):
    """Returns list of Saturdays in the given year.

    Parameters
    ----------
    start_date, end_date : datetime.date objects
        Indicate the start and end (inclusive) of the date range.
    day_list : list of datetime.date objects
        The weekdays to generarte (default: 5=Saturday).

    Returns
    -------
    list of datetime.date objects
        List of generated dates.
    """
    tmp_list = []
    date_list = []
    for x in xrange((end_date - start_date).days + 1):
        tmp_list.append(start_date + datetime.timedelta(days=x))
    for date_record in tmp_list:
        if date_record.weekday() in day_list:
            date_list.append(date_record)
    return date_list


def add_from_date(df, chart, saturday):
    """Retrieves Billboard Hot 100 song rankings from one week and adds to the dataframe.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe to be updated with this week's data.
    chart : chart URL identifier
    saturday : datetime.date object
        The Saturday of the week to be retrieved.

    Examples
    --------
    add_from_date(df1, "hot-100", "2016-12-17")
    """
    text = requests.get("http://www.billboard.com/charts/" + chart + "/%s" %
                        str(saturday)).text
    soupy = BeautifulSoup(text, 'html.parser')
    date = str(saturday)
    try:
        for entry in soupy.find_all('article', {'class': 'chart-row'}):
            contents = entry.find('div', 'chart-row__title').contents
            title = contents[1].string.strip()
            if (contents[3].find('a')):
                artist = contents[3].a.string.strip()
            else:
                artist = contents[3].string.strip()
            rank = entry.select_one('.chart-row__current-week').string.strip()
            ID = entry.get('data-spotifyid')
            uri = entry.get('data-spotifyuri')
            row = [date, artist, title, rank, ID, uri]
            df.loc[len(df)] = row
    except AttributeError:
        print('Error retrieving data for date: ' + date)


def add_from_date_range(df, chart, start_date, end_date, log=True):
    """Add Billboard Hot 100 song rankings from the given date range (inclusive)."""
    for saturday in saturdays_in_date_range(start_date, end_date):
        add_from_date(df, chart, saturday)
        if log == True:
            print 'Added week: ' + saturday.strftime('%m/%d/%Y')


def add_from_year_range(df, chart, start_year, end_year, log=True):
    """Add Billboard Hot 100 song rankings from the given year range (inclusive)."""
    for year in xrange(start_year, end_year + 1):
        for saturday in saturdays_in_year(year):
            add_from_date(df, chart, saturday)
            if log == True:
                print 'Added week: ' + saturday.strftime('%m/%d/%Y')
        if log == True:
            print 'Added year: ' + str(year)


def generate_billboard_data(chart, start_date=None, end_date=None, start_year=None, end_year=None):
    """Compiles Billboard Hot 100 song rankings from a given date range.

    Parameters
    ----------
    start_date, end_date : datetime.date objects
        Bounds (inclusive) of the date range.
    start_year, end_year : int
        Bounds (inclusive) of the year range (used only if no date range is specified).

    If no ranges are specified, default to `start_year`=datetime.date(1960, 1, 2) and
    `end_year`=datetime.date.today().

    Returns
    -------
    pd.DataFrame
        A pandas Dataframe containing the columns:
            ['date', 'artist', 'title', 'rank', 'ID', 'uri']

    Usage
    -----
    df = generate_billboard_data("hot-100", start_year=1960, end_year=2016)
    """
    df = pd.DataFrame(columns=('date', 'artist', 'title', 'rank', 'ID', 'uri'))
    if start_date and end_date:
        add_from_date_range(df, start_date, end_date)
        return df
    start_year = start_year or datetime.date(1960, 1, 2).year
    end_year = end_year or datetime.date.today().year
    add_from_year_range(df, chart, start_year, end_year)
    return df


def spi_scoring_fn(rank):
    """Converts Billboard Hot 100 rank to a special score using the Song-Database SPI formula."""
    special_ranks_to_scores = {1: 250, 2: 150, 3: 120}
    if rank == 0 or rank == None:
        return 0
    try:
        return special_ranks_to_scores[rank]
    except KeyError:
        return 101 - rank


def compute_scores(df, scoring_function=spi_scoring_fn):
    """Computes total scores by song.

    Removes extraneous columns from dataframe, replaces Hot-100 ranks with scores, groups the
    dataframe by song ID, then computes the total score for each song.

    Parameters
    ----------
    df : pd.Dataframe
        Dataframe containing song data (ID, rank, title, artist).
    scoring_function: function
        Function used to map ranks to scores.

    Returns
    -------
    pd.DataFrame
        Dataframe grouped by {'ID', 'title', 'artist'} showing summed scores.
    """
    df_new = df.loc[:, ['ID', 'rank', 'title', 'artist']]
    df_new.loc[:, 'rank'] = pd.to_numeric(df_new.loc[:, 'rank'])
    df_new.loc[:, 'rank'] = df_new.loc[:, 'rank'].map(scoring_function)
    df_new = df_new.groupby(['ID'], as_index=False).sum() #title,artist
    df_new.sort_values(['rank'], ascending=False, inplace=True)
    df_new.reset_index(drop=True, inplace=True)
    return df_new


def merge_billboard_and_spotify_dataframes(df_billboard, df_spotify):
    """Merges dataframes containing Billboard and Spotify song data.

    Parameters
    ----------
    df_billboard : pd.Dataframe
        Dataframe grouped by ID and sorted by rank (descending):
            ['ID', 'rank', 'title', 'artist']
    df_spotify : pd.Dataframe
        Dataframe containing Spotify audio features:
            ['ID', 'acousticness', 'analysis_url', 'danceability',
             'duration_ms', 'energy', 'id', 'instrumentalness',
             'key', 'liveness', 'loudness', 'mode', 'speechiness',
             'tempo', 'time_signature', 'track_href', 'type',
             'uri', 'valence']
    Returns
    -------
    pd.Dataframe
        Merged dataframe grouped by ID and sorted by rank (descending).
    """
    new_bb = df_billboard.copy()
    new_feat = df_spotify.copy()
    new_bb['year'] = new_bb.apply(lambda x: datetime.datetime.strptime(x['date'], '%Y-%m-%d').year, axis=1)
    new_bb['score'] = new_bb.apply(lambda x: score_from_rank(int(x['rank'])), axis=1)
    grouped = new_bb.groupby(['ID', 'year'], sort=False)['score'].sum()
    grouped = grouped.reset_index()
    grouped = grouped.loc[grouped.groupby(['ID'])['score'].idxmax()]
    grouped = grouped.set_index('ID')
    grouped = grouped.loc[:, ['year']]

    new_feat = new_feat.set_index('ID')
    new_df = new_feat.join(grouped)
    return new_df
