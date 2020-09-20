import pandas as pd
import numpy as np
import yfinance_loader as yfl
import matplotlib.pyplot as plt


def get_returns(prices):
    cleaned = pd.DataFrame(prices).dropna()
    return cleaned.pct_change(fill_method="ffill").dropna()


def get_covar_matrix(returns):
    return pd.DataFrame(returns).cov()


def min_var_weights(cov_matrix):
    ones = np.ones(len(cov_matrix))
    inverted_cov = pd.DataFrame(np.linalg.pinv(cov_matrix.values), cov_matrix.columns, cov_matrix.index)
    weights = np.dot(inverted_cov, ones)
    return weights/sum(weights)


def efficient_weights(cov_matrix, mean_returns):
    mean = np.array(mean_returns.values)
    inverted_cov = pd.DataFrame(np.linalg.pinv(cov_matrix.values), cov_matrix.columns, cov_matrix.index)
    weights = np.dot(inverted_cov, mean)
    return weights/sum(weights)


def yearly_returns(prices):
    returns = prices.asfreq('D').ffill().asfreq('AS').pct_change().dropna().mean()
    if returns.isna().sum() > 0:
        return prices.iloc[-1, :]/prices.iloc[0, :]-1
    return returns


def portfolio_value(endowment, weights, prices):
    initial_investment = endowment * weights
    amounts = initial_investment / prices.iloc[0, :]
    value = pd.DataFrame(amounts * prices).sum(axis=1)
    return value


#yfl.clean_raw_files()

tickers = pd.read_csv('ticker_lists/swedish_first_north.csv', header=None)
tickers = tickers[0].to_list()
tickers = [x.replace(' ', '-') + '.ST' for x in tickers]
#tickers = ['SPY', 'VOO']
#tickers = ['JYSK.CO', 'DANSKE.CO', 'RILBA.CO', 'JUTBK.CO', 'NDA-DK.CO', 'VJBA.CO',
#           'SYDB.CO', 'SPNO.CO', 'MNBA.CO', 'FYNBK.CO', 'SKJE.CO', 'LOLB.CO', 'SALB.CO', 'DJUR.CO']
prices = yfl.download_tickers(tickers, False, return_only=['Adj Close'], min_period='3y').dropna()
returns = get_returns(prices)


cov = get_covar_matrix(returns)
min_var = min_var_weights(cov)
efficient = efficient_weights(cov, yearly_returns(prices))
endowment = 100000

portfolio_min = portfolio_value(endowment, min_var, prices)
portfolio_eff = portfolio_value(endowment, efficient, prices)


compare = 'SPY'
spx = yfl.download_tickers([compare], False, return_only=['Adj Close'])[compare]
combined = pd.concat([portfolio_min, portfolio_eff], axis=1).join(spx, how='left').ffill()
combined.columns = ['Portfolio min', 'Porfolio eff', compare]
normalized = combined*100/combined.iloc[0, :]

print('\nEfficient:')
for stock in zip(tickers, efficient):
    print(stock[0], f'{stock[1]*100:.2f}%')

print('\nMin var:')
for stock in zip(tickers, min_var):
    print(stock[0], f'{stock[1]*100:.2f}%')




plt.style.use('seaborn-ticks')
plt.plot(normalized)
plt.yscale('log')
plt.legend(['Min var port', 'Efficient port', 'S&P500'])
plt.gcf().text(0.05, 0.95, tickers, fontsize=8)
plt.show()



