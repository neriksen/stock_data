import os
import yfinance as yf
import datetime as dt
import bz2
import _pickle as cPickle
import pandas as pd
import monthdelta
import re


def download_tickers(tickers, force_update, **kwargs):
    """
    force_update = False
    
    return_only = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
    Used for selecting what to return. Leave out to return everything.
    
    min_period = 1d
    Only load stocks with at least this range of data. 
    Valid formats: 3d, 20mo, 5y
    """
    already_downloaded = local_tickers()
    tickers_to_download = []
    if force_update:
        tickers_to_download = tickers
    else:
        for ticker in tickers:             # If already downloaded, check if they need updates
            if ticker in already_downloaded:
                if ticker_needs_update(ticker):
                    tickers_to_download.append(ticker)
            else:
                tickers_to_download.append(ticker)

    not_downloaded = download_dump(tickers_to_download)
    tickers_to_load = [x for x in tickers if x not in not_downloaded]
    
    # Read stock data from file(s)
    return load_stocks(tickers_to_load, **kwargs)


def min_date_check_multiple(stock_data, tickers, min_date):
    good_tickers = []
    for ticker in tickers:
        data = clean_df(stock_data[ticker])
        if min_date_check(data, min_date):
            good_tickers.append(ticker)
    return good_tickers


def min_date_check(stock_data, min_date):
    if stock_data.index[0] < min_date:
        return True
    return False


def load_stocks(tickers, **kwargs):
    if len(tickers) > 1:
        data = pd.concat([decompress_pickle('/Users/nielseriksen/stock_data/raw_data/' + x + '.pbz2') for x in tickers],
                         axis=1, sort=True)
    else:
        data = decompress_pickle('/Users/nielseriksen/stock_data/raw_data/' + tickers[0] + '.pbz2')

    if 'return_only' in kwargs:
        data = data[kwargs['return_only']]
        cols = kwargs['return_only']
    else:
        cols = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']

    data = create_stock_columns(data, tickers, cols)

    try:
        data.index = pd.to_datetime(data.index, unit='ms')
    except ValueError:
        data.index = pd.to_datetime(data.index)

    tickers_to_keep = tickers
    if 'min_period' in kwargs:
        min_period = convert_period(kwargs['min_period'])
        tickers_to_keep = min_date_check_multiple(data, tickers, min_period)
        if not tickers_to_keep:
            raise ValueError(f'Warning: No tickers found. No data found before {min_period}'
                             f'. Change to something less restrictive')
    data = data[tickers_to_keep]

    return data


def local_tickers():
    tickers = [x[0:-5] if '.pbz2' in x else '' for x in
                          os.listdir('/Users/nielseriksen/stock_data/raw_data/')]
    tickers.remove('')
    return tickers


def ticker_needs_update(ticker):
    stock_data = decompress_pickle('/Users/nielseriksen/stock_data/raw_data/' + ticker + '.pbz2')
    date_modified = dt.datetime.fromtimestamp(
        os.path.getmtime('/Users/nielseriksen/stock_data/raw_data/' + ticker + '.pbz2')).date()

    if bad_local_data(stock_data) or date_modified == dt.date.today() or newest_date(stock_data) == last_weekday():
        return False
    return True


def bad_local_data(stock_data):
    if len(stock_data) < 2:
        return True
    return False


def newest_date(stock_data):
    date = stock_data.index[-1]
    if date == float:
        date = dt.datetime.fromtimestamp(date / 1000)
    date = date.date()
    return date


def create_stock_columns(stock_data, tickers, cols = ('Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume')):
    index = pd.MultiIndex.from_product([tickers, cols], names=['Stock ticker', 'Data type'])
    stock_data.columns = index
    return stock_data


def default_download(tickers, period='100y'):
    return create_stock_columns(yf.download(tickers, period=period, group_by='tickers'), tickers)


def download_dump(tickers):
    not_downloaded = []
    if tickers:
        data = default_download(tickers)
        for ticker in tickers:
            clean_data = clean_df(data[ticker])
            compressed_pickle(ticker, clean_data) if not bad_local_data(clean_data) else not_downloaded.extend([ticker])

    return not_downloaded


def last_weekday():
    todays_day = dt.date.today().day
    if todays_day in [5, 6]:
        return dt.date.today() - dt.timedelta(days=todays_day-4)
    else:
        return dt.date.today()
    
    
def clean_df(df):
    df = df.dropna(axis = 0, how='all')
    return df


def compressed_pickle(ticker, data):
    ticker = ticker[0] if isinstance(ticker, list) else ticker
    with bz2.BZ2File('/Users/nielseriksen/stock_data/raw_data/' + ticker + '.pbz2', 'w') as f:
        cPickle.dump(data, f)
        
        
def decompress_pickle(file):
    data = bz2.BZ2File(file, 'rb')
    return pd.DataFrame(cPickle.load(data), dtype='object')


def convert_period(date_string):
    if date_string != 'YTD':
        match = re.match(r"([0-9]+)([a-z]+)", date_string, re.I)
        assert match, 'Period must begin with number and end with string, like 3d, 4mo and 10y'
        items = match.groups()
        number, period = int(items[0]), items[1]
        assert period.upper() in ['D', 'MO', 'Y'], 'Period must be of form 10d, 2mo or 4y or ytd'
        if period.upper() == 'D':
            start_date = dt.date.today() + dt.timedelta(-number)
        if period.upper() == 'MO':
            start_date = dt.date.today() + monthdelta.monthdelta(-number)
        if period.upper() == 'Y':
            start_date = dt.date.today() + dt.timedelta(round(-number*365.2422, 0))
    else:
        start_date = dt.date(dt.date.today().year, 1, 1)
    return start_date


def clean_raw_files():
    for filename in os.listdir('/Users/nielseriksen/stock_data/raw_data'):
        if filename.endswith(".pbz2"): 
            df = pd.DataFrame(decompress_pickle('/Users/nielseriksen/stock_data/raw_data/' + filename))
            try:
                non_zeroes = len(df) - df.iloc[:, 4].isna().sum()
            except IndexError:
                non_zeroes = 0
            if non_zeroes < 2:
                os.remove('/Users/nielseriksen/stock_data/raw_data/' + filename)
            else:
                df = df.dropna(how='all', axis=0)
                ticker = filename.replace('.pbz2', '')
                compressed_pickle(ticker, df)