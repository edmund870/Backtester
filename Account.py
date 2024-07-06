class account:
    """
    Account Information
    1. Cash
    2. Asset Value

    Parameters
    ----------
    init_cash : float
        Starting capital
    """
    def __init__(
            self,
            init_cash: float
    ) -> None:

        self.cash = init_cash
        self.asset_value = 0

        self.daily_account_value = {
            'Date': [],
            'Account_Value': []
        }

    def update_cash(self, cash: float):
        """
        Updates available cash

        Parameters
        ----------
        cash : float
            Change in cash

        Returns
        -------
        None
        """
        self.cash += cash 

    def update_asset_value(self, asset_value: float):
        """
        Updates asset value

        Parameters
        ----------
        asset_value : float
            Point in time asset value

        Returns
        -------
        None
        """
        self.asset_value: float = asset_value

    def update_daily_account_value(self, date: str):
        """
        Updates account value

        Parameters
        ----------
        date : string
            Date of account value

        Returns
        -------
        None
        """
        self.daily_account_value['Date'].append(date)    
        self.daily_account_value['Account_Value'].append(self.cash + self.asset_value)

class position:
    """
    Tracks point in time positions

    Parameters
    ----------
    tickers : list[string]
        List of tickers
    """
    def __init__(
            self,
            tickers: list[str]
        ) -> None:
        
        self.position: dict[str, float] = {
            **{ticker: 0 for ticker in tickers}
        }