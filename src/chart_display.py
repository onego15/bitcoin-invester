"""チャート表示モジュール"""

import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
from typing import Optional
import os


class ChartDisplay:
    """ビットコインのローソク足チャートを表示するクラス"""

    def __init__(self, output_dir: str = "charts"):
        """
        Args:
            output_dir: チャート画像の保存先ディレクトリ
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def plot_candlestick_chart(
        self,
        df: pd.DataFrame,
        title: str = "Bitcoin (BTC/USD) Daily Chart",
        save_path: Optional[str] = None,
        show: bool = False
    ) -> str:
        """
        ローソク足チャートを作成（出来高付き）

        Args:
            df: OHLCVデータを含むDataFrame
            title: チャートのタイトル
            save_path: 保存先パス（Noneの場合は自動生成）
            show: チャートを表示するか

        Returns:
            str: 保存されたファイルのパス
        """
        # データの検証
        required_columns = ["Open", "High", "Low", "Close", "Volume"]
        for col in required_columns:
            if col not in df.columns:
                raise ValueError(f"DataFrameに'{col}'カラムが必要です")

        # 保存先パスの設定
        if save_path is None:
            save_path = os.path.join(self.output_dir, "bitcoin_chart.png")

        # 移動平均線を計算
        df = df.copy()
        df["MA7"] = df["Close"].rolling(window=7).mean()
        df["MA25"] = df["Close"].rolling(window=25).mean()

        # 移動平均線の設定
        ma_lines = [
            mpf.make_addplot(df["MA7"], color="blue", width=1.5, label="MA7"),
            mpf.make_addplot(df["MA25"], color="red", width=1.5, label="MA25")
        ]

        # チャートスタイルの設定
        mc = mpf.make_marketcolors(
            up="green",      # 陽線の色
            down="red",      # 陰線の色
            edge="inherit",  # 枠線の色
            wick="inherit",  # ヒゲの色
            volume="in",     # 出来高の色（価格と同じ）
        )

        style = mpf.make_mpf_style(
            marketcolors=mc,
            gridstyle=":",
            y_on_right=False
        )

        # チャートの描画
        fig, axes = mpf.plot(
            df,
            type="candle",         # ローソク足
            style=style,
            volume=True,           # 出来高を表示
            addplot=ma_lines,      # 移動平均線を追加
            title=title,
            ylabel="Price (USD)",
            ylabel_lower="Volume",
            figsize=(14, 8),
            returnfig=True,
            datetime_format="%Y-%m-%d",
            xrotation=15
        )

        # 凡例を追加
        axes[0].legend(["MA7", "MA25"], loc="upper left")

        # 保存
        fig.savefig(save_path, dpi=150, bbox_inches="tight")
        print(f"チャートを保存しました: {save_path}")

        # 表示
        if show:
            plt.show()
        else:
            plt.close(fig)

        return save_path

    def get_chart_summary(self, df: pd.DataFrame) -> str:
        """
        チャートデータの簡単なサマリーを取得

        Args:
            df: OHLCVデータを含むDataFrame

        Returns:
            str: サマリー文字列
        """
        latest = df.iloc[-1]
        previous = df.iloc[-2] if len(df) > 1 else latest

        change = latest["Close"] - previous["Close"]
        change_pct = (change / previous["Close"]) * 100

        summary = f"""
=== ビットコイン チャートサマリー ===
期間: {df.index[0].strftime('%Y-%m-%d')} 〜 {df.index[-1].strftime('%Y-%m-%d')}
データ数: {len(df)}日分

【最新の価格情報】
日付: {latest.name.strftime('%Y-%m-%d')}
始値: ${latest['Open']:,.2f}
高値: ${latest['High']:,.2f}
安値: ${latest['Low']:,.2f}
終値: ${latest['Close']:,.2f}
出来高: ${latest['Volume']:,.0f}

前日比: ${change:+,.2f} ({change_pct:+.2f}%)

【期間内の統計】
最高値: ${df['High'].max():,.2f}
最安値: ${df['Low'].min():,.0f}
平均終値: ${df['Close'].mean():,.2f}
平均出来高: ${df['Volume'].mean():,.0f}
"""
        return summary


if __name__ == "__main__":
    # テスト用
    from api_client import BitcoinAPIClient

    print("ビットコインデータを取得中...")
    client = BitcoinAPIClient()
    df = client.get_daily_ohlcv(90)

    print("チャートを作成中...")
    chart = ChartDisplay()

    # サマリーを表示
    print(chart.get_chart_summary(df))

    # チャートを作成
    chart_path = chart.plot_candlestick_chart(df)
    print(f"\n完了! チャートは {chart_path} に保存されました")
