import polars as pl

class strategy():
    """
    Strategies to compute trade signal
    1. Double Bollinger Bands

    Parameters
    ----------
    pl_df : pl.DataFrame
        Polars DataFrame containing close prices and technical indicators
    tickers : list[str]
        List of tickers
    """
    def __init__(
            self,
            pl_df: pl.DataFrame,
            tickers: list[str]
        ) -> None:

        self.pl_df: pl.DataFrame = pl_df
        self.tickers: list[str] = tickers

    def double_bbands(self):
        """
        Compute signal for double bollinger bands strategy
        buy when close > first upper band and close < second upper band
        sell when close < first lower band and close < second lower band

        Parameters
        ----------
        None

        Returns
        -------
        None
        """
        self.pl_df = self.pl_df.with_columns(
            pl.when(
                pl.col(f'{col}') > pl.col(f'{col}_1_upper_band'),
                pl.col(f'{col}') < pl.col(f'{col}_2_upper_band')
            ).then(1).otherwise(
                pl.when(
                    pl.col(f'{col}') < pl.col(f'{col}_1_lower_band'),
                    pl.col(f'{col}') > pl.col(f'{col}_2_lower_band')
                ).then(-1).otherwise(0)
            ).alias(f'{col}_signal') for col in self.tickers
        )
