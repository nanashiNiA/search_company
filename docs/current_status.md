# プロジェクト現状報告

## 1. プロジェクト概要

**目的:** Webサイトから企業関連イベントの情報を収集し、構造化データとして整理・出力する。

**主な技術スタック:**

*   Python
*   Requests (HTTPリクエスト)
*   PyYAML (設定ファイル読み込み)
*   python-dotenv (環境変数管理)
*   google-generativeai (Gemini API 利用)
*   (将来的) openpyxl (Excel出力), google-api-python-client等 (Google Sheets出力)

## 2. 現在の実装方針

情報収集の主要なアプローチとして、当初のCSSセレクタベースのスクレイピングから**Gemini APIによる直接HTML抽出方式**に変更しました。

*   **情報収集:** 指定されたURLからHTMLコンテンツを取得する (`fetch_html`)。
*   **情報抽出:** 取得したHTML全体をGemini APIに送信し、設定ファイル (`config.yaml`) 内のプロンプト (`html_extraction_prompt_template`) に基づいてイベント情報をJSON形式で抽出する (`scrape_events`)。
*   **情報処理 (未実装):** 抽出されたデータに対し、Gemini APIを用いて要約作成やカテゴリ分類などを行う。
*   **出力 (未実装):** 最終的なデータをExcelファイルまたはGoogleスプレッドシートに出力する。

## 3. 実装済みの主要コンポーネント

*   **設定ファイル (`config/`)**
    *   `config.yaml`:
        *   出力形式 (`output_format`), 出力ファイルパス (`output_file_path`)
        *   情報収集対象リスト (`target_sources`): `name`, `url`, `type` を含む。
        *   Gemini API設定 (`gemini_model`, 各種プロンプトテンプレート, `safety_settings`)
            *   **`html_extraction_prompt_template`**: HTMLから直接JSONリストを抽出するためのプロンプトが追加されました。
            *   `extraction_prompt_template`, `summary_prompt_template`, `category_prompt_template`: テキスト処理用のプロンプト (現状の直接抽出方式ではすぐには使われない可能性あり)。
        *   ロギング設定 (`log_level`, `log_file`)
    *   `.env.example`, `.env`: APIキーなどの機密情報を管理。`GEMINI_API_KEY` が必須。

*   **ユーティリティ (`src/utils/`)**
    *   `config_loader.py`: `config.yaml` を読み込む `load_config()` 関数。
    *   `gemini_client.py`: `.env` からAPIキーを読み込み、`config.yaml` の設定に基づいてGemini APIクライアント (`GenerativeModel`) を初期化する `initialize_gemini()` 関数。

*   **情報収集・抽出 (`src/collector/`)**
    *   `website_scraper.py`:
        *   `fetch_html(url)`: 指定されたURLからHTMLコンテンツを取得する関数。
        *   `scrape_events(html_content, config)`:
            *   `initialize_gemini()` でGeminiクライアントを準備。
            *   `config` から `html_extraction_prompt_template` を取得。
            *   HTMLコンテンツを埋め込んだプロンプトをGemini APIに送信 (`generate_content`)。
            *   APIのレスポンス (JSON形式のテキストを期待) をパースし、イベント情報の辞書のリスト (`list[dict]`) として返す。
            *   APIエラー、JSONパースエラー等の基本的なエラーハンドリングを含む。

## 4. 実行に必要な準備

1.  **環境変数設定:** プロジェクトルートに `.env` ファイルを作成 (または `.env.example` をコピー) し、`GEMINI_API_KEY` に有効なGoogle AI StudioのAPIキーを設定します。
    ```.env
    GEMINI_API_KEY="YOUR_API_KEY_HERE"
    # 必要に応じて GOOGLE_APPLICATION_CREDENTIALS も設定
    ```
2.  **依存ライブラリ:** `requirements.txt` に以下のライブラリが含まれていることを確認し、インストールします。
    ```bash
    pip install -r requirements.txt
    ```
    必要なライブラリ (例): `requests`, `PyYAML`, `python-dotenv`, `google-generativeai`
3.  **ターゲットURLの指定:** `config/config.yaml` 内の `target_sources` リストにある収集したいサイトの `url` を、実際にイベント情報が掲載されているページのURLに変更します。
    ```yaml
    target_sources:
      - name: "Tech Conference Site"
        url: "https://techconference.com/upcoming-events"
        type: "website_scrape"
    ```

## 5. テスト実行

上記準備完了後、以下のコマンドでHTML取得とGeminiによる情報抽出のテストを実行できます。

```bash
python src/collector/website_scraper.py
```

実行すると、指定されたURLからHTMLを取得し、その内容をGemini APIに送信して抽出結果 (JSONリスト) がコンソールに出力されます。

## 6. 今後のステップ (案)

1.  **抽出テストとプロンプト調整:** 実際のターゲットサイトでテストを実行し、期待通りの情報が抽出できるか確認します。必要に応じて `config.yaml` の `html_extraction_prompt_template` を調整します。
2.  **メインスクリプト作成 (`main.py`):** 設定を読み込み、`target_sources` をループして各サイトから情報を収集・抽出する処理を実装します。
3.  **情報処理モジュール (`src/processor/`)**: 抽出したデータを使って、要約作成 (`summary_prompt_template` を利用) やカテゴリ分類 (`category_prompt_template` を利用) を行う関数を実装します。
4.  **出力モジュール (`src/writer/`)**: 処理済みのデータを、設定 (`output_format`) に従ってExcelまたはGoogle Sheetsに出力する関数を実装します。
5.  **エラーハンドリング強化:** ネットワークエラー、API制限、予期せぬHTML構造など、より多様なエラーケースに対応できるようにします。
6.  **ロギング実装:** 各ステップで適切なログを出力するようにします (`logging` モジュールと `config.yaml` の設定を利用)。