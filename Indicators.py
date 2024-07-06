import polars as pl

class indicators:
    """
    Computes technical indicators
    1. Simple Moving Average
    2. Bollinger Bands

    Parameters
    ----------
    pl_df : pl.DataFrame
        Polars DataFrame containing close prices
    """
    def __init__(
            self,
            pl_df: pl.DataFrame,
        ) -> None:

        self.pl_df = pl_df
        
    def compute_SMA(
            self, 
            window: int
        ) -> pl.DataFrame:
        """
        Compute simple moving average

        Parameters
        ----------
        window : int
            Time window in days

        Returns
        -------
        pl.DataFrame
            Polars DataFrame with columns as SMA of tickers
        """
        pl_sma: pl.DataFrame = self.pl_df.drop('Date').with_columns(
            pl.all().rolling_mean(window_size = int(window))
        )

        pl_sma.columns = [col + '_sma' for col in pl_sma.columns]

        self.pl_df: pl.DataFrame = pl.concat([self.pl_df, pl_sma], how = 'horizontal')

        return pl_sma

    def compute_bbands(
            self,
            window: int,
            std: float
        ) -> None:
        """
        Compute Bollinger Bands

        Parameters
        ----------
        window : int
            Time window in days
        std : float
            Number of Standard Deviations 

        Returns
        -------
        None
        """
        pl_sma: pl.DataFrame = self.pl_df.select([col for col in self.pl_df.columns if 'sma' in col])

        pl_upper_bands: pl.DataFrame = pl_sma + std * pl_sma.with_columns(pl.all().rolling_std(window_size = window))
        pl_lower_bands: pl.DataFrame = pl_sma - std * pl_sma.with_columns(pl.all().rolling_std(window_size = window)) 

        pl_upper_bands.columns = [col.replace('_sma', '') + f'_{std}_upper_band' for col in pl_upper_bands.columns]
        pl_lower_bands.columns = [col.replace('_sma', '') + f'_{std}_lower_band' for col in pl_lower_bands.columns]

        self.pl_df: pl.DataFrame = pl.concat([self.pl_df, pl_upper_bands, pl_lower_bands], how = 'horizontal')
