from django import forms
import os

downloaded_tickers = [x[0:-5] if '.pbz2' in x else '' for x in os.listdir('/Users/nielseriksen/stock_data/raw_data')]
downloaded_tickers.sort()

#downloaded_tickers = {'stocks': downloaded_tickers}
downloaded_tickers = [(str(stock), stock) for stock in downloaded_tickers]


class PickStockForm(forms.Form):
    stocks = forms.ChoiceField(choices=downloaded_tickers)