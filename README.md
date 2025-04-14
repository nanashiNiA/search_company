# 企業イベントリスト作成プロジェクト

## 概要

このプロジェクトは、指定された情報源から企業のイベント情報を収集し、Gemini API を活用して情報を整理・抽出し、最終的に Google スプレッドシートまたは Excel ファイルにリストとして出力することを目的としています。

詳細なプロジェクト計画については、[`docs/plan.md`](docs/plan.md) を参照してください。

## 機能 (予定)

*   Webサイトからのイベント情報スクレイピング
*   (オプション) APIやRSSフィードからの情報収集
*   Gemini API を利用した情報抽出 (日時、場所、概要生成、カテゴリ分類など)
*   収集データの整形と重複排除
*   Google スプレッドシートまたは Excel ファイルへの出力
*   設定ファイルによる収集対象や出力形式のカスタマイズ
*   定期実行による自動化

## セットアップ

1.  **リポジトリのクローン:**
    ```bash
    git clone <リポジトリURL>
    cd <プロジェクトディレクトリ名>
    ```

2.  **Python環境の準備:**
    Python 3.9 以降が必要です。仮想環境の作成を推奨します。
    ```bash
    python -m venv venv
    # Windows
    .\venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **依存ライブラリのインストール:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **環境変数の設定:**
    `.env.example` ファイルをコピーして `.env` ファイルを作成します。
    ```bash
    cp .env.example .env
    ```
    作成した `.env` ファイルを開き、必要なAPIキーなどを設定してください。(例: `GEMINI_API_KEY=`)
    **注意:** `.env` ファイルは機密情報を含むため、Git管理対象外です (`.gitignore` に記載済み)。

5.  **(Google Sheets利用時) 認証情報の設定:**
    Google Cloud Platform でサービスアカウントを作成し、認証用のJSONキーファイルをダウンロードします。ダウンロードしたキーファイルのパスを環境変数 (`GOOGLE_APPLICATION_CREDENTIALS`) に設定するか、`config/config.yaml` などで指定する想定です。詳細は Google Sheets API のドキュメントを参照してください。

## 使い方

(実行方法をここに記述します。例: )

```bash
python src/main.py [--config config/config.yaml] [--output data/processed/events.xlsx]
```

*   設定ファイル (`config.yaml`) で情報源、出力先などを指定します。
*   コマンドライン引数で設定を上書きすることも可能です (実装による)。

## ディレクトリ構造

プロジェクトのディレクトリ構造については、[`structure.yaml`](structure.yaml) を参照してください。

## 貢献

(貢献に関するガイドラインがあれば記述)

## ライセンス

(ライセンス情報を記述。例: MIT License)