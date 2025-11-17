"""ビットコインデータ取得モジュール"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd
import numpy as np


class BitcoinAPIClient:
    """CoinGecko APIを使用してビットコインデータを取得するクライアント"""

    def __init__(self, verify_ssl: bool = True):
        """
        Args:
            verify_ssl: SSL証明書を検証するか（デフォルト: True）
        """
        self.base_url = "https://api.coingecko.com/api/v3"
        self.verify_ssl = verify_ssl

    def get_daily_ohlcv(self, days: int = 90) -> pd.DataFrame:
        """
        ビットコインの日足OHLCVデータを取得

        Args:
            days: 取得する日数（デフォルト: 90日）

        Returns:
            pd.DataFrame: OHLCV データ（Date, Open, High, Low, Close, Volume）
        """
        try:
            # CoinGecko APIでビットコインの価格データを取得
            url = f"{self.base_url}/coins/bitcoin/market_chart"
            params = {
                "vs_currency": "usd",
                "days": days,
                "interval": "daily"
            }

            response = requests.get(url, params=params, timeout=10, verify=self.verify_ssl)
            response.raise_for_status()
            data = response.json()

            # 価格データと出来高データを整形
            prices = data.get("prices", [])
            volumes = data.get("total_volumes", [])

            if not prices or not volumes:
                raise ValueError("APIからデータを取得できませんでした")

            # DataFrameに変換
            df = pd.DataFrame(prices, columns=["timestamp", "close"])
            df["volume"] = [v[1] for v in volumes]
            df["date"] = pd.to_datetime(df["timestamp"], unit="ms")

            # OHLCVデータを取得（より詳細なAPI）
            ohlc_data = self._get_ohlc_data(days)

            if ohlc_data is not None:
                # OHLCデータをマージ（closeカラムはohlc_dataのものを使用）
                # volumeとdateだけを残してマージ
                df = df[["date", "volume"]].merge(ohlc_data, on="date", how="left")
            else:
                # OHLCデータが取得できない場合は終値から推定
                df["open"] = df["close"].shift(1).fillna(df["close"])
                df["high"] = df["close"] * 1.02  # 簡易推定
                df["low"] = df["close"] * 0.98   # 簡易推定

            # カラムを整理
            df = df[["date", "open", "high", "low", "close", "volume"]]
            df.columns = ["Date", "Open", "High", "Low", "Close", "Volume"]
            df.set_index("Date", inplace=True)

            return df

        except requests.exceptions.RequestException as e:
            raise Exception(f"API接続エラー: {e}")
        except Exception as e:
            raise Exception(f"データ取得エラー: {e}")

    def _get_ohlc_data(self, days: int) -> pd.DataFrame:
        """
        OHLC（Open, High, Low, Close）データを取得

        Args:
            days: 取得する日数

        Returns:
            pd.DataFrame: OHLCデータ
        """
        try:
            url = f"{self.base_url}/coins/bitcoin/ohlc"
            params = {
                "vs_currency": "usd",
                "days": days
            }

            response = requests.get(url, params=params, timeout=10, verify=self.verify_ssl)
            response.raise_for_status()
            data = response.json()

            if not data:
                return None

            # [timestamp, open, high, low, close] の形式
            df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close"])
            df["date"] = pd.to_datetime(df["timestamp"], unit="ms")
            df = df[["date", "open", "high", "low", "close"]]

            return df

        except Exception:
            # OHLCデータが取得できない場合はNoneを返す
            return None

    def get_current_price(self) -> Dict[str, float]:
        """
        現在のビットコイン価格を取得

        Returns:
            Dict: 現在価格情報
        """
        try:
            url = f"{self.base_url}/simple/price"
            params = {
                "ids": "bitcoin",
                "vs_currencies": "usd",
                "include_24hr_change": "true",
                "include_24hr_vol": "true"
            }

            response = requests.get(url, params=params, timeout=10, verify=self.verify_ssl)
            response.raise_for_status()
            data = response.json()

            bitcoin_data = data.get("bitcoin", {})

            return {
                "price": bitcoin_data.get("usd", 0),
                "change_24h": bitcoin_data.get("usd_24h_change", 0),
                "volume_24h": bitcoin_data.get("usd_24h_vol", 0)
            }

        except Exception as e:
            raise Exception(f"現在価格の取得エラー: {e}")

    @staticmethod
    def generate_demo_data(days: int = 90, base_price: float = 90000) -> pd.DataFrame:
        """
        デモ用のサンプルOHLCVデータを生成

        Args:
            days: 生成する日数
            base_price: 基準価格

        Returns:
            pd.DataFrame: サンプルOHLCVデータ
        """
        np.random.seed(42)
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')

        data = []
        price = base_price

        for date in dates:
            # ランダムウォークで価格を変動
            change_pct = np.random.normal(0, 0.02)  # 平均0%, 標準偏差2%
            price = price * (1 + change_pct)

            # OHLC生成
            open_price = price * (1 + np.random.normal(0, 0.005))
            high_price = max(open_price, price) * (1 + abs(np.random.normal(0, 0.01)))
            low_price = min(open_price, price) * (1 - abs(np.random.normal(0, 0.01)))
            close_price = price

            # 出来高生成（ランダム）
            volume = np.random.uniform(20_000_000_000, 50_000_000_000)

            data.append({
                'Date': date,
                'Open': open_price,
                'High': high_price,
                'Low': low_price,
                'Close': close_price,
                'Volume': volume
            })

        df = pd.DataFrame(data)
        df.set_index('Date', inplace=True)

        return df


if __name__ == "__main__":
    # テスト用
    client = BitcoinAPIClient()

    print("ビットコインの現在価格を取得中...")
    current = client.get_current_price()
    print(f"現在価格: ${current['price']:,.2f}")
    print(f"24時間変化: {current['change_24h']:.2f}%")
    print(f"24時間出来高: ${current['volume_24h']:,.0f}")

    print("\n過去90日分のデータを取得中...")
    df = client.get_daily_ohlcv(90)
    print(f"データ取得完了: {len(df)}日分")
    print(df.tail())
