import matplotlib.pyplot as plt
import mpld3
import sys
sys.path.append('/Users/nielseriksen/stock_data')

import yfinance_loader as yfl


def create_graph_html(ticker):
    stocks = yfl.download_tickers([ticker], False, return_only=['Adj Close']).ffill(axis=0)
    plt.switch_backend('Agg')
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.set_facecolor("black")
    ax.spines['bottom'].set_color('white')
    ax.xaxis.label.set_color('white')
    ax.tick_params(axis='x', colors='white')
    ax.plot(stocks, c='white')
    html = mpld3.fig_to_html(fig)
    return html
