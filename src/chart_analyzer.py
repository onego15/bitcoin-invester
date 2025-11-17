"""AI チャート分析モジュール"""

import os
from typing import Dict, Optional
import pandas as pd
from anthropic import Anthropic


class ChartAnalyzer:
    """AIを使用してビットコインチャートを分析するクラス"""

    def __init__(self, api_key: Optional[str] = None, rules_path: str = "rules/analysis_rules.md"):
        """
        Args:
            api_key: Anthropic APIキー（Noneの場合は環境変数から取得）
            rules_path: 分析ルールのMarkdownファイルパス
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError(
                "ANTHROPIC_API_KEYが設定されていません。"
                "環境変数に設定するか、コンストラクタで指定してください。"
            )

        self.client = Anthropic(api_key=self.api_key)
        self.rules_path = rules_path
        self.analysis_rules = self._load_rules()

    def _load_rules(self) -> str:
        """分析ルールをMarkdownファイルから読み込む"""
        try:
            with open(self.rules_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"分析ルールファイルが見つかりません: {self.rules_path}")

    def _prepare_chart_data_summary(self, df: pd.DataFrame, days: int = 30) -> str:
        """
        チャートデータをテキスト形式でサマリー化

        Args:
            df: OHLCVデータ
            days: 分析する日数

        Returns:
            str: データサマリー
        """
        # 最新N日分のデータを取得
        recent_df = df.tail(days).copy()

        # 移動平均線を計算
        recent_df["MA7"] = recent_df["Close"].rolling(window=7).mean()
        recent_df["MA25"] = recent_df["Close"].rolling(window=25).mean()

        # データサマリーを作成
        summary_parts = []

        # 全体の統計情報
        summary_parts.append("【期間全体の統計】")
        summary_parts.append(f"分析期間: {recent_df.index[0].strftime('%Y-%m-%d')} 〜 {recent_df.index[-1].strftime('%Y-%m-%d')}")
        summary_parts.append(f"最高値: ${recent_df['High'].max():,.2f}")
        summary_parts.append(f"最安値: ${recent_df['Low'].min():,.2f}")
        summary_parts.append(f"平均終値: ${recent_df['Close'].mean():,.2f}")
        summary_parts.append(f"平均出来高: ${recent_df['Volume'].mean():,.0f}")
        summary_parts.append("")

        # 最新の価格情報
        latest = recent_df.iloc[-1]
        previous = recent_df.iloc[-2] if len(recent_df) > 1 else latest

        change = latest["Close"] - previous["Close"]
        change_pct = (change / previous["Close"]) * 100

        summary_parts.append("【最新の価格情報】")
        summary_parts.append(f"日付: {latest.name.strftime('%Y-%m-%d')}")
        summary_parts.append(f"始値: ${latest['Open']:,.2f}")
        summary_parts.append(f"高値: ${latest['High']:,.2f}")
        summary_parts.append(f"安値: ${latest['Low']:,.2f}")
        summary_parts.append(f"終値: ${latest['Close']:,.2f}")
        summary_parts.append(f"出来高: ${latest['Volume']:,.0f}")
        summary_parts.append(f"前日比: ${change:+,.2f} ({change_pct:+.2f}%)")
        summary_parts.append(f"7日移動平均: ${latest['MA7']:,.2f}")
        summary_parts.append(f"25日移動平均: ${latest['MA25']:,.2f}")
        summary_parts.append("")

        # 最近5日間のローソク足データ
        summary_parts.append("【直近5日間のローソク足データ】")
        for i in range(min(5, len(recent_df))):
            row = recent_df.iloc[-(5-i)]
            candle_type = "陽線" if row["Close"] >= row["Open"] else "陰線"
            body_size = abs(row["Close"] - row["Open"])
            upper_wick = row["High"] - max(row["Open"], row["Close"])
            lower_wick = min(row["Open"], row["Close"]) - row["Low"]

            summary_parts.append(
                f"{row.name.strftime('%Y-%m-%d')}: {candle_type} | "
                f"始値${row['Open']:,.0f} 高値${row['High']:,.0f} "
                f"安値${row['Low']:,.0f} 終値${row['Close']:,.0f} | "
                f"実体${body_size:,.0f} 上ヒゲ${upper_wick:,.0f} 下ヒゲ${lower_wick:,.0f} | "
                f"出来高${row['Volume']:,.0f}"
            )
        summary_parts.append("")

        # トレンド情報
        summary_parts.append("【トレンド情報】")
        if len(recent_df) >= 7:
            ma7_trend = "上向き" if recent_df["MA7"].iloc[-1] > recent_df["MA7"].iloc[-7] else "下向き"
            summary_parts.append(f"7日移動平均のトレンド: {ma7_trend}")

        if len(recent_df) >= 25:
            ma25_trend = "上向き" if recent_df["MA25"].iloc[-1] > recent_df["MA25"].iloc[-25] else "下向き"
            summary_parts.append(f"25日移動平均のトレンド: {ma25_trend}")

        if pd.notna(latest["MA7"]) and pd.notna(latest["MA25"]):
            if latest["MA7"] > latest["MA25"]:
                summary_parts.append("移動平均線の位置: 短期が長期の上（強気）")
            else:
                summary_parts.append("移動平均線の位置: 短期が長期の下（弱気）")

        return "\n".join(summary_parts)

    def analyze(self, df: pd.DataFrame, days: int = 30) -> Dict[str, str]:
        """
        チャートを分析して売買判断を提供

        Args:
            df: OHLCVデータ
            days: 分析する日数

        Returns:
            Dict: 分析結果（recommendation, reasoning, confidence）
        """
        # チャートデータをサマリー化
        chart_summary = self._prepare_chart_data_summary(df, days)

        # AIに分析を依頼
        prompt = f"""あなたはビットコインのチャート分析の専門家です。
