import sys
import time
from datetime import datetime
from operator import itemgetter

import pytest
from _pytest.python_api import approx

from blankly.enums import Side, OrderType, ContractType, OrderStatus, HedgeMode, MarginType, PositionMode, TimeInForce
from blankly.exchanges.interfaces.abc_base_exchange_interface import ABCBaseExchangeInterface
from blankly.exchanges.interfaces.exchange_interface import ExchangeInterface
from blankly.utils import utils
from tests.new_interface_tests.test_utils import wait_till_filled, homogeneity_testing, sell, buy, cancelling_order, \
    close_position, \
    close_all


def valid_product_helper(interface: ABCBaseExchangeInterface, product):
    base = product['base_asset']
    quote = product['quote_asset']
    symbol = product['symbol']
    assert symbol == base + '-' + quote
    exc = utils.to_exchange_symbol(symbol, interface.get_exchange_type())
    bly = utils.to_blankly_symbol(exc, interface.get_exchange_type(), quote)
    assert bly == symbol


def test_valid_symbols(interface: ABCBaseExchangeInterface):
    if interface.get_exchange_type().startswith('alpaca'):
        pytest.skip('stonk symbols can be whatever they wanna be')

    products = interface.get_products()

    for product in products:
        valid_product_helper(interface, product)


@homogeneity_testing
def test_get_products_spot(spot_interface: ExchangeInterface):
    return spot_interface.get_products()


def test_simple_open_close(interface: ABCBaseExchangeInterface,
                           symbol: str) -> None:
    close_position(interface, symbol)

    # buy
    size = buy(interface, symbol).get_size()
    base = utils.get_base_asset(symbol)
    assert interface.get_account(base)['available'] == approx(size)

    close_position(interface, symbol)
