# BitcoinInvester

AIエージェントを使用したビットコインチャート分析ツール

## 概要

BitcoinInvesterは、ビットコインのチャートを分析し、AIエージェント（OpenAI GPT-4o）が買い・売り・様子見の判断を提供するプロトタイプツールです。

### 主な機能

- **ビットコインデータ取得**: CoinGecko APIを使用して最新のビットコイン価格データを取得
- **ローソク足チャート表示**: 日足のローソク足チャートと出来高を表示
- **移動平均線**: 7日・25日移動平均線を自動計算して表示
- **AI分析エージェント**: Markdownで定義したルールに基づいてAIがチャートを分析
- **売買判断**: 買い・売り・様子見の推奨アクションと理由を提供
- **社内プロキシ対応**: カスタムヘッダー（X-User-Id、X-Title）をサポート

## セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd bitcoin-invester
```

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定

`.env.example`をコピーして`.env`ファイルを作成し、OpenAI API設定を行ってください。

```bash
cp .env.example .env
```

`.env`ファイルを編集：

#### 標準のOpenAI APIを使用する場合

```bash
OPENAI_API_KEY=sk-your-api-key
```

#### 社内プロキシを使用する場合

```bash
# APIキー（プロキシから取得）
OPENAI_API_KEY=ok-your-api-key

# プロキシのベースURL
OPENAI_API_BASE=https://openai-proxy-apigw-genai.api.linecorp.com/v1

# 社員ID（オプション）
OPENAI_USER_ID=your-employee-id

# アプリケーション識別子（オプション）
OPENAI_APP_TITLE=BitcoinInvester
```

## 使用方法

### 基本的な使い方

```bash
python src/main.py
```

このコマンドは以下を実行します：
1. 過去90日分のビットコインデータを取得
2. 現在価格を表示
3. ローソク足チャートを生成（`charts/bitcoin_chart.png`に保存）
4. 直近30日間のデータをAIが分析し、売買判断を提供

### オプション

```bash
# 取得する日数を指定（デフォルト: 90日）
python src/main.py -d 180

# 分析対象の日数を指定（デフォルト: 30日）
python src/main.py -a 60

# チャート生成のみ（AI分析をスキップ）
python src/main.py --chart-only

# AI分析のみ（チャート生成をスキップ）
python src/main.py --no-chart

# チャート保存先を指定
python src/main.py -o my_chart.png

# ヘルプを表示
python src/main.py --help
```

### 使用例

```bash
# 過去180日分のデータを取得し、直近60日分を分析
python src/main.py -d 180 -a 60

# チャート生成のみ実行
python src/main.py --chart-only -d 365
```

## プロジェクト構造

```
bitcoin-invester/
├── README.md                    # このファイル
├── requirements.txt             # Python依存関係
├── .env.example                 # 環境変数のサンプル
├── .gitignore                   # Git除外設定
├── rules/
│   └── analysis_rules.md        # チャート分析ルール（カスタマイズ可能）
├── src/
│   ├── __init__.py
│   ├── api_client.py            # ビットコインデータ取得
│   ├── chart_display.py         # チャート表示
│   ├── chart_analyzer.py        # AI分析エージェント
│   └── main.py                  # メインアプリケーション
└── charts/                      # 生成されたチャート画像
```

## 分析ルールのカスタマイズ

`rules/analysis_rules.md`ファイルを編集することで、AI分析のルールをカスタマイズできます。

このファイルには以下のような内容を記述できます：
- トレンド分析の基準
- ローソク足パターンの定義
- 出来高分析の方法
- 移動平均線の使い方
- 売買判断の条件

AIはこのMarkdownファイルを読み込んで、記載されたルールに従ってチャートを分析します。

## 技術スタック

- **Python 3.7+**
- **OpenAI API (GPT-4o)**: AI分析エージェント
- **CoinGecko API**: ビットコイン価格データ取得（無料）
- **mplfinance**: ローソク足チャート表示
- **pandas**: データ処理
- **requests**: HTTP通信

## 注意事項

### 免責事項

**このツールはプロトタイプであり、教育・研究目的のみで使用してください。**

- この分析結果はあくまで参考情報です
- 投資判断は自己責任で行ってください
- 暗号資産投資には高いリスクが伴います
- 金銭的損失について開発者は一切の責任を負いません

### APIレート制限

- CoinGecko API: 無料プランでは1分間に10-50リクエストの制限があります
- OpenAI API: 使用量に応じて課金されます（プランによって異なります）

## 開発・カスタマイズ

### 各モジュールの単体テスト

```bash
# API接続テスト
python src/api_client.py

# チャート表示テスト
python src/chart_display.py

# AI分析テスト
python src/chart_analyzer.py
```

### 拡張アイデア

- 複数の暗号通貨に対応
- テクニカル指標（RSI、MACD等）の追加
- バックテスト機能の実装
- Webアプリケーション化
- リアルタイム監視機能
- 通知機能（LINE、Slack等）

## ライセンス

MIT License

## 作成者

1日プロトタイピング課題として作成
