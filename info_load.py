import yfinance as yf
import pandas as pd


tickers = ['AAPL', 'MSFT', 'TSLA']

inf = yf.Tickers(tickers)
stocks = inf.download(group_by='tickers', actions=False)

info = [ticker.info for ticker in inf.tickers]



print(pd.DataFrame(info).set_index(['symbol']))