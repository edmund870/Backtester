import polars as pl
import numpy as np

class performance:
    """
    Computes performance of portfolio        
    1. Cumulative Returns
    2. Annualized Returns
    3. Sharpe + Rolling Sharpe
    4. Sortino + Rolling Sortino
    5. Max Drawdown + Rolling Drawdown
    6. Volatility

    Parameters
    ----------
    portfolio_ret : np.array
        Array of portfolio returns
    years : int
        Trailing Years
    """
    def __init__(
            self,
            portfolio_ret: np.array,
            years: int
        ) -> None:

        self.years = years
        self.trade_days = 252
        self.timeframe = self.years * self.trade_days
        
        self.portfolio_ret = portfolio_ret[-self.timeframe : ]

        self.rolling = portfolio_ret

    def compute_cum_rets(self) -> np.array:
        return np.cumprod(self.rolling + 1)
    
    def compute_annualized_rets(self) -> float:
        annualized_return = np.prod(1 + self.portfolio_ret) ** (self.trade_days / self.timeframe) - 1
        return round(annualized_return * 100, 2)

    def compute_sharpe(self) -> float:
        sharpe = self.portfolio_ret.mean(axis = 0) / self.portfolio_ret.std(axis = 0) * np.sqrt(self.trade_days)
        return np.round(sharpe, 2)
    
    def compute_rolling_sharpe(self) -> list[float]:
        pad = np.zeros(self.timeframe - 1)
        rolling_mean = np.convolve(self.rolling, np.ones(self.timeframe) / self.timeframe, mode='valid')
        rolling_mean = np.concatenate((pad, rolling_mean), axis = 0)
        rolling_std = pl.Series(self.rolling).rolling_std(self.timeframe).to_numpy()

        rolling_sharpe = (rolling_mean / rolling_std) * np.sqrt(self.trade_days)
        return np.round(rolling_sharpe, 2)

    def compute_sortino(self, downside_risk: float) -> float:
        downside_ret = np.where(self.portfolio_ret < downside_risk, self.portfolio_ret, 0)
        downside_std = downside_ret.std(axis = 0)
        sortino = self.portfolio_ret.mean(axis = 0) / downside_std * np.sqrt(self.trade_days)
        return np.round(sortino, 2)
    
    def compute_rolling_sortino(self, downside_risk: float) -> list[float]:
        pad = np.zeros(self.timeframe - 1)
        rolling_mean = np.convolve(self.rolling, np.ones(self.timeframe) / self.timeframe, mode='valid')
        rolling_mean = np.concatenate((pad, rolling_mean), axis = 0)

        downside_ret = np.where(self.rolling < downside_risk, self.rolling, 0)
        rolling_downside_ret = pl.Series(downside_ret).rolling_std(self.timeframe).to_numpy()

        rolling_sortino = (rolling_mean / rolling_downside_ret) * np.sqrt(self.trade_days)
        
        return np.round(rolling_sortino, 2)

    def compute_max_dd(self) -> float:
        cum_ret = np.cumprod(1 + self.portfolio_ret)   
        cum_roll_max = np.maximum.accumulate(cum_ret)
        drawdowns = cum_roll_max - cum_ret
        max_drawdown = np.max(drawdowns / cum_roll_max)
        return round(max_drawdown * 100, 2)
    
    def compute_drawdown(self) -> list[float]:
        cum_ret = np.cumprod(1 + self.portfolio_ret)
        peak = np.maximum.accumulate(cum_ret)
        
        return cum_ret / peak - 1
    
    def compute_volatility(self) -> float:
        vol = self.portfolio_ret.std() * np.sqrt(self.trade_days)
        return np.round(vol * 100, 2)  
    