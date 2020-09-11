from django.shortcuts import render
from django.http import HttpResponse
import os

def home(request):
    downloaded_tickers = [x[0:-5] if '.pbz2' in x else '' for x in os.listdir('/Users/nielseriksen/stock_data/raw_data')]
    downloaded_tickers = {'name': downloaded_tickers[i] for i in range(0, len(downloaded_tickers))}

    return render(request, 'stock_data_app/stock_data-graph.html', context=downloaded_tickers)