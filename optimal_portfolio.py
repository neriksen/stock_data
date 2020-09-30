import pandas as pd
import numpy as np
import yfinance_loader as yfl
import matplotlib.pyplot as plt
import seaborn as sns


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


def monthly_returns(prices):
    returns = prices.asfreq('D').ffill().asfreq('M').pct_change().dropna(how='all').mean()
    if returns.isna().sum() > 0:
        return prices.iloc[-1, :]/prices.iloc[0, :]-1
    return returns


#def dynamic_portfolio_value(endowment, weights, prices):
#     if isinstance(weights, np.ndarray):
#         weights = pd.DataFrame(np.full((prices.shape[0], prices.shape[1]), weights), index=prices.index)
#         weights.columns = prices.columns
#     print(weights)
#     amounts = [(endowment * weights.iloc[0, :]).divide(prices.iloc[0, :])]
#     value = [endowment]
#     #initial_investment = endowment * weights
#     for i in range(1, len(prices)):
#         value.append((amounts[-1]*prices.iloc[i, :]).sum())
#         amounts.append(weights.iloc[i, :]*value[-1]/prices.iloc[i, :])
#
#     return pd.DataFrame(value)


def portfolio_value(endowment, weights, prices):
    initial_investment = endowment*weights
    amounts = initial_investment/prices.iloc[0, :]
    value = pd.DataFrame(amounts*prices).sum(axis=1)
    return value


def split_prices(prices, start_window = 0, len_window = 600):
    return prices.iloc[start_window:start_window+len_window, :]


#yfl.clean_raw_files()

#tickers = pd.read_csv('ticker_lists/c25.csv', header=None)
#tickers = tickers[0].to_list()
#tickers = [x.replace(' ', '-') + '.ST' for x in tickers]
#tickers = ['VOO']
#tickers = ['JYSK.CO', 'DANSKE.CO', 'RILBA.CO', 'JUTBK.CO', 'NDA-DK.CO', 'VJBA.CO',
#           'SYDB.CO', 'SPNO.CO', 'MNBA.CO', 'FYNBK.CO', 'SKJE.CO', 'LOLB.CO', 'SALB.CO', 'DJUR.CO']
tickers = ['MBS', 'MGK', 'REMEDY.HE', 'PDX.ST']
prices = yfl.download_tickers(tickers, False, return_only=['Adj Close'], min_period='2Y').dropna()

start = 800
weights = []
rebalance_index = []
# for i in range(start, len(prices)-start, 30):
#     price = split_prices(prices, i, start)
#     print(price)
#     rebalance_index.append(price.index[-1])
#     cov = get_covar_matrix(get_returns(price))
#     efficient = efficient_weights(cov, yearly_returns(price)).tolist()
#     weights.append(efficient)

#eff_port_weights_raw = pd.DataFrame(weights, index=rebalance_index)

#dynamic_eff_weights = pd.DataFrame(eff_port_weights_raw, index=prices.index).ffill(axis=0)\
#    .fillna(1/len(eff_port_weights_raw.columns))
#print(dynamic_eff_weights)
#dynamic_eff_weights = yfl.create_stock_columns(dynamic_eff_weights, tickers, cols=['Adj Close'])

#print(len(dynamic_eff_weights), len(prices))

cov = get_covar_matrix(get_returns(prices))

min_var = min_var_weights(cov)
efficient = efficient_weights(cov, monthly_returns(prices))

endowment = 100000

portfolio_min = portfolio_value(endowment, min_var, prices)
portfolio_eff = portfolio_value(endowment, efficient, prices)
#portfolio_eff = portfolio_value(endowment, dynamic_eff_weights, prices)


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
fig, ax = plt.subplots(2, 1)
ax[0].plot(normalized)
#ax[0].set_yscale('log')
ax[0].legend(['Min var port', 'Efficient port', 'S&P500'])
sns.distplot(efficient, ax=ax[1])
fig.text(0.05, 0.95, tickers, fontsize=8)
plt.show()



