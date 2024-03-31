"""
    Exchange metadata for use in the CLI
    Copyright (C) 2022 Matias Kotlik

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

from typing import Dict, List
from questionary import Choice

from blankly.deployment.ui import print_failure


class Exchange:
    name: str
    symbols: List[str]
    python_class: str
    tlds: List[str]
    display_name: str
    key_info: Dict[str, str]

    def __init__(self, name: str, symbols: List[str], test_func, key_info: List[str] = None, python_class: str = None,
                 tlds: List[str] = None, display_name: str = None, currency: str = 'USD'):
        self.name = name
        self.symbols = symbols
        self.test_func = test_func
        self.key_info = {k.replace('_', ' ').title().replace('Api', 'API'): k  # autogen key instructions
                         for k in key_info or ['API_KEY', 'API_SECRET']}  # default to just key/secret
        self.python_class = python_class or name.replace('_', ' ').title().replace(' ', '')  # snake case to pascalcase
        self.tlds = tlds or []
        self.display_name = display_name or name.replace('_', ' ').title()  # prettify
        self.currency = currency


EXCHANGES = []
try:
    import alpaca_trade_api
    from blankly.exchanges.interfaces.alpaca import alpaca_api
    EXCHANGE_ALPACA = Exchange('alpaca', ['MSFT', 'GME', 'AAPL'],
             lambda auth, tld: alpaca_trade_api.REST(key_id=auth['API_KEY'],
                                                     secret_key=auth['API_SECRET'],
                                                     base_url=(alpaca_api.live_url,
                                                               alpaca_api.paper_url)[auth['sandbox']]
                                                     ).get_account())
    EXCHANGES.append(EXCHANGE_ALPACA)
except:
    pass
try:
    from blankly.exchanges.interfaces.coinbase_pro.coinbase_pro_api import API as CoinbaseProAPI
    EXCHANGE_COINBASE = Exchange('coinbase_pro', ['BTC-USD', 'ETH-USD', 'SOL-USD'],
             lambda auth, tld: CoinbaseProAPI(api_key=auth['API_KEY'], api_secret=auth['API_SECRET'],
                                              api_pass=auth['API_PASS'],
                                              API_URL=('https://api.pro.coinbase.com/',
                                                       'https://api-public.sandbox.pro.coinbase.com/')[auth['sandbox']]
                                              ).get_accounts(),
             key_info=['API_KEY', 'API_SECRET', 'API_PASS'])
    EXCHANGES.append(EXCHANGE_COINBASE)
except:
    pass

EXCHANGE_CHOICES_NO_KEYLESS = [Choice(exchange.display_name, exchange)
                               for exchange in EXCHANGES]
EXCHANGE_CHOICES = EXCHANGE_CHOICES_NO_KEYLESS[:]
EXCHANGE_CHOICES.append(Choice('Keyless/No Exchange', False))


def exc_display_name(name):
    return next((exchange.display_name for exchange in EXCHANGES if name == exchange.name), name)
