import requests
# from bs4 import BeautifulSoup # BeautifulSoupは不要になったのでコメントアウト or 削除
import sys
import os
import json # JSONパースのために追加
from dotenv import load_dotenv # .env読み込みのために追加
import google.generativeai as genai # Gemini APIのために追加

# src/utils ディレクトリをPythonパスに追加する代わりに相対インポートを使用
current_dir = os.path.dirname(os.path.abspath(__file__))
utils_dir = os.path.join(current_dir, '..', 'utils')
if utils_dir not in sys.path:
    sys.path.append(utils_dir)

try:
    # 絶対インポートに変更
    from src.utils.config_loader import load_config
    from src.utils.gemini_client import initialize_gemini
except ImportError as e:
    print(f"Error: Could not import required utility modules: {e}")
    # 実行場所によっては 'attempted relative import beyond top-level package' エラーが出る可能性あり
    # その場合は `python -m src.collector.website_scraper` のようにモジュールとして実行する必要がある
    print("Hint: Try running the script as a module, e.g., 'python -m src.collector.website_scraper'")
    sys.exit(1)


def fetch_html(url: str, timeout: int = 10) -> str | None:
    """
    指定されたURLからHTMLコンテンツを取得します。

    Args:
        url: 取得対象のURL。
        timeout: リクエストのタイムアウト時間 (秒)。

    Returns:
        取得したHTMLテキスト。取得に失敗した場合は None を返します。
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status() # HTTPエラーがあれば例外を発生させる (4xx or 5xx)
        response.encoding = response.apparent_encoding # 文字化け対策
        print(f"Successfully fetched HTML from {url} (Status: {response.status_code})")
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while fetching {url}: {e}")
        return None

# --- scrape_events 関数の実装 (Gemini API使用版) ---
def scrape_events(html_content: str, config: dict) -> list[dict]:
    """
    HTMLコンテンツをGemini APIに渡し、イベント情報を抽出します。

    Args:
        html_content: 解析対象のHTMLテキスト。
        config: アプリケーション設定全体を含む辞書。
                'html_extraction_prompt_template' を使用します。

    Returns:
        抽出されたイベント情報の辞書を要素とするリスト。
        抽出に失敗した場合は空のリストを返します。
    """
    if not html_content:
        print("Error: No HTML content provided to scrape.")
        return []
    if not config:
        print("Error: Config is required for scraping with Gemini.")
        return []

    # Geminiクライアントを初期化 (APIキーは initialize_gemini 内で .env から読み込まれる)
    gemini_model = initialize_gemini(config)
    if not gemini_model:
        print("Error: Failed to initialize Gemini model. Cannot scrape.")
        return []

    # HTML抽出用プロンプトを取得
    prompt_template = config.get('html_extraction_prompt_template')
    if not prompt_template:
        print("Error: 'html_extraction_prompt_template' not found in config.")
        return []

    # プロンプトにHTMLコンテンツを埋め込む
    prompt = prompt_template.format(html_content=html_content)

    # HTMLは長くなる可能性があるので、トークン数を確認・制限する方が安全だが、
    # まずはそのまま実行してみる
    print("\nSending HTML content to Gemini API for extraction...")
    try:
        # generation_config で出力形式を JSON に指定 (推奨)
        generation_config = genai.types.GenerationConfig(
            # candidate_count=1, # 候補は1つで良い
            # stop_sequences=['...'], # 必要なら停止シーケンス
            # max_output_tokens=8192, # 長いHTML用。必要に応じて調整
            # temperature=0.2, # 安定した出力を得るために低めに設定
            # top_p=...,
            # top_k=...,
            response_mime_type="application/json" # JSON出力を期待
        )
        response = gemini_model.generate_content(
            prompt,
            generation_config=generation_config
            )

        # レスポンスからJSONテキストを取得しパース
        # response.text にJSON文字列が含まれると期待
        if response.text:
            print("Received response from Gemini API.")
            # JSON文字列の最初と最後に```json ... ``` が付く場合があるので除去
            json_text = response.text.strip().removeprefix("```json").removesuffix("```").strip()
            events = json.loads(json_text)
            if isinstance(events, list):
                print(f"Successfully extracted {len(events)} events using Gemini.")
                return events
            else:
                print("Error: Gemini response was not a JSON list.")
                print(f"Raw response: {response.text[:500]}...") # デバッグ用に一部表示
                return []
        else:
            print("Error: Gemini API returned an empty response.")
            # 候補がない場合やブロックされた場合も考慮 (response.prompt_feedback)
            if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                 print(f"Prompt Feedback: {response.prompt_feedback}")
            return []

    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON response from Gemini: {e}")
        # エラー時のレスポンス内容も表示
        if 'response' in locals() and hasattr(response, 'text'):
             print(f"Raw response: {response.text[:500]}...")
        else:
             print("Could not retrieve raw response text.")
        return []
    except Exception as e:
        print(f"An error occurred during Gemini API call: {e}")
        # APIエラーの詳細を取得 (もしあれば)
        # 例: if hasattr(e, 'response'): print(e.response.text)
        return []


if __name__ == '__main__':
    print("Running website_scraper.py as main script...")
    # .envファイルをロード (APIキーなどを確実に読み込むためここでも呼ぶ)
    load_dotenv()
    # 設定ファイルを読み込む
    config = load_config() # デフォルトパスを使用

    if not config:
        print("Could not load configuration. Exiting.")
        sys.exit(1)

    example_source = None
    if 'target_sources' in config:
        for source in config['target_sources']:
            if source.get('name') == 'Example Tech News Site':
                example_source = source
                break

    if example_source and 'url' in example_source:
        target_url = example_source['url']
        print(f"\nAttempting to fetch HTML from: {target_url}")
        html = fetch_html(target_url)

        if html:
            print("\n--- Fetched HTML (first 500 chars) ---")
            print(html[:500] + "...")
            print("\n--- End of HTML snippet ---")

            # --- scrape_events 呼び出し部分 (Gemini版) ---
            print("\nAttempting to scrape events using Gemini API...")
            # scrape_events には設定全体を渡す
            events = scrape_events(html, config)
            if events:
                print(f"\nFound {len(events)} events:")
                # JSONできれいに表示
                print(json.dumps(events, indent=2, ensure_ascii=False))
            else:
                print("\nNo events extracted using Gemini API.")
            # --- ここまで ---
        else:
            print(f"\nFailed to fetch HTML from {target_url}.")
    else:
        print("\n'Example Tech News Site' or its URL not found in config/config.yaml.")
