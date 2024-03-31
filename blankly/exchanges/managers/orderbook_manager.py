"""
    Class to manage the orderbook, adding, removing and updating - as well as provide user interaction
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
import traceback
import warnings
import random
from typing import List

import requests

import blankly.exchanges.auth.utils
import blankly.utils.utils
from blankly.exchanges.interfaces.alpaca.alpaca_websocket import Tickers as Alpaca_Websocket
from blankly.exchanges.managers.websocket_manager import WebsocketManager


def sort_list_tuples(list_with_tuples: list) -> List[tuple]:
    return sorted(list_with_tuples, key=lambda x: x[0])


def remove_price(book: list, price: float) -> list:
    for j in range(len(book)):
        price_at_index = book[j][0]
        if price_at_index > price:
            break
        if price_at_index == price:
            book.pop(j)
            break

    return book


class OrderbookManager(WebsocketManager):
    def __init__(self, default_exchange, default_symbol):
        """
        Create a new orderbook manager
        Args:
            default_exchange: Add an exchange name for the manager to favor
            default_symbol: Add a default currency for the manager to favor
        """
        self.__default_exchange = default_exchange
        self.__default_currency = default_symbol

        self.__orderbooks = {default_exchange: {}}

        self.__websockets = {default_exchange: {}}

        self.__websockets_callbacks = {default_exchange: {}}

        self.__websockets_kwargs = {default_exchange: {}}

        # Create the abstraction for adding many managers
        super().__init__(self.__websockets, default_symbol, default_exchange)

    def create_orderbook(self, callback,
                         override_symbol=None,
                         override_exchange=None,
                         initially_stopped=False,
                         **kwargs):
        """
        Create an orderbook for a given exchange
        Args:
            callback: Callback object for the function. Should be something like self.price_event
            override_symbol: Override the default currency id
            override_exchange: Override the default exchange
            initially_stopped: Keep the websocket stopped when created
            kwargs: Add any other parameters that should be passed into a callback function to identify
                it or modify behavior
        """

        use_sandbox = self.preferences['settings']['use_sandbox_websockets']

        exchange_name = self.__default_exchange
        # Ensure the ticker dict has this overridden exchange
        if override_exchange is not None:
            if override_exchange not in self.__websockets.keys():
                self.__websockets[override_exchange] = {}
                self.__websockets_callbacks[override_exchange] = {}
                self.__websockets_kwargs[override_exchange] = {}
            # Write this value so it can be used later
            exchange_name = override_exchange

        # Ensure that we always have a key the relevant orderbook
        if exchange_name not in self.__orderbooks:
            self.__orderbooks[exchange_name] = {}

        if exchange_name == "alpaca":
            warning_string = "Alpaca only allows the viewing of the bid/ask spread, not a total orderbook."
            warnings.warn(warning_string)
            if override_symbol is None:
                override_symbol = self.__default_currency

            stream = self.preferences['settings']['alpaca']['websocket_stream']
            override_symbol = blankly.utils.to_exchange_symbol(override_symbol, "alpaca")

            if use_sandbox:
                websocket = Alpaca_Websocket(override_symbol, 'quotes', initially_stopped=initially_stopped,
                                             WEBSOCKET_URL=
                                             "wss://paper-api.alpaca.markets/stream/v2/{}/".format(stream))
            else:
                websocket = Alpaca_Websocket(override_symbol, 'quotes', initially_stopped=initially_stopped,
                                             WEBSOCKET_URL="wss://stream.data.alpaca.markets/v2/{}/".format(stream))

            websocket.append_callback(self.alpaca_update)

            self.__websockets['alpaca'][override_symbol] = websocket
            self.__websockets_callbacks['alpaca'][override_symbol] = [callback]
            self.__websockets_kwargs['alpaca'][override_symbol] = kwargs

            self.__orderbooks['alpaca'][override_symbol] = {
                "bids": [],
                "asks": [],
            }

        else:
            print(exchange_name + " ticker not supported, skipping creation")

    def alpaca_update(self, update: dict):
        # Alpaca only gives the spread, no orderbook depth (alpaca is very bad)
        symbol = update['S']
        self.__orderbooks['alpaca'][symbol]['bids'] = [(update['bp'], update['bs'])]
        self.__orderbooks['alpaca'][symbol]['asks'] = [(update['ap'], update['as'])]

        callbacks = self.__websockets_callbacks['alpaca'][symbol]
        for i in callbacks:
            i(self.__orderbooks['alpaca'][symbol],
              **self.__websockets_kwargs['alpaca'][symbol])

    def append_orderbook_callback(self, callback_object, override_symbol=None, override_exchange=None):
        """
        These are appended calls to a sorted orderbook. Functions added to this will be fired every time the orderbook
        changes.
        Args:
            callback_object: Reference for the callback function. The price_event(self, tick)
                function would be passed in as just self.price_event -- no parenthesis or arguments, just the reference
            override_symbol: Ticker id, such as "BTC-USD" or exchange equivalents.
            override_exchange: Forces the manager to use a different supported exchange.
        """
        if override_symbol is None:
            override_symbol = self.__default_currency

        if override_exchange is None:
            override_exchange = self.__default_exchange

        self.__websockets_callbacks[override_exchange][override_symbol].append(callback_object)

    def get_most_recent_orderbook(self, override_symbol=None, override_exchange=None):
        """
        Get the most recent orderbook under a currency and exchange.

        Args:
            override_symbol: Ticker id, such as "BTC-USD" or exchange equivalents.
            override_exchange: Forces the manager to use a different supported exchange.
        """
        if override_symbol is None:
            override_symbol = self.__default_currency

        if override_exchange is None:
            override_exchange = self.__default_exchange

        return self.__orderbooks[override_exchange][override_symbol]
