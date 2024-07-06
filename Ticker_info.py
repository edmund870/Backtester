import polars as pl
import pandas as pd
import yfinance as yf

class ticker_info:
    """
    Retrieves historical information of tickers

    Parameters
    ----------
    tickers : list[str]
        List of tickers
    """
    def __init__(
            self,
            tickers: list[str]
        ) -> None:
        
        self.tickers = tickers

    def get_close(
            self, 
            start_date: str, 
            end_date: str
        ) -> pl.DataFrame:
        """
        Retrieve adjusted close over specified start and end date

        Parameters
        ----------
        start_date : string
            start date of data
        end_date : string
            end date of data

        Returns
        -------
        Polars Dataframe
        """
        close_price: pd.DataFrame = yf.download(tickers = self.tickers, start = start_date, end = end_date)['Adj Close'].reset_index()
        pl_close_price: pl.DataFrame = pl.from_dataframe(close_price)
        pl_close_price: pl.DataFrame = pl_close_price.with_columns(pl.col('Date').cast(pl.Date))

        return pl_close_price.drop_nulls()