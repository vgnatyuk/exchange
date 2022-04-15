import datetime

from C3 import C3_API, CoinsbitAPI, Config, CoinsbitConfig


def c3_logger(func):
    def wrapper(*args, **kwargs):
        warlock_instance = args[0]
        return_value = {"INIT_ERROR": "Haven't C3 API instance"}
        if hasattr(warlock_instance, "c3"):
            return_value = func(*args, **kwargs)
        log_result(return_value, func.__name__, *args, **kwargs)

    return wrapper


def coinsbit_logger(func):
    def wrapper(*args, **kwargs):
        warlock_instance = args[0]
        return_value = {"INIT_ERROR": "Haven't COINSBIT API instance"}
        if hasattr(warlock_instance, "coinsbit"):
            return_value = func(*args, **kwargs)
        log_result(return_value, func.__name__, *args, **kwargs)

    return wrapper


def log_result(result, file_name, *args, **kwargs):
    if isinstance(result, bytes):
        result = result.decode()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(f"{file_name}.json", "a", encoding="utf-8") as file:
        file.write(f"[{now}] {result} {args} {kwargs}\n")


class Warlock:
    def __init__(
            self,
            c3: C3_API = None,
            c3_config: Config = None,
            coinsbit: CoinsbitAPI = None,
            coinsbit_config: CoinsbitConfig = None,
    ):
        if c3 and c3_config:
            self.c3 = C3_API(
                c3_config.C3_PR_KEY,
                c3_config.C3_PUB_KEY,
            )
            self.c3_tickers = c3_config.TICKERS
        if coinsbit and coinsbit_config:
            self.coinsbit = CoinsbitAPI(
                coinsbit_config.API_KEY,
                coinsbit_config.SECRET_API,
                coinsbit_config.WEBSOCKET_TOKEN,
            )
            self.coinsbit_tickers = coinsbit_config.TICKERS

    @c3_logger
    def c3_getCurrentBalances(self, tickers):
        return self.c3.getCurrentBalances(tickers)

    @c3_logger
    def c3_getOrdersHistory(self, tickers, status: str = "all"):
        return self.c3.getOrdersHistory(tickers, status)

    @c3_logger
    def c3_getCurrentOrders(self, tickers):
        return self.c3.getCurrentOrders(tickers)

    @c3_logger
    def c3_getTxsHistory(self, tickers, returnSize: int = 50):
        return self.c3.getTxsHistory(tickers, returnSize)

    @c3_logger
    def c3_getCurrentOrderbook(self, tickers):
        return self.c3.getCurrentOrderbook(tickers)

    @c3_logger
    def c3_getCurrentTxs(self, tickers, returnSize: int = 50):
        return self.c3.getCurrentTxs(tickers, returnSize)

    @c3_logger
    def c3_getLastPrice(self, tickers):
        return self.c3.getLastPrice(tickers)

    @c3_logger
    def c3_placeOrder(self, tickers, orderData: dict) -> None:
        return self.c3.placeOrder(tickers, orderData)

    @c3_logger
    def c3_cancelOrder(self, tickers, order_guid: str):
        return self.c3.cancelOrder(tickers, order_guid)

    @coinsbit_logger
    def coinsbit_get_current_orders(self, tickers, offset: int, limit: int):
        return self.coinsbit.get_current_orders(tickers, offset, limit)

    @coinsbit_logger
    def coinsbit_get_orders_history(self, tickers, offset: int, limit: int):
        return self.coinsbit.get_orders_history(tickers, offset, limit)

    @coinsbit_logger
    def coinsbit_get_balance(self, currency):
        return self.coinsbit.get_balance(currency)

    @coinsbit_logger
    def coinsbit_place_order(self, tickers, side: str, amount: float, price: float):
        return self.coinsbit.place_order(tickers, side, amount, price)

    @coinsbit_logger
    def coinsbit_cancel_order(self, tickers, order_id: int):
        return self.coinsbit.cancel_order(tickers, order_id)

    @coinsbit_logger
    def coinsbit_get_tickers(self):
        return self.coinsbit.get_tickers()

    @coinsbit_logger
    def coinsbit_get_current_order_book(self, tickers, side: str, offset: int, limit: int):
        return self.coinsbit.get_current_order_book(
            tickers,
            side,
            offset,
            limit,
        )


if __name__ == '__main__':
    # добавил пару запросов для примера
    coinsbit_config = CoinsbitConfig()
    warlock = Warlock(coinsbit=CoinsbitAPI, coinsbit_config=coinsbit_config)
    warlock.coinsbit_get_tickers()
    warlock.coinsbit_get_current_order_book(coinsbit_config.TICKERS, side="sell", offset=0, limit=20)

    orderData = {
        "direction": "sell",
        "volume": 1,
        "price": 10,
    }
    c3_config = Config()
    warlock = Warlock(C3_API, c3_config)
    warlock.c3_placeOrder(c3_config.TICKERS, orderData)
    warlock.c3_getCurrentBalances(c3_config.TICKERS)
    warlock.c3_getLastPrice(c3_config.TICKERS)
