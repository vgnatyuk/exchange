from abc import ABC, abstractmethod


class API(ABC):

    def __init__(self, market: str = "eth_usdt") -> None:
        if not (isinstance(market, str) and '_' in market):
            raise Exception(
                'market must be string with "currency1_currency2" format'
            )
        self.market = market
        self.currency_1, self.currency_2 = [
            s.upper() for s in self.market.split('_')
        ]

    @abstractmethod
    def get_order_book(self) -> dict:
        """
        Return orderbook separately asks and bids.

        :return: {
            'asks': List[[price, volume], [price, volume], ...],
            'bids': List[[price, volume], [price, volume], ...],
        }
        """

    @abstractmethod
    def check_accounts_state(self) -> dict:
        """
        Return balances for market currencies. Based on market in __init__

        :return: {
            'account_state': {
                    'del': 6.5,
                     'usdt': 2.20241475125,
                     },
        }
        """

    @abstractmethod
    def place_order(
            self,
            side: str,
            amount: str,
            price: str,
            order_type: str,
    ) -> dict:
        """
        Return info about placed order or failed placing info.

        :param pair_name: string. market pair ex. 'DEL_USDT'
        :param side: string. 'buy' or 'sell' options only
        :param amount: string. order volume. ex. '0.909'
        :param price: string. order price. ex. '0.0465'
        :param order_type: string. order type: 'limit', 'stop'... ex. 'limit'

        :return: {
            'ok': True,
            'result': {
                'order_id': 40284615,
                'user_id': 12369,
                'quantity': 0.001,
                'pair': 'del_usdt',
                'side': 'sell',
                'price': 1,
                'executed': 0,
                'status': 'created',
                'base_decimals': 18,
                'quote_decimals': 6,
                'pair_id': 24,
                'type': 'limit',
                'stop_price': None,
                'slippage': None,
                'timestamp': 1656999563,
                'updated_at': '2022-07-05T05:39:23.221Z',
                'created_at': '2022-07-05T05:39:23.221Z',
                'executed_price': None,
                'fee': None,
                'order_cid': None,
                'expires': None
                }
        }

        """

    @abstractmethod
    def cancel_order(self, order_id: str) -> dict:
        """
        Return info about cancelled order or failed cancelling.

        :param order_id: string. order id to cancel. ex. '5646545'

        :return: {
            'ok': True, # may be False
            'result': {
                'message': 'The request to cancel your order was received'
                }
            }
        """

    @abstractmethod
    def get_user_orders(self, order_status: str) -> dict:
        """
        Return user orders by type.

        :param order_status: string. Type depends on exchange. ex. 'all' or 'active'

        :return: {
            'ok': True,
            'result': {
                'count': 5,
                'orders': [
                    {
                        'order_id': 40285458,
                        'user_id': 12369,
                        'pair': 'del_usdt',
                        'pair_id': 24,
                        'quantity': 0.001,
                        'price': 1,
                        'executed_price': None,
                        'fee': None,
                        'order_cid': None,
                        'executed': 0, # NOT boolean! int. quantity of sold
                        'expires': None,
                        'base_decimals': 18,
                        'quote_decimals': 6,
                        'timestamp': 1657000659,
                        'status': 'accepted',
                        'side': 'sell',
                        'type': 'limit',
                        'stop_price': None,
                        'slippage': None
                    },
                    ...
                ]
            }
        }
        """

    @abstractmethod
    def get_order_state(self, order_id: str) -> dict:
        """
        Return order state.

        :param order_id: string. id to get info from exchange. ex. '4987494'

        :return: {
            'ok': True,
            'result': {
                'order_id': 40285458,
                'user_id': 12369,
                'pair': 'del_usdt',
                'pair_id': 24,
                'quantity': 0.001,
                'price': 1,
                'executed_price': None,
                'fee': None,
                'order_cid': None,
                'executed': 0,
                'expires': None,
                'base_decimals': 18,
                'quote_decimals': 6,
                'timestamp': 1657000659,
                'status': 'accepted',
                'side': 'sell',
                'type': 'limit',
                'stop_price': None,
                'slippage': None
            }
        }
        """

    @abstractmethod
    def parse_check_accounts_state(self, account_balance: dict) -> dict:
        pass

    @abstractmethod
    def parse_get_order_book(self, order_book: dict) -> dict:
        pass

    @abstractmethod
    def parse_placing_order_result(self, placing_order_result: dict) -> dict:
        pass

    @abstractmethod
    def parse_cancel_order(self, canceling_order_result: dict) -> dict:
        pass

    @abstractmethod
    def parse_user_orders(self, current_orders: dict) -> dict:
        pass

    @abstractmethod
    def parse_order_state(self, order_state: dict) -> dict:
        pass


class EmptyKeysException(Exception):
    pass
