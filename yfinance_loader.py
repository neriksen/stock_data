import os
import yfinance as yf
import datetime as dt
import bz2
import pickle
import _pickle as cPickle
import pandas as pd


def download_tickers(tickers, force_update, **kwargs):
    # Fetch downloaded ticker from raw_data
    downloaded_tickers = [x[0:-5] if '.pbz2' in x else '' for x in os.listdir('/Users/nielseriksen/stock_data/raw_data/')]
    downloaded_tickers.remove('')
    # Check if tickers already are downloaded
    tickers_to_download = []
    for ticker in tickers:             # If already downloaded, check if they need updates
        if ticker not in downloaded_tickers or force_update or update_ticker(ticker):
            tickers_to_download.append(ticker)
    not_downloaded = download_dump(tickers_to_download)
    tickers_to_load = [x for x in tickers if x not in not_downloaded]
    
    # Read stock data from file(s)
    return load_stocks(tickers_to_load, **kwargs)


def load_stocks(tickers, **kwargs):

    if len(tickers) > 1:
        data = pd.concat([decompress_pickle('/Users/nielseriksen/stock_data/raw_data/' + x + '.pbz2') for x in tickers], axis=1, sort=True)
    else:
        data = decompress_pickle('/Users/nielseriksen/stock_data/raw_data/' + tickers[0] + '.pbz2')
    
    if 'return_only' in kwargs:
        data = data[kwargs['return_only']]
        cols = kwargs['return_only']
    else:
        cols = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
        
    index = pd.MultiIndex.from_product([tickers, cols], names=['Stock ticker', 'Data type'])
    data.columns = index
    
    try:
        data.index = pd.to_datetime(data.index, unit='ms')
    except ValueError:
        data.index = pd.to_datetime(data.index)
        
    return data


def update_ticker(ticker):
    date_modified = dt.datetime.fromtimestamp(os.path.getmtime('/Users/nielseriksen/stock_data/raw_data/' + ticker + '.pbz2')).date()
    if date_modified != dt.date.today():  # In case stock has not been downloaded today
        last_bday = last_weekday()
        newest_date = decompress_pickle('/Users/nielseriksen/stock_data/raw_data/' + ticker + '.pbz2').index[-1]
        if newest_date == float:
            newest_date = dt.datetime.fromtimestamp(newest_date/1000)
        newest_date = newest_date.date()
        if newest_date != last_bday:
            return True 
        else:
            return False
    return False


def download_dump(tickers):
    not_downloaded = []
    if tickers != []:
        data = yf.download(tickers, period='100y', group_by='tickers')
        if len(tickers) > 1:
            for ticker in tickers:
                    clean_data = clean_df(data[ticker])
                    if len(clean_data) > 1:
                        compressed_pickle(ticker, clean_data)
                    else:
                        not_downloaded.extend(tickers)
        else:
            clean_data = clean_df(data)
            if len(clean_data) > 1:
                compressed_pickle(tickers, clean_data)
            else:
                not_downloaded.extend(tickers)
                
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
    data = cPickle.load(data)
    return data



def clean_raw_files():
    for filename in os.listdir('/Users/nielseriksen/stock_data/raw_data'):
        if filename.endswith(".pbz2"): 
            df = pd.DataFrame(decompress_pickle('/Users/nielseriksen/stock_data/raw_data/' + filename))
            non_zeroes = len(df) - df.iloc[:, 4].isna().sum()
            if non_zeroes < 2:
                os.remove('/Users/nielseriksen/stock_data/raw_data/' + filename)
            else:
                df = df.dropna(how='all', axis=0)
                ticker = filename.replace('.pbz2', '')
                compressed_pickle(ticker, df)