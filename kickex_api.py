import base64
import hashlib
import hmac
import json
from functools import reduce
from typing import List, Optional
from urllib import parse

import requests
import time

from base_api import API, EmptyKeysException
from config import KICKEX_PUB_KEY, KICKEX_PR_KEY, KICKEX_PASSWORD


class Kickex(API):
    """wrapper for kickex.com exchange api"""

    ORDER_STATUSES = {
        1: 'pending',  # 1 отложенный по каким - то причинам ордер
        2: 'on hold',  # 2 состояние торгового ордера после подтверждения сервисом SOB тогда
        3: 'placing',  # 3 ордер находится в процессе доставки в свой сервис(матчер или SOB)
        4: 'accepted',  # 4 ордер на исполнении(размещен в LOB или в SOB);
        5: 'executed',  # 5 исполненный ордер
        6: 'rejected',  # 6 ордер, в исполнении которого отказано
        7: 'cancelled',  # 7 отмененный ордер.
        45: 'partially executed',  # статус для внутреннего пользования, кикекс такой не присылает
    }

    SIDES = {
        'buy': 0,
        'sell': 1,
    }
    SIDES.update({v: k for k, v in SIDES.items()})

    def __init__(self, market: str = "eth_usdt") -> None:
        super().__init__(market)

        self.BASE_URI = "https://gate.kickex.com/api/v1"
        self.GET_DEPTH_URI = "/market/orderbook"
        self.GET_BALANCE_URI = "/user/balance"
        self.PLACE_ORDER_URI = '/createTradeOrder'
        self.CANCEL_ORDER_URI = '/orders/'  # + {orderId}
        self.GET_USER_ORDERS = '/activeOrders'
        self.GET_ORDER_STATE = '/ordersHistory'
        self.FETCH_ORDER = '/order'
        self.GET_ORDERS_HISTORY = '/ordersHistory'

        self.kkx_pubKey = KICKEX_PUB_KEY
        self.kkx_prKey = KICKEX_PR_KEY
        self.password = KICKEX_PASSWORD

        if not all([self.kkx_pubKey, self.kkx_prKey, self.password]):
            raise EmptyKeysException('Kickex has no api keys')

        self.pair_name = f'{self.currency_1}/{self.currency_2}'

    def get_order_book(self) -> dict:
        url = self.BASE_URI + self.GET_DEPTH_URI + f"?pairName={self.pair_name}"
        order_book = requests.get(url).json()
        return self.parse_get_order_book(order_book=order_book)

    def parse_get_order_book(self, order_book: dict) -> dict:
        if 'asks' in order_book and 'bids' in order_book:
            ok = True
            result = {
                "asks": [
                    (order['price'], order['amount']) for order in order_book["asks"]
                ],
                "bids": [
                    (order['price'], order['amount']) for order in order_book["bids"]
                ],
            }
        else:
            ok = False
            result = order_book

        return {
            'ok': ok,
            'result': result,
        }

    def check_accounts_state(self) -> dict:
        method = 'GET'
        headers, url_params, params = self.get_headers_and_stuff(
            self.GET_BALANCE_URI, method=method
        )
        url = self.BASE_URI + self.GET_BALANCE_URI + url_params
        account_balance = requests.request(
            method, url, headers=headers, data=params
        ).json()

        return self.parse_check_accounts_state(account_balance)

    def parse_check_accounts_state(self, account_balance: dict) -> dict:
        if 'code' not in account_balance:
            ok = True
            balances = {
                balance['currencyCode']: balance['available']
                for balance in account_balance
            }
            bt_base = balances.get(self.currency_1, -1)  # -1 if balance for token doesn't exist
            bt_exch = balances.get(self.currency_2, -1)
            account_state = {
                "account_state": {
                    self.currency_1: float(bt_base),
                    self.currency_2: float(bt_exch),
                },
            }
            result = account_state
        else:
            ok = False
            result = account_balance

        return {
            'ok': ok,
            'result': result,
        }

    def place_order(
        self,
        side: str,
        amount: str,
        price: str,
        order_type: str,
    ) -> dict:
        """
        :param pair_name: string. ex. 'DEL/USDT'
        :param side: integer. 0 to buy, 1 to sell. ex. 1
        :param amount: string. ex. '0.1'
        :param price: string. ex. '0.112'
        :param order_type: this method creates ONLY limit orders
        :return:
        """
        trade_intent = self.SIDES[side]

        payload = {
            "pairName": self.pair_name,
            "orderedAmount": amount,
            "limitPrice": price,
            "tradeIntent": trade_intent,
            "modifier": "GTC",
        }
        method = 'POST'

        headers, url_params, body = self.get_headers_and_stuff(
            self.PLACE_ORDER_URI, method, params=payload
        )
        url = self.BASE_URI + self.PLACE_ORDER_URI + url_params
        placing_order_result = requests.request(
            method, url, headers=headers, data=body
        ).json()
        return self.parse_placing_order_result(placing_order_result)

    def parse_placing_order_result(self, placing_order_result: dict) -> dict:
        if 'orderId' in placing_order_result:
            ok = True
            result = self.parse_orders([placing_order_result])[0]
        else:
            ok = False
            result = placing_order_result
        return {
            'ok': ok,
            'result': result,
        }

    def cancel_order(self, order_id: str) -> dict:
        method = 'DELETE'
        headers, url_params, body = self.get_headers_and_stuff(
            self.CANCEL_ORDER_URI + order_id, method, params={}
        )
        url = self.BASE_URI + self.CANCEL_ORDER_URI + order_id

        canceling_order_result = requests.request(method, url, headers=headers).json()

        return self.parse_cancel_order(canceling_order_result)

    def parse_cancel_order(self, canceling_order_result: dict) -> dict:
        if canceling_order_result == {}:
            ok = True
            result = {'message': 'The request to cancel your order was received'}
        else:
            ok = False
            result = canceling_order_result
        return {
            'ok': ok,
            'result': result,
        }

    def get_user_orders(self, order_status: str) -> dict:
        method = 'GET'
        headers, url_params, params = self.get_headers_and_stuff(
            self.GET_USER_ORDERS, method=method
        )
        url = self.BASE_URI + self.GET_USER_ORDERS + url_params

        current_orders = requests.request(
            method, url, headers=headers, data=params
        ).json()
        return self.parse_user_orders(current_orders)

    def parse_user_orders(self, current_orders) -> dict:
        if isinstance(current_orders, list):
            ok = True
            result = {
                'count': len(current_orders),
                'orders': self.parse_orders(current_orders),
            }
        else:
            ok = False
            result = {**current_orders}

        return {
            'ok': ok,
            'result': result,
        }

    def parse_orders(self, orders: List[dict]) -> List[dict]:
        handled_orders = []
        for order in orders:
            handled_orders.append(
                {
                    'order_id': int(order.get('orderId')),
                    'user_id': order.get('userId'),
                    'quantity': get_float_value_or_None(order.get('orderedVolume')),
                    'pair': order.get('pairName'),
                    'side': self.SIDES.get(order.get('tradeIntent')),
                    'price': get_float_value_or_None(order.get('limitPrice')),
                    'executed': get_float_value_or_None(order.get('totalSellVolume')),
                    'status': self.get_order_status(order),
                    'base_decimals': order.get('baseDecimals'),
                    'quote_decimals': order.get('quoteDecimals'),
                    'pair_id': order.get('pairId'),
                    'type': order.get('type'),
                    'stop_price': order.get('stopPrice'),
                    'slippage': order.get('slippage'),
                    'timestamp': self.get_formatted_timestamp(
                        order.get('createdTimestamp')
                    ),
                    'updated_at': order.get('updatedAt'),
                    'created_at': order.get('createdAt'),
                    'executed_price': get_float_value_or_None(
                        order.get('executedPrice')
                    ),
                    'fee': get_float_value_or_None(order.get('fee')),
                    'order_cid': order.get('orderCid'),
                    'expires': order.get('expires'),
                }
            )
        return handled_orders

    @staticmethod
    def get_formatted_timestamp(nanoseconds: float) -> Optional[int]:
        """
        Kickex returns timestamp in nanoseconds but we need just seconds
        """
        if nanoseconds is None:
            return None
        return int(float(nanoseconds) / 1e9)

    def get_order_state(self, order_id: str) -> dict:
        return self.parse_order_state(self.fetch_order(order_id))

    def parse_order_state(self, order_state: dict) -> dict:
        if 'orderId' in order_state:
            ok = True
            result = self.parse_orders([order_state])[0]
        else:
            ok = False
            result = order_state

        return {
            'ok': ok,
            'result': result,
        }

    def get_order_status(self, order: dict) -> Optional[str]:
        status = order.get('state', None)
        if status is None:
            return None

        if status == 5 and order['totalSellVolume'] < order['orderedVolume']:
            status = 45
        return self.ORDER_STATUSES[status]

    def fetch_order(self, order_id: str) -> dict:
        method = 'GET'
        params = {"orderId": order_id}
        headers, url_params, params = self.get_headers_and_stuff(
            self.FETCH_ORDER, method=method, params=params
        )
        url = self.BASE_URI + self.FETCH_ORDER + url_params
        response = requests.request(method, url, headers=headers, data=params)
        return response.json()

    def get_headers_and_stuff(self, path, method, params=None):
        full_path = "/api/v1" + path
        timestamp = str(int(time.time()))
        body_for_signature = ''
        url_params = ''
        body = ''
        params = params or {}

        if method == 'GET' or method == 'DELETE':
            body_for_signature = parse.urlencode(params, False)
            if body_for_signature:
                url_params = "?" + body_for_signature
        elif method == 'POST':
            body_for_signature = json.dumps(params, separators=(',', ':'))
            if body_for_signature:
                body = body_for_signature

        signature = self.get_signature(timestamp, method, full_path, body_for_signature)

        headers = {
            'Content-Type': 'application/json',
            'KICK-API-KEY': self.kkx_pubKey,
            'KICK-API-PASS': (
                base64.standard_b64encode(self.password.encode('latin-1'))
            ),
            'KICK-API-TIMESTAMP': timestamp,
            'KICK-SIGNATURE': signature,
        }
        return headers, url_params, body

    def get_signature(
            self,
            timestamp,
            method,
            full_path,
            body_for_signature,
    ):
        secret = base64.standard_b64decode(
            self.kkx_prKey.replace('-', '+').replace('_', '/')
        )

        signature = (
            base64.standard_b64encode(
                (
                    hmac.new(
                        timestamp.encode('latin-1'),
                        method.lower().encode('latin-1'),
                        hashlib.sha512,
                    )
                ).digest()
            )
        ).decode('latin-1')

        arguments = [
            signature,
            full_path.encode('latin-1'),
            body_for_signature.encode('latin-1'),
            secret,
        ]
        signature = reduce(self.generate_sign, arguments)

        return signature

    @staticmethod
    def generate_sign(key: str, message) -> str:
        signature = (
                base64.standard_b64encode(
                    (
                        hmac.new(
                            base64.standard_b64decode(key),
                            message,
                            hashlib.sha512,
                        )
                    ).digest()
                )
            ).decode('latin-1')
        return signature

    def get_orders_history(self):
        params = {'pairName': self.pair_name}
        method = 'GET'
        headers, url_params, params = self.get_headers_and_stuff(
            self.GET_ORDERS_HISTORY, method=method, params=params
        )
        url = self.BASE_URI + self.GET_ORDERS_HISTORY + url_params

        orders = requests.request(
            method, url, headers=headers, data=params
        ).json()
        return orders


def get_float_value_or_None(value) -> Optional[float]:
    if value is None:
        return None
    return float(value)


if __name__ == '__main__':
    k = Kickex()
    _id = 167885682112
    # print(k.get_order_state(str(_id))) # done
    print(k.get_order_book()) # done
    # print(k.get_user_orders('all')) # done
    # print(k.place_order(side='sell', order_type='limit', amount='1', price='1')) # done
    # print(k.cancel_order(str(_id))) # done
    # print(k.check_accounts_state()) # done
    # print(k.get_orders_history()) # done
