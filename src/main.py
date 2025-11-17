#!/usr/bin/env python3
"""
BitcoinInvester - ビットコインチャート分析ツール

ビットコインのチャートを分析し、AIエージェントが買い・売り・様子見の判断を提供します。
"""

import argparse
import os
import sys
from dotenv import load_dotenv

from api_client import BitcoinAPIClient
from chart_display import ChartDisplay
from chart_analyzer import ChartAnalyzer


def print_banner():
    """アプリケーションバナーを表示"""
    banner = """
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║              BitcoinInvester v0.1.0                       ║
║        AIによるビットコインチャート分析ツール                   ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
"""
    print(banner)


def main():
    """メイン処理"""
    # 環境変数を読み込み
    load_dotenv()

    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(
        description="BitcoinInvester - AIによるビットコインチャート分析ツール"
    )
    parser.add_argument(
        "-d", "--days",
        type=int,
        default=90,
        help="取得する日数（デフォルト: 90日）"
    )
    parser.add_argument(
        "-a", "--analyze-days",
        type=int,
        default=30,
        help="分析対象の日数（デフォルト: 30日）"
    )
    parser.add_argument(
        "--no-chart",
        action="store_true",
        help="チャート生成をスキップ"
    )
    parser.add_argument(
        "--chart-only",
        action="store_true",
        help="チャート生成のみ実行（AI分析をスキップ）"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default="charts/bitcoin_chart.png",
        help="チャート画像の保存先（デフォルト: charts/bitcoin_chart.png）"
    )
    parser.add_argument(
        "--demo",
        action="store_true",
        help="デモモード（サンプルデータを使用）"
    )
    parser.add_argument(
        "--no-ssl-verify",
        action="store_true",
        help="SSL証明書の検証をスキップ（開発環境用）"
    )

    args = parser.parse_args()

    # バナー表示
    print_banner()

    try:
        # Step 1: ビットコインデータの取得
        if args.demo:
            print(f"[1/4] デモモード: サンプルデータを生成中... ({args.days}日分)")
            df = BitcoinAPIClient.generate_demo_data(args.days)
            print(f"✓ {len(df)}日分のサンプルデータを生成しました")
        else:
            print(f"[1/4] ビットコインデータを取得中... ({args.days}日分)")
            api_client = BitcoinAPIClient(verify_ssl=not args.no_ssl_verify)

            if args.no_ssl_verify:
                print("⚠ 警告: SSL証明書の検証を無効化しています")

            df = api_client.get_daily_ohlcv(args.days)
            print(f"✓ {len(df)}日分のデータを取得しました")

        # Step 2: 現在価格の取得
        if args.demo:
            print("\n[2/4] デモモード: 現在価格をスキップ")
            latest_price = df.iloc[-1]['Close']
            print(f"最新終値: ${latest_price:,.2f}")
        else:
            print("\n[2/4] 現在価格を取得中...")
            current_price = api_client.get_current_price()
            print(f"✓ 現在価格: ${current_price['price']:,.2f}")
            print(f"  24時間変化: {current_price['change_24h']:+.2f}%")
            print(f"  24時間出来高: ${current_price['volume_24h']:,.0f}")

        # Step 3: チャート生成
        if not args.no_chart:
            print(f"\n[3/4] ローソク足チャートを生成中...")
            chart_display = ChartDisplay()
            chart_path = chart_display.plot_candlestick_chart(
                df,
                title=f"Bitcoin (BTC/USD) Daily Chart - Last {args.days} Days",
                save_path=args.output
            )
            print(f"✓ チャートを保存しました: {chart_path}")

            # チャートサマリーを表示
            print("\n" + chart_display.get_chart_summary(df))
        else:
            print("\n[3/4] チャート生成をスキップしました")

        # Step 4: AI分析
        if not args.chart_only:
            print(f"\n[4/4] AI分析を実行中... (分析期間: {args.analyze_days}日)")

            # ANTHROPIC_API_KEYの確認
            if not os.getenv("ANTHROPIC_API_KEY"):
                print("\n⚠ エラー: ANTHROPIC_API_KEYが設定されていません")
                print("環境変数にANTHROPIC_API_KEYを設定するか、.envファイルに記載してください")
                print("\n例: export ANTHROPIC_API_KEY='your-api-key'")
                sys.exit(1)

            analyzer = ChartAnalyzer()
            result = analyzer.analyze(df, days=args.analyze_days)

            print("✓ 分析完了\n")

            # 分析結果を表示
            print("=" * 70)
            print("                    AI分析結果")
            print("=" * 70)
            print(result["reasoning"])
            print("\n" + "=" * 70)
            print(f"【推奨アクション】: {result['recommendation']}")
            print(f"【確信度】: {result['confidence']}")
            print("=" * 70)

            # 免責事項
            print("\n⚠ 免責事項:")
            print("この分析結果はあくまで参考情報です。")
            print("投資判断は自己責任で行ってください。")
            print("暗号資産投資には高いリスクが伴います。")

        else:
            print("\n[4/4] AI分析をスキップしました")

        print("\n✓ 処理が完了しました\n")

    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
