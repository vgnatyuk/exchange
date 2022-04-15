import base64
import hmac
import hashlib
import time

import requests
import json

from typing import Tuple, List, Dict


class Config:
    # C3_PR_KEY = "5RllygX2DRdwbCABaeFDuf0qTq1RJJxjsSNi7Z34So9XVc1KemustC4BykyAXmUuyATYdw"
    # C3_PUB_KEY = "nhKgow2x7wg9XAdUsqN_KRkMwUSqWyWWysDENg"
    C3_PR_KEY = "JnNw3Wnx5QIBfjHSksYVFXEsbulcBO2uOJQln3woDGsizvervidJNk3gXE2rqzEUyNgCzg"
    C3_PUB_KEY = "QWn55oJdZofjXUv4JKN9LKarNkahzLqq84Nt_g"

    def __init__(self, tickers: list = None):
        self.TICKERS = tickers or ["DEL", "USDT"]


class C3_API:
    def __init__(self, prKey: str, pubKey: str) -> None:
        self.prKey = prKey
        self.pubKey = pubKey

        # Base URL
        self.BASE_URL = "https://api.c3.exchange"

        # Account Endpoints
        self.CURRENT_BALANCES_ENDPOINT = "/api/wallets/balances"  # [GET]
        self.ORDERS_IN_MARKET_ENDPOINT = "/api/user/orders"  # [GET]
        self.TXS_HISTORY_ENDPOINT = "/api/user/deals"  # [GET]
        self.ORDERS_HISTORY_ENDPOINT = "/api/user/orders"  # [GET]

        # Current Market Endpoints
        self.CURRENT_ORDER_BOOK_ENDPOINT = "/api/orderbook"  # [GET]
        self.CURRENT_TRANSACTIONS_ENDPOINT = "/api/deals"  # [GET]
        self.LAST_PRICE_ENDPOINT = "/api/tickers"  # [GET]

        # Trade Endpoints
        self.PLACE_ORDER_ENDPOINT = (
            "/api/orders"  # [POST] + Header: API-pubKey and API-sig;
        )
        #        + json payload, ex.:
        #        {
        #         "side": "buy",
        #         "currencyPairCode": "BTC_USDT",
        #         "amount": 0.001,
        #         "price": 45000
        #        }
        self.CANCEL_ORDER_ENDPOINT = "/api/orders/"  # [DELETE] + /{orderId}

    # ===== ACCOUNT ENDPOINTS =====
    def getCurrentBalances(self, tickers: list) -> List[dict]:
        """
        Gets currency codes, prepares cryptography signiture and exchange request
        and returns account balances.
        """

        # Generate msg to sign
        requestUrl = self.BASE_URL + self.CURRENT_BALANCES_ENDPOINT
        msg = self.pubKey + requestUrl
        msg = msg.encode("utf-8")
        pubKey = self.pubKey.encode("utf-8")
        prKey = self.prKey.encode("utf-8")

        # Sign message
        signature = hmac.new(prKey, msg, hashlib.sha256).hexdigest()

        # Create and send request
        headers = {
            "API-PublicKey": pubKey,
            "API-Signature": signature,
        }

        balances = json.loads(requests.get(requestUrl, headers=headers).content)

        # Make tickers upper case just in case
        tickers = [ticker.upper() for ticker in tickers]
        # Get target balances
        returnBalances = [
            balance
            for balance in balances["balances"]
            if balance["currencyCode"] in tickers
        ]

        return returnBalances

    def getOrdersHistory(self, tickers: list, status: str = "all"):
        """
        status: "all" / "active" / "canceled"
        """
        currency_pair_code = tickers[0].upper() + "_" + tickers[1].upper()
        requestUrl = self.BASE_URL + self.ORDERS_HISTORY_ENDPOINT
        msg = (self.pubKey + requestUrl).replace(" ", "")
        msg = msg.encode("utf-8")
        pubKey = self.pubKey.encode("utf-8")
        prKey = self.prKey.encode("utf-8")

        # Sign message
        signature = hmac.new(prKey, msg, hashlib.sha256).hexdigest()

        # Create and send request
        headers = {
            "API-PublicKey": self.pubKey,
            "API-Signature": signature,
        }
        response = requests.get(  # TODO Wrong API-Signature
            requestUrl,
            headers=headers,
            params={
                "currencyPairCode": currency_pair_code,
                "status": status,
            },
        )
        return response.content

    def getCurrentOrders(self, tickers: list) -> List[dict]:
        """
        Gets currencies codes to build currencyPairCode, prepares cryptography signiture and exchange request
        and returns active market orders.
        """
        tickers = [ticker.upper() for ticker in tickers]
        currencyPairCode = tickers[0] + "_" + tickers[1]

        # Generate msg to sign
        requestUrl = self.BASE_URL + self.ORDERS_IN_MARKET_ENDPOINT
        requestBody = f"?currencyPairCode={currencyPairCode}&status=active"

        msg = self.pubKey + requestUrl + requestBody
        msg = msg.encode("utf-8")
        pubKey = self.pubKey.encode("utf-8")
        prKey = self.prKey.encode("utf-8")

        # Sign message
        signature = hmac.new(prKey, msg, hashlib.sha256).hexdigest()

        # Create and send request
        headers = {
            "API-PublicKey": pubKey,
            "API-Signature": signature,
        }

        requestMsg = requestUrl + requestBody
        currentOrders = json.loads(requests.get(requestMsg, headers=headers).content)

        return currentOrders

    def getTxsHistory(self, tickers: list, returnSize: int = 50) -> List[dict]:
        """
        Gets currencies codes to build currencyPairCode, prepares cryptography signiture and exchange request
        and returns 50 last txs.

        Attention! Request could be processing around 3-4 seconds on server side!!!
        """

        tickers = [ticker.upper() for ticker in tickers]
        currencyPairCode = tickers[0] + "_" + tickers[1]

        # Generate msg to sign
        requestUrl = self.BASE_URL + self.TXS_HISTORY_ENDPOINT
        requestBody = f"?currencyPairCode={currencyPairCode}&pageSize={returnSize}"

        msg = self.pubKey + requestUrl + requestBody
        msg = msg.encode("utf-8")
        pubKey = self.pubKey.encode("utf-8")
        prKey = self.prKey.encode("utf-8")

        # Sign message
        signature = hmac.new(prKey, msg, hashlib.sha256).hexdigest()

        # Create and send request
        headers = {
            "API-PublicKey": pubKey,
            "API-Signature": signature,
        }

        requestMsg = requestUrl + requestBody
        txsHistory = json.loads(requests.get(requestMsg, headers=headers).content)

        return txsHistory

    # ===== CURRENT MARKET ENDPOINTS =====
    def getCurrentOrderbook(self, tickers: list) -> List[dict]:
        """
        Gets currencies codes to build currencyPairCode, prepares exchange request
        and returns 40 current asks and bids.
        """

        tickers = [ticker.upper() for ticker in tickers]
        currencyPairCode = tickers[0] + "_" + tickers[1]

        requestUrl = self.BASE_URL + self.CURRENT_ORDER_BOOK_ENDPOINT
        requestBody = f"?currencyPairCode={currencyPairCode}"
        requestMsg = requestUrl + requestBody

        orderBook = json.loads(requests.get(requestMsg).content)

        return orderBook

    def getCurrentTxs(self, tickers: list, returnSize: int = 50) -> List[dict]:
        """
        Gets currencies codes to build currencyPairCode, prepares exchange request
        and returns 50 current pair trades.

        Attention! Request could be processing around 4-5 seconds on server side!!!
        """

        tickers = [ticker.upper() for ticker in tickers]
        currencyPairCode = tickers[0] + "_" + tickers[1]

        requestUrl = self.BASE_URL + self.CURRENT_TRANSACTIONS_ENDPOINT
        requestBody = f"?currencyPairCode={currencyPairCode}&pageSize={returnSize}"
        requestMsg = requestUrl + requestBody

        currentTxs = json.loads(requests.get(requestMsg).content)

        return currentTxs

    def getLastPrice(self, tickers: list) -> float:
        """
        Gets currencies codes to build currencyPairCode, prepares exchange request
        and returns last market price.

        NOTE! Original API response contains best ask and best bid.
        """

        tickers = [ticker.upper() for ticker in tickers]
        currencyPairCode = tickers[0] + "_" + tickers[1]

        requestUrl = self.BASE_URL + self.LAST_PRICE_ENDPOINT
        requestBody = f"?currencyPairCode={currencyPairCode}"
        requestMsg = requestUrl + requestBody

        lastPrice = json.loads(requests.get(requestMsg).content)["price"]

        return lastPrice

    # ===== TRADE ENDPOINTS =====
    def placeOrder(self, tickers: list, orderData: dict) -> None:
        """
        Creates and sends limit order to the exchange in format:
        {
          "side": "buy",
          "currencyPairCode": "BTC_USDT",
          "amount": 0.001,
          "price": 45000
        }

        """
        tickers = [ticker.upper() for ticker in tickers]
        currencyPairCode = tickers[0] + "_" + tickers[1]

        # Generate msg to sign
        requestUrl = self.BASE_URL + self.PLACE_ORDER_ENDPOINT
        requestBody = {
            "isBid": False if orderData["direction"].lower() == "sell" else True,
            #             "side": orderData["direction"].lower(),
            "currencyPairCode": currencyPairCode,
            "amount": float(orderData["volume"]),
            "price": float(orderData["price"]),
        }

        # Generate msg to sign
        msg = self.pubKey + requestUrl + json.dumps(requestBody)
        msg = msg.replace(" ", "")
        msg = msg.encode("utf-8")
        pubKey = self.pubKey.encode("utf-8")
        prKey = self.prKey.encode("utf-8")

        # Sign message
        signature = hmac.new(prKey, msg, hashlib.sha256).hexdigest()

        # Create and send request
        headers = {
            "API-PublicKey": self.pubKey,
            "API-Signature": signature,
            "Content-Type": "application/json",
        }
        orderPlaceResult = requests.post(
            requestUrl, headers=headers, json=requestBody
        ).content

        return orderPlaceResult

    def cancelOrder(self, tickers: list, order_guid: str):
        tickers = [ticker.upper() for ticker in tickers]
        currencyPairCode = tickers[0] + "_" + tickers[1]

        # Generate msg to sign
        requestUrl = self.BASE_URL + self.CANCEL_ORDER_ENDPOINT + order_guid

        # Generate msg to sign
        msg = self.pubKey + requestUrl
        msg = msg.replace(" ", "")
        msg = msg.encode("utf-8")
        pubKey = self.pubKey.encode("utf-8")
        prKey = self.prKey.encode("utf-8")

        # Sign message
        signature = hmac.new(prKey, msg, hashlib.sha256).hexdigest()

        # Create and send request
        headers = {
            "API-PublicKey": self.pubKey,
            "API-Signature": signature,
        }
        cancelOrderResult = requests.delete(
            requestUrl,
            headers=headers,
        ).content

        return cancelOrderResult


class CoinsbitConfig:
    API_KEY = "0fcfad9435f7b81261d1eea1ee3bde23"
    SECRET_API = "0c96af3654655a667c5f82f7d77b4098"
    WEBSOCKET_TOKEN = "$2y$10$XrSTDj2Al5q1Hu6k61SCP.LJRLLWHqGQM/zOkIFwzlPu0R6C.Yf0O"

    def __init__(self, tickers: list = None):
        self.TICKERS = tickers or ["BNB", "USDT"]


class CoinsbitAPI:
    """for post methods needs headers
    {
        'X-TXC-APIKEY': self.api_key,
        'X-TXC-PAYLOAD': payload,
        'X-TXC-SIGNATURE': signature,
        "Content-type": "application/json"
    }
    """

    BASE_URL = "https://coinsbit.io"
    TICKERS_URL = "/api/v1/public/tickers"  # [GET]

    # Account Endpoints
    CURRENT_BALANCES_ENDPOINT = "/api/v1/account/balances"  # [POST]
    ORDERS_IN_MARKET_ENDPOINT = "/api/v1/orders"  # [POST]
    ORDERS_HISTORY_ENDPOINT = "/api/v1/account/order_history_list"  # [POST]
    # TXS_HISTORY_ENDPOINT = ""  # []

    # Current Market Endpoints
    CURRENT_ORDER_BOOK_ENDPOINT = "/api/v1/public/book"  # [GET]
    # CURRENT_TRANSACTIONS_ENDPOINT = ""  # []
    # LAST_PRICE_ENDPOINT = ""  # []

    # Trade Endpoints
    PLACE_ORDER_ENDPOINT = "/api/v1/order/new"  # [POST]
    # {
    #     "request": "/api/v1/order/new",
    #     "market": "ETH_BTC",
    #     "side": "sell",
    #     "amount": "0.1",
    #     "price": "0.1",
    #     "nonce": "1636733702330"
    # }
    CANCEL_ORDER_ENDPOINT = "/api/v1/order/cancel"  # [POST]

    # {
    #     "request": "/api/v1/order/cancel",
    #     "market": "ETH_BTC",
    #     "orderId": 25749,
    #     "nonce": "1636733702330"
    # }

    def __init__(self, api_key, secret_api, websocket_token):
        self.api_key = api_key
        self.secret_api = secret_api
        self.websocket_token = websocket_token
        self.headers = {
            "X-TXC-APIKEY": self.api_key,
            "Content-type": "application/json",
        }

    @staticmethod
    def get_payload(request_data):
        return base64.b64encode(json.dumps(request_data).encode())

    def get_signature(self, payload):
        return hmac.new(
            self.secret_api.encode(), payload, digestmod=hashlib.sha512
        ).hexdigest()

    def set_authorization_headers(self, request_data):
        payload = self.get_payload(request_data)
        signature = self.get_signature(payload)
        self.headers["X-TXC-PAYLOAD"] = payload
        self.headers["X-TXC-SIGNATURE"] = signature

    @staticmethod
    def get_currency_pair(tickers: list) -> str:
        return f"{tickers[0].upper()}_{tickers[1].upper()}"

    def get_current_orders(
            self,
            tickers: list,
            offset: int,
            limit: int,
    ):
        url = self.BASE_URL + self.ORDERS_IN_MARKET_ENDPOINT
        request_data = {
            "request": self.ORDERS_IN_MARKET_ENDPOINT,
            "market": self.get_currency_pair(tickers),
            "offset": offset,
            "limit": limit,
            "nonce": int(time.time())
        }
        self.set_authorization_headers(request_data)
        response = requests.post(url, headers=self.headers, json=request_data)
        return response.content

    def get_orders_history(
            self,
            tickers: list,
            offset: int,
            limit: int,
    ):
        url = self.BASE_URL + self.ORDERS_HISTORY_ENDPOINT
        request_data = {
            "request": self.ORDERS_HISTORY_ENDPOINT,
            "market": self.get_currency_pair(tickers),
            "offset": offset,
            "limit": limit,
            "nonce": int(time.time())
        }
        self.set_authorization_headers(request_data)

        response = requests.post(
            url, headers=self.headers, json=request_data
        ).content
        return response

    def get_balance(self, currency: str):
        endpoint_url = self.CURRENT_BALANCES_ENDPOINT
        url = self.BASE_URL + endpoint_url
        request_data = {
            "request": endpoint_url,
            "currency": currency.upper(),
            "nonce": int(time.time()),
        }

        self.set_authorization_headers(request_data)

        response = requests.post(
            url, headers=self.headers, json=request_data
        ).content
        return response

    def place_order(
            self,
            tickers: list,
            side: str,
            amount: float,
            price: float,
    ):
        currency_pair = self.get_currency_pair(tickers)
        url = self.BASE_URL + self.PLACE_ORDER_ENDPOINT
        request_data = {
            "market": currency_pair,
            "side": side,
            "amount": amount,
            "price": price,
        }
        self.set_authorization_headers(request_data)
        response = requests.post(url, headers=self.headers, json=request_data).content

        return response

    def cancel_order(
            self,
            tickers: list,
            order_id: int,
    ):
        url = self.BASE_URL + self.CANCEL_ORDER_ENDPOINT
        currency_pair = self.get_currency_pair(tickers)
        request_data = {
            "market": currency_pair,
            "orderId": order_id,
            "nonce": int(time.time()),
        }
        self.set_authorization_headers(request_data)
        response = requests.post(url, headers=self.headers, json=request_data).content
        return response

    def get_tickers(self):
        url = self.BASE_URL + self.TICKERS_URL
        response = requests.get(url).content
        return response

    def get_current_order_book(
            self,
            tickers: list,
            side: str,
            offset: int,
            limit: int,
    ):
        url = self.BASE_URL + self.CURRENT_ORDER_BOOK_ENDPOINT
        currency_pair = self.get_currency_pair(tickers)
        request_data = {
            "market": currency_pair,  # //ETH_BTC, BTC-ETH ...etc
            "side": side,  # //sell or buy
            "offset": offset,  # //optional; default value 0
            "limit": limit,  # //optional; default value = 50
        }
        return requests.get(url, json=request_data).content
