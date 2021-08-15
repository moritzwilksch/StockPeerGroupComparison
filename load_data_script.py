
from IPython.display import display, Markdown
from pandas.core.base import DataError
import requests
import joblib
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import config
import random


api_key_fmp = random.choice(config.api_keys_fmp)


def load_data_assemble_output(tickers) -> pd.DataFrame:
    # tickers = ['KR', 'WMT', 'TGT', 'COST']
    # tickers = ['O', 'DLR', 'MPW', 'LTC']

    responses = {}

    for ticker in tickers:
        try:
            responses[ticker] = joblib.load(f"data/{ticker}_response.gz")
        except:
            try:
                response = requests.get(f"https://financialmodelingprep.com/api/v3/ratios/{ticker}?apikey={api_key_fmp}")
                if response.ok:
                    joblib.dump(response, f"data/{ticker}_response.gz")
                    responses[ticker] = joblib.load(f"data/{ticker}_response.gz")
                else:
                    raise DataError("Ticker does not exist")
            except:
                print(f"[ERROR] Fetching {ticker} did not work.")
                tickers.remove(ticker)

    all_dfs = {ticker: pd.DataFrame(responses[ticker].json()) for ticker in tickers}
    all_dfs = pd.concat(all_dfs)

    all_dfs['date'] = all_dfs['date'].astype('datetime64')
    all_dfs = (
        all_dfs
        .assign(year=all_dfs['date'].dt.year)
        .reset_index()
        .drop(['level_0', 'level_1'], axis=1)
    )

    # get most recent common year for all tickers
    years_as_sets = all_dfs.groupby('symbol')['year'].agg(set)
    largest_common_year = max(years_as_sets.iloc[0].intersection(*years_as_sets.values))

    mry = all_dfs.query("year == @largest_common_year").set_index('symbol')
    mry

    fields = [
        'grossProfitMargin',
        'netProfitMargin',
        'returnOnEquity',
        'returnOnCapitalEmployed',
        'dividendYield',
        'dividendPayoutRatio',
        'operatingCashFlowPerShare',
        'freeCashFlowPerShare',
        'debtEquityRatio',
        'cashPerShare',
        'priceEarningsRatio',
        'priceToFreeCashFlowsRatio',
        'priceFairValue',
    ]

    display_names = {'grossProfitMargin': 'Gross Profit Margin',
                     'netProfitMargin': 'Net Profit Margin',
                     'returnOnEquity': 'Return on Equity',
                     'returnOnCapitalEmployed': 'ROCE',
                     'dividendYield': 'Dividend Yield',
                     'dividendPayoutRatio': 'Dividend Payout Ratio',
                     'operatingCashFlowPerShare': 'OCF/Share',
                     'freeCashFlowPerShare': 'FCF/Share',
                     'debtEquityRatio': 'Debt/Equity Ratio',
                     'cashPerShare': 'Cash/Share',
                     'priceEarningsRatio': 'PE Ratio',
                     'priceToFreeCashFlowsRatio': 'Price/FCF',
                     'priceFairValue': 'Price/FairValue',
                     'prevClose': 'Last Closing Price'
                     }

    rounding_rules = {
        'grossProfitMargin': 3,
        'netProfitMargin': 3,
        'returnOnEquity': 3,
        'returnOnCapitalEmployed': 3,
        'debtEquityRatio': 1,
        'operatingCashFlowPerShare': 2,
        'freeCashFlowPerShare': 2,
        'cashPerShare': 2,
        'dividendPayoutRatio': 3,
        'priceEarningsRatio': 1,
        'priceToFreeCashFlowsRatio': 1,
        'dividendYield': 3,
        'priceFairValue': 1,
    }

    pct_rows = [
        'grossProfitMargin',
        'netProfitMargin',
        'returnOnEquity',
        'returnOnCapitalEmployed',
        'dividendPayoutRatio',
        'dividendYield',
    ]

    output = (
        mry[fields]
        .round(rounding_rules)
        .applymap(lambda s: f"{s:,}" if s else "0")
        .T
    )

    output.loc[pct_rows] = output.loc[pct_rows].applymap(lambda s: f"{float(s):.1%}")

    try:
        response = requests.get(
            "https://sandbox.tradier.com/v1/markets/quotes",
            headers=config.tradier_headers,
            params={
                'symbols': ",".join(tickers)
            }
        )

        resp = response.json()

        prevclose = pd.DataFrame(resp.get('quotes').get('quote')).set_index('symbol')['prevclose'].to_frame().T
    except:
        print("[ERROR] Could not fetch previous close.")
        prevclose = pd.Series(np.full(len(tickers), np.nan), index=tickers).to_frame().T

    output = pd.concat((prevclose, output))
    output = output.rename(display_names)

    return output, tickers
