import polars as pl
import pandas as pd
import numpy as np
import datetime
from typing import Type
import matplotlib.pyplot as plt
from matplotlib import patheffects

import Account
import Performance

class backtest:
    """
    Runs backtest and produces performance metrics 

    Parameters
    ----------
    init_capital: float
        Initial capital
    pl_df: pl.DataFrame
        Polars DataFrame containing prices and signals
    tickers: list[str]
        List of Tickers
    slippage: float
        Transaction cost, bid ask spread
    downside_risk: float
        For Sortino Ratio computation
    metric: list[str]
        List of Metrics for computation
    chart: bool
        T/F to plot charts
    timeframe: list[int]
        Timeframe for performance computation in years
    """
    def __init__(
            self,
            init_capital: float,
            pl_df: pl.DataFrame,
            tickers: list[str],
            slippage: float,
            downside_risk: float,
            metric: list[str],
            chart: bool,
            timeframe: list[int]
        ) -> None:

        self.account = Account.account(init_cash = init_capital)
        self.pos = Account.position(tickers)
        self.pl_df = pl_df[['Date'] + tickers + [col for col in pl_df.columns if 'signal' in col]]
        self.tickers = tickers
        self.signals = [col for col in pl_df.columns if 'signal' in col]
        self.slippage = slippage
        self.downside_risk = downside_risk
        self.dates = pl.Series(pl_df['Date'])
        self.timeframe = timeframe
        self.metrics = metric
        self.charts = chart

        self.port_ret = None
    
    def run(self):
        """
        Runs backtest based on trading signals and computes portfolio returns
        1. For each trading day, check for buy and sell signals
        2. Execute sell signals first, updating cash balance
        3. Execute buy signals
        4. Update daily asset value and account value

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        for date in self.dates:
            curr_day: pl.DataFrame = self.pl_df.filter(pl.col('Date') == date)
            curr_day_signal: pl.DataFrame = curr_day[self.signals]

            buy_signal: int = 1 if ((curr_day_signal == 1).sum_horizontal() > 0).any() else 0
            sell_signal: int = 1 if ((curr_day_signal == -1).sum_horizontal() > 0).any() else 0

            if sell_signal:
                for ticker in self.tickers:
                    if curr_day_signal[f'{ticker}_signal'][-1] == -1 and self.pos.position[ticker] != 0:
                        sell_value: float = curr_day[ticker][-1] * self.pos.position[ticker]
                        self.account.update_cash(sell_value * (1 - self.slippage))

                        self.pos.position[ticker] = 0
            
            if buy_signal:
                buy_ticker = []
                for ticker in self.tickers:
                    if curr_day_signal[f'{ticker}_signal'][-1] == 1 and self.pos.position[ticker] == 0:
                        buy_ticker.append(ticker)

                if self.account.cash > 0 and len(buy_ticker) > 0:
                    cash_allocation: float = self.account.cash / len(buy_ticker)
                    for ticker in buy_ticker:
                        curr_price: float = curr_day[ticker][-1]
                        if cash_allocation / curr_price > 1:
                            self.pos.position[ticker] = cash_allocation / curr_price
                            self.account.update_cash(-cash_allocation * (1 + self.slippage))
            
            today_asset_value: float = 0.0
            for ticker in self.tickers:
                today_asset_value += self.pos.position[ticker] * curr_day[ticker][-1]

            self.account.update_asset_value(today_asset_value)
            self.account.update_daily_account_value(date)

        self.port_ret: np.array = np.diff(self.account.daily_account_value['Account_Value']) / self.account.daily_account_value['Account_Value'][1:]
        self.port_ret: np.array = np.pad(self.port_ret, (1, 0), 'constant', constant_values = 0)

    def generate_performance(self):
        """
        computes rolling performance
        1. Cumulative returns
        2. Rolling Drawdown
        3. Rolling Annualized Sharpe Ratio
        4. Rolling Annualized Sortino Ratio

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        compute_port_perf: Type[Performance.performance] = Performance.performance(self.port_ret, 0)
        
        self.pl_df: pl.DataFrame = self.pl_df.with_columns(
            pl.Series(name = 'portfolio_cum_ret', values = compute_port_perf.compute_cum_rets()),
            pl.Series(name = 'portfolio_drawdown', values = compute_port_perf.compute_drawdown()),
        )
        
        for tf in self.timeframe:
            if len(self.pl_df) > tf:
                compute_port_perf: Type[Performance.performance] = Performance.performance(self.port_ret, tf)

                self.pl_df: pl.DataFrame = self.pl_df.with_columns(
                    # Sharpe
                    pl.Series(name = f'portfolio_{tf}Y_annualized_sharpe', values = compute_port_perf.compute_rolling_sharpe()),

                    # Sortino
                    pl.Series(name = f'portfolio_{tf}Y_annualized_sortino', values = compute_port_perf.compute_rolling_sortino(downside_risk = self.downside_risk))
                )

    def generate_report(self) -> None:
        '''
        Generates backtest report and plots based on timeframes and metrics

        Parameters
        ----------
        None

        Returns
        -------
        None
        '''
        print('--------------BACKTEST REPORT--------------')
        for metric in self.metrics:
            for tf in self.timeframe:
                if len(self.pl_df) > tf:
                    compute_port_perf: Type[Performance.performance] = Performance.performance(self.port_ret, tf)

                    port_cum_ret: np.array = compute_port_perf.compute_annualized_rets()
                    port_rolling_sharpe: np.array = np.nanmean(compute_port_perf.compute_rolling_sharpe())
                    port_rolling_sortino: np.array = np.nanmean(compute_port_perf.compute_rolling_sortino(downside_risk = self.downside_risk))
                    port_maxdd: np.array = compute_port_perf.compute_max_dd()
                    port_vol: np.array = compute_port_perf.compute_volatility()

                    print(f'T{tf}Y {metric}: {port_cum_ret}%') if metric == 'Annualized Return' else \
                    print(f'T{tf}Y Average Annualized {metric}: {round(port_rolling_sharpe, 2)}') if metric == 'Sharpe Ratio' else \
                    print(f'T{tf}Y Average Annualized {metric}: {round(port_rolling_sortino, 2)}') if metric == 'Sortino Ratio' else \
                    print(f'T{tf}Y {metric}: {port_maxdd}%') if metric == 'Max Drawdown' else \
                    print(f'T{tf}Y {metric}: {port_vol}%') if metric == 'Volatility' else print('')
            print('###############################################')

        ############
        ## Plots ##
        ############
        if self.charts:
            to_plot: list[int] = []
            for tf in self.timeframe:
                if any([i for i in self.pl_df.columns if str(tf) in i]):
                    to_plot.append(tf)

            n_rows = 2

            fig, main = plt.subplots(1, 2, figsize = (30,5), tight_layout = True)
            self.plotting_metrics(main, 0, 'cum_ret', 'Cumulative Returns (Log Scaled)')
            main[0].set_title(f'cum_ret (log scaled) \n Trade cumulative Returns: {(self.pl_df.select("portfolio_cum_ret")[-1].to_numpy().flatten() * 100).round(2)}%')
            self.plotting_metrics(main, 1, 'drawdown', 'Drawdown')

            fig2, axs = plt.subplots(n_rows, len(to_plot), sharex = False, figsize = (30,10), tight_layout = True)
            axs = axs.flatten()
            for tf in range(len(to_plot)):
                self.plotting_metrics(axs, tf, f'{to_plot[tf]}Y_annualized_sharpe', f'{to_plot[tf]}Y Rolling Sharpe')
                self.plotting_metrics(axs, tf + len(to_plot), f'{to_plot[tf]}Y_annualized_sortino', f'{to_plot[tf]}Y Rolling Sortino')
                
        print('--------------END------------------')
    
    def plotting_metrics(
            self, 
            ax: np.array, 
            i: int, 
            y: np.array, 
            title: str
        ) -> None:
        '''
        Plotter function

        Parameters
        ----------
        ax: np.array
            Subplot to plot the chart
        i: int
            Location on `ax` to plot the chart
        y: np.array
            Metric to plot
        title: string
            Title of chart

        Returns
        -------
        None
        '''
        
        x: np.array = self.pl_df.select('Date').to_numpy().flatten()

        y_port: np.array = self.pl_df.select(f'portfolio_{y}').to_numpy().flatten()

        y_port: np.array = y_port if y != 'cum_ret' else np.log(y_port)

        ax[i].plot(x, y_port, label = 'portfolio', color = 'b')
        ax[i].set_title(title)
        ax[i].axhline(0 if y != 'cum_ret' else 1, color = 'r', alpha = 0.2, linestyle = 'dashed')
        self.plot_crash(ax, i)
        ax[i].legend(fontsize = 'small');
    
    def plot_crash(
            self, 
            ax: np.array, 
            i: int
        ) -> None:
        '''
        Plots market crashes

        Parameters
        ----------
        ax: np.array
            Subplot to plot the chart
        i: int
            Location on `ax` to plot the chart

        Returns
        -------
        None
        '''

        financial_regimes: list[tuple[datetime.datetime, datetime.datetime, str]] = [
            (pd.to_datetime('2015-07-01'), pd.to_datetime('2015-12-31'), '2015 Chinese Market Crash'),
            (pd.to_datetime('2018-10-01'), pd.to_datetime('2018-12-24'), '2018 US-China Trade War'),
            (pd.to_datetime('2020-02-19'), pd.to_datetime('2020-03-23'), '2020 COVID-19'),
            (pd.to_datetime('2021-11-14'), pd.to_datetime('2022-12-25'), '2022 I/R Hike & Russia-Ukraine War')
        ]
        # Add shaded areas to indicate financial crisis boundaries
        label_offset: float = 0  # initial offset for label placement
        for crisis in financial_regimes:
            start_date, end_date, crisis_label = crisis
            ax[i].axvspan(start_date, end_date, color='red', alpha=0.3)
            # Calculate midpoint of the crisis period
            crisis_midpoint: float = start_date + (end_date - start_date) / 2
            # Shift label down by a certain offset
            effect = [patheffects.withStroke(linewidth=3, foreground='white')]  # Adding grey outline
            ax[i].text(crisis_midpoint, ax[i].get_ylim()[1]*0.9 - label_offset, crisis_label, verticalalignment='top', horizontalalignment='center', path_effects=effect)

            offset = ax[i].get_ylim()[1] / 8 if int(ax[i].get_ylim()[1]) != 0.0 else -ax[i].get_ylim()[0] / 8
            label_offset += offset  # increase offset for the next label    
