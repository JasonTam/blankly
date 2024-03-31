"""
    Script for managing the variety of tickers on different exchanges.
    Copyright (C) 2021  Emerson Dove

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import random
import requests

import blankly.utils.utils
from blankly.exchanges.interfaces.alpaca.alpaca_websocket import Tickers as Alpaca_Ticker
from blankly.exchanges.managers.websocket_manager import WebsocketManager


class TickerManager(WebsocketManager):
    def __init__(self, default_exchange: str, default_symbol: str):
        """
        Create a new manager.
        Args:
            default_exchange: Add an exchange name for the manager to favor
            default_symbol: Add a default currency for the manager to favor
        """
        self.__default_exchange = default_exchange
        if default_exchange == "alpaca":
            default_symbol = blankly.utils.to_exchange_symbol(default_symbol, "alpaca")

        self.__default_symbol = default_symbol

        self.__tickers = {default_exchange: {}}

        # Create abstraction for writing many managers
        super().__init__(self.__tickers, default_symbol, default_exchange)

    """ 
    Manager Functions 
    """

    def create_ticker(self, callback, log: str = None, override_symbol: str = None, override_exchange: str = None,
                      **kwargs):
        """
        Create a ticker on a given exchange.
        Args:
            callback: Callback object for the function. Should be something like self.price_event
            log: Fill this with a path to log the price updates.
            override_symbol: The currency to create a ticker for.
            override_exchange: Override the default exchange.
            kwargs: Any keyword arguments to be passed into the callback besides the first positional message argument
        Returns:
            Direct ticker object
        """

        # Delete the symbol arg because it shouldn't be in kwargs
        try:
            del(kwargs['symbol'])
        except KeyError:
            pass

        sandbox_mode = self.preferences['settings']['use_sandbox_websockets']

        exchange_name = self.__default_exchange
        # Ensure the ticker dict has this overridden exchange
        if override_exchange is not None:
            if override_exchange not in self.__tickers.keys():
                self.__tickers[override_exchange] = {}
            # Write this value so it can be used later
            exchange_name = override_exchange

        if exchange_name == "alpaca":
            stream = self.preferences['settings']['alpaca']['websocket_stream']
            if override_symbol is None:
                override_symbol = self.__default_symbol

            override_symbol = blankly.utils.to_exchange_symbol(override_symbol, "alpaca")
            if sandbox_mode:
                ticker = Alpaca_Ticker(override_symbol,
                                       "trades",
                                       log=log,
                                       websocket_url="wss://paper-api.alpaca.markets/stream/v2/{}/".format(stream),
                                       **kwargs)
            else:
                ticker = Alpaca_Ticker(override_symbol,
                                       "trades",
                                       log=log,
                                       websocket_url="wss://stream.data.alpaca.markets/v2/{}/".format(stream),
                                       **kwargs)
            ticker.append_callback(callback)
            self.__tickers['alpaca'][override_symbol] = ticker
            return ticker

        else:
            print(exchange_name + " ticker not supported, skipping creation")
