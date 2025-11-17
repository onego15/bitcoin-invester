"""
BitcoinInvester - Streamlit WebUI

ビットコインチャート分析のWebアプリケーション
"""

import streamlit as st
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 環境変数を読み込み
load_dotenv()

# srcディレクトリをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.api_client import BitcoinAPIClient
from src.chart_analyzer import ChartAnalyzer

# ページ設定
st.set_page_config(
    page_title="BitcoinInvester - AI分析ツール",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .recommendation-buy {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
    }
    .recommendation-sell {
        background-color: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
    }
    .recommendation-hold {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
    }
</style>
""", unsafe_allow_html=True)


def create_candlestick_chart(df):
    """Plotlyでローソク足チャートを作成"""
    # サブプロットを作成（価格チャートと出来高）
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        subplot_titles=('Bitcoin Price (USD)', 'Volume'),
        row_heights=[0.7, 0.3]
    )

    # ローソク足チャート
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='OHLC',
            increasing_line_color='green',
            decreasing_line_color='red'
        ),
        row=1, col=1
    )

    # 移動平均線
    df_copy = df.copy()
    df_copy['MA7'] = df_copy['Close'].rolling(window=7).mean()
    df_copy['MA25'] = df_copy['Close'].rolling(window=25).mean()

    fig.add_trace(
        go.Scatter(
            x=df_copy.index,
            y=df_copy['MA7'],
            name='MA7',
            line=dict(color='blue', width=1.5)
        ),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(
            x=df_copy.index,
            y=df_copy['MA25'],
            name='MA25',
            line=dict(color='red', width=1.5)
        ),
        row=1, col=1
    )

    # 出来高
    colors = ['green' if row['Close'] >= row['Open'] else 'red'
              for _, row in df.iterrows()]

    fig.add_trace(
        go.Bar(
            x=df.index,
            y=df['Volume'],
            name='Volume',
            marker_color=colors,
            showlegend=False
        ),
        row=2, col=1
    )

    # レイアウト設定
    fig.update_layout(
        title='Bitcoin (BTC/USD) Daily Chart',
        yaxis_title='Price (USD)',
        yaxis2_title='Volume',
        xaxis_rangeslider_visible=False,
        height=700,
        hovermode='x unified'
    )

    fig.update_xaxes(title_text="Date", row=2, col=1)

    return fig


def main():
    # ヘッダー
    st.markdown('<div class="main-header">💰 BitcoinInvester</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AIによるビットコインチャート分析ツール</div>', unsafe_allow_html=True)

    # サイドバー
    with st.sidebar:
        st.header("⚙️ 設定")

        # データ取得設定
        st.subheader("データ取得")
        use_demo = st.checkbox("デモモード（サンプルデータ）", value=False)
        days = st.slider("取得日数", min_value=30, max_value=365, value=90, step=10)

        # AI分析設定
        st.subheader("AI分析")
        analyze_days = st.slider("分析期間（日）", min_value=7, max_value=90, value=30, step=1)
        enable_ai = st.checkbox("AI分析を実行", value=False)

        st.divider()

        # 実行ボタン
        run_button = st.button("🚀 分析実行", type="primary", use_container_width=True)

    # メインエリア
    if run_button:
        try:
            # データ取得
            with st.spinner('ビットコインデータを取得中...'):
                if use_demo:
                    df = BitcoinAPIClient.generate_demo_data(days)
                    st.success(f'✓ {len(df)}日分のサンプルデータを生成しました')
                else:
                    client = BitcoinAPIClient()
                    df = client.get_daily_ohlcv(days)
                    st.success(f'✓ {len(df)}日分のデータを取得しました')

                    # 現在価格を表示
                    current_price = client.get_current_price()
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("現在価格", f"${current_price['price']:,.2f}")
                    with col2:
                        st.metric("24時間変化", f"{current_price['change_24h']:+.2f}%",
                                 delta=f"{current_price['change_24h']:+.2f}%")
                    with col3:
                        st.metric("24時間出来高", f"${current_price['volume_24h']/1e9:.2f}B")

            # チャート表示
            st.subheader("📈 チャート")

            # NaN値を除去
            df_clean = df.dropna(subset=['Open', 'High', 'Low', 'Close'])

            if len(df_clean) == 0:
                st.error("有効なデータがありません")
                return

            # Plotlyチャートを作成して表示
            fig = create_candlestick_chart(df_clean)
            st.plotly_chart(fig, use_container_width=True)

            # サマリー情報
            with st.expander("📊 チャートサマリー", expanded=True):
                latest = df_clean.iloc[-1]
                previous = df_clean.iloc[-2] if len(df_clean) > 1 else latest
                change = latest['Close'] - previous['Close']
                change_pct = (change / previous['Close']) * 100

                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**最新の価格情報**")
                    st.write(f"日付: {latest.name.strftime('%Y-%m-%d')}")
                    st.write(f"始値: ${latest['Open']:,.2f}")
                    st.write(f"高値: ${latest['High']:,.2f}")
                    st.write(f"安値: ${latest['Low']:,.2f}")
                    st.write(f"終値: ${latest['Close']:,.2f}")
                    st.write(f"前日比: ${change:+,.2f} ({change_pct:+.2f}%)")

                with col2:
                    st.markdown("**期間内の統計**")
                    st.write(f"期間: {df_clean.index[0].strftime('%Y-%m-%d')} 〜 {df_clean.index[-1].strftime('%Y-%m-%d')}")
                    st.write(f"データ数: {len(df_clean)}日分")
                    st.write(f"最高値: ${df_clean['High'].max():,.2f}")
                    st.write(f"最安値: ${df_clean['Low'].min():,.2f}")
                    st.write(f"平均終値: ${df_clean['Close'].mean():,.2f}")

            # AI分析
            if enable_ai:
                st.subheader("🤖 AI分析結果")

                if use_demo:
                    st.warning("⚠️ デモモードではAI分析は利用できません")
                else:
                    # 環境変数からAPIキーを取得
                    api_key = os.getenv("OPENAI_API_KEY")

                    if not api_key:
                        st.error("⚠️ OPENAI_API_KEYが設定されていません")
                        st.info("""
                        **設定方法:**
                        1. `.env`ファイルを作成
                        2. `OPENAI_API_KEY=your-api-key` を記載
                        3. アプリを再起動してください
                        """)
                    else:
                        with st.spinner('AI分析を実行中...'):
                            analyzer = ChartAnalyzer()
                            result = analyzer.analyze(df_clean, days=analyze_days)

                            # 推奨アクションに応じたスタイル
                            recommendation = result['recommendation']
                            if recommendation == '買い':
                                style_class = 'recommendation-buy'
                                icon = '📈'
                            elif recommendation == '売り':
                                style_class = 'recommendation-sell'
                                icon = '📉'
                            else:
                                style_class = 'recommendation-hold'
                                icon = '⏸️'

                            # 推奨アクションを表示
                            st.markdown(f"""
                            <div class="{style_class}">
                                <h3>{icon} 推奨アクション: {recommendation}</h3>
                                <p><strong>確信度:</strong> {result['confidence']}</p>
                            </div>
                            """, unsafe_allow_html=True)

                            # 詳細な分析結果
                            st.markdown("### 詳細分析")
                            st.markdown(result['reasoning'])

                            # 免責事項
                            st.warning("""
                            **⚠️ 免責事項**
                            この分析結果はあくまで参考情報です。投資判断は自己責任で行ってください。
                            暗号資産投資には高いリスクが伴います。
                            """)

        except Exception as e:
            st.error(f"❌ エラーが発生しました: {str(e)}")
            st.exception(e)

    else:
        # 初期画面
        st.info("👈 左のサイドバーで設定を行い、「分析実行」ボタンをクリックしてください")

        # 使い方説明
        with st.expander("📖 使い方", expanded=True):
            st.markdown("""
            ### 基本的な使い方

            1. **サイドバーで設定を行う**
               - デモモード：サンプルデータで試す場合はチェック
               - 取得日数：表示するデータの期間を選択（30〜365日）
               - 分析期間：AI分析の対象期間を選択（7〜90日）

            2. **AI分析を有効にする（オプション）**
               - 「AI分析を実行」にチェック
               - 事前に`.env`ファイルにOpenAI API Keyを設定してください

            3. **「分析実行」ボタンをクリック**
               - ビットコインのチャートが表示されます
               - AI分析を有効にした場合は、売買判断も表示されます

            ### 機能

            - **ローソク足チャート**: 日足のローソク足と出来高を表示
            - **移動平均線**: 7日・25日移動平均線を自動計算
            - **AI分析**: Markdownで定義したルールに基づいてAIが分析
            - **売買判断**: 買い・売り・様子見の推奨アクションを表示
            """)

        with st.expander("⚙️ 分析ルールのカスタマイズ"):
            st.markdown("""
            `rules/analysis_rules.md` ファイルを編集することで、AI分析のルールをカスタマイズできます。

            - トレンド分析の基準
            - ローソク足パターンの定義
            - 出来高分析の方法
            - 移動平均線の使い方
            - 売買判断の条件

            AIはこのMarkdownファイルを読み込んで、記載されたルールに従ってチャートを分析します。
            """)


if __name__ == "__main__":
    main()