以下の分析ルールとチャートデータに基づいて、現在のビットコインが「買い」「売り」「様子見」のどれに該当するか判断してください。

# 分析ルール
{self.analysis_rules}

# チャートデータ
{chart_summary}

# 指示
上記の分析ルールに従って、以下の形式で回答してください：

**判断**: [買い/売り/様子見]
**確信度**: [高/中/低]
**理由**:
- [理由1]
- [理由2]
- [理由3]
...

**注意点**:
- [投資家が注意すべきポイント]

明確で簡潔な回答をお願いします。"""

        try:
            # Claude APIを呼び出し
            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            analysis_result = message.content[0].text

            # 結果をパース
            recommendation = "様子見"  # デフォルト
            if "**判断**: 買い" in analysis_result or "判断**: 買い" in analysis_result:
                recommendation = "買い"
            elif "**判断**: 売り" in analysis_result or "判断**: 売り" in analysis_result:
                recommendation = "売り"

            confidence = "中"  # デフォルト
            if "**確信度**: 高" in analysis_result or "確信度**: 高" in analysis_result:
                confidence = "高"
            elif "**確信度**: 低" in analysis_result or "確信度**: 低" in analysis_result:
                confidence = "低"

            return {
                "recommendation": recommendation,
                "confidence": confidence,
                "reasoning": analysis_result,
                "chart_summary": chart_summary
            }

        except Exception as e:
            raise Exception(f"AI分析エラー: {e}")


if __name__ == "__main__":
    # テスト用
    from api_client import BitcoinAPIClient

    print("ビットコインデータを取得中...")
    client = BitcoinAPIClient()
    df = client.get_daily_ohlcv(90)

    print("\nAI分析を実行中...")
    analyzer = ChartAnalyzer()
    result = analyzer.analyze(df, days=30)

    print("\n" + "=" * 60)
    print("AI分析結果")
    print("=" * 60)
    print(result["reasoning"])
    print("\n" + "=" * 60)
    print(f"推奨アクション: {result['recommendation']}")
    print(f"確信度: {result['confidence']}")
    print("=" * 60)
