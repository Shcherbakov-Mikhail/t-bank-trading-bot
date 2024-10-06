import sqlite3
import pandas as pd


class SQLiteClient:
    def __init__(self, db_name):
        self.db_name = db_name
        self.conn = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_name)

    def close(self):
        self.conn.close()

    def execute(self, sql, params=None):
        if params is None:
            params = []
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        self.conn.commit()
        return cursor.fetchall()

    def execute_insert(self, sql, params=None):
        if params is None:
            params = []
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        self.conn.commit()
        return cursor.lastrowid

    def execute_update(self, sql, params=None):
        if params is None:
            params = []
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        self.conn.commit()
        return cursor.rowcount

    def execute_delete(self, sql, params=None):
        if params is None:
            params = []
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        self.conn.commit()
        return cursor.rowcount

    def execute_select(self, sql, params=None):
        if params is None:
            params = []
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()

    def execute_select_one(self, sql, params=None):
        if params is None:
            params = []
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        return cursor.fetchone()
    

class OrderSQLiteClient:
    def __init__(self, db_name = 'trader_stats.db'):
        self.db_client = SQLiteClient(db_name)
        self.db_client.connect()
        self._create_table()

    def _create_table(self):
        self._drop_table()
        self.db_client.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id str PRIMARY KEY,
                figi str,
                direction TEXT,
                price REAL,
                quantity INTEGER,
                status TEXT
            )
            """
        )

    def _drop_table(self):
        self.db_client.execute(
            """
            DROP TABLE IF EXISTS orders
            """
        )

    def add_order(
        self,
        order_id: str,
        figi: str,
        order_direction: str,
        price: float,
        quantity: int,
        status: str,
    ):
        self.db_client.execute_insert(
            "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?)",
            (order_id, figi, order_direction, price, quantity, status),
        )

    def get_orders(self):
        return self.db_client.execute_select("SELECT * FROM orders")

    def update_order_status(self, order_id: str, status: str):
        self.db_client.execute_update(
            "UPDATE orders SET status=? WHERE id=?",
            (status, order_id),
        )


class SimpleStrategySQLiteClient:
    def __init__(self, db_name = 'trader_stats.db'):
        self.db_client = SQLiteClient(db_name)
        self.db_client.connect()
        self._create_table()

    def _create_table(self):
        self._drop_table()
        self.db_client.execute(
            """
            CREATE TABLE IF NOT EXISTS simple_strategy (
                ticker STR,
                percentage REAL,
                quantity INTEGER
            )
            """
        )

    def _drop_table(self):
        self.db_client.execute(
            """
            DROP TABLE IF EXISTS simple_strategy
            """
        )

    def add_order(
        self,
        ticker: str,
        percentage: float,
        quantity: int
    ):
        self.db_client.execute_insert(
            "INSERT INTO simple_strategy VALUES (?, ?, ?)",
            (ticker, percentage, quantity),
        )

    def add_orders_from_excel(self, filename, sheet_name): # TODO: Tooo slow
        orders = pd.read_excel(
            filename, 
            sheet_name=sheet_name, 
            header=0, 
            dtype={
                'Ticker': str,
                'Percentage': float,
                'Lots': int
                }
            )
        
        for i in range(orders.shape[0]):
            self.add_order(
                str(orders.iloc[i][0]),
                float(orders.iloc[i][1]),
                int(orders.iloc[i][2])
                )

    def get_strategy(self):
        """
        Returns list of tuples
        """
        return self.db_client.execute_select("SELECT * FROM simple_strategy")