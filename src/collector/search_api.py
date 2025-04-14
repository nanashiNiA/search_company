import os
import json
import sys
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# 必要なユーティリティモジュールのインポート
current_dir = os.path.dirname(os.path.abspath(__file__))
utils_dir = os.path.join(current_dir, '..', 'utils')
if utils_dir not in sys.path:
    sys.path.append(utils_dir)

try:
    from src.utils.config_loader import load_config
    from src.utils.gemini_client import initialize_gemini
except ImportError as e:
    print(f"Error: Could not import required utility modules: {e}")
    print("Hint: Try running the script as a module, e.g., 'python -m src.collector.search_api'")
    sys.exit(1)

def search_query(query: str, config: dict) -> dict:
    """
    検索APIを使ってクエリを実行し結果を取得します。

    Args:
        query: 検索クエリ文字列。
        config: 設定辞書（search_api セクションを参照）。

    Returns:
        検索結果を含む辞書。エラー時は空の辞書または説明付きの辞書を返します。
    """
    try:
        api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
        search_engine_id = os.getenv("SEARCH_ENGINE_ID")

        if not api_key or not search_engine_id:
            print("Error: GOOGLE_SEARCH_API_KEY or SEARCH_ENGINE_ID not found in environment variables.")
            return {"error": "Missing API credentials"}

        # 検索設定の取得
        search_config = config.get("search_api", {})
        results_count = search_config.get("results_count", 5)

        # 検索サービスの初期化
        service = build("customsearch", "v1", developerKey=api_key)

        # 検索実行
        print(f"\nExecuting search query: '{query}'")
        search_results = service.cse().list(
            q=query,
            cx=search_engine_id,
            num=results_count
        ).execute()

        print(f"Search completed. Found {len(search_results.get('items', []))} results.")
        return search_results

    except HttpError as e:
        print(f"HTTP error occurred: {e}")
        return {"error": f"HTTP error: {e.status_code}"}
    except Exception as e:
        print(f"An error occurred during search: {e}")
        return {"error": str(e)}

def extract_events_from_search(search_results: dict, config: dict) -> list:
    """
    検索結果からGemini APIを使ってイベント情報を抽出します。

    Args:
        search_results: search_query() から返された検索結果辞書。
        config: 設定辞書（search_extraction_prompt_template を参照）。

    Returns:
        抽出されたイベント情報の辞書リスト。エラー時は空のリストを返します。
    """
    # エラーチェック
    if "error" in search_results:
        print(f"Cannot extract events from search results due to previous error: {search_results['error']}")
        return []

    items = search_results.get("items", [])
    if not items:
        print("No search results found to extract events from.")
        return []

    # Geminiクライアントの初期化
    gemini = initialize_gemini(config)
    if not gemini:
        print("Error: Failed to initialize Gemini model. Cannot extract events.")
        return []

    # 検索結果を整形（分析しやすいフォーマットに）
    formatted_results = []
    for item in items:
        formatted_results.append({
            "title": item.get("title", ""),
            "link": item.get("link", ""),
            "snippet": item.get("snippet", ""),
            "displayLink": item.get("displayLink", "")
        })

    # 検索結果をJSON文字列に変換
    search_results_json = json.dumps(formatted_results, ensure_ascii=False, indent=2)

    # プロンプトテンプレートを取得して検索結果を埋め込む
    prompt_template = config.get("search_extraction_prompt_template")
    if not prompt_template:
        print("Error: 'search_extraction_prompt_template' not found in config.")
        return []

    prompt = prompt_template.replace("{search_results}", search_results_json)

    # Gemini APIに送信
    print("\nSending search results to Gemini API for event extraction...")
    try:
        # JSON出力を指定
        generation_config = {
            "response_mime_type": "application/json"  # JSON出力を期待
        }

        response = gemini.generate_content(
            prompt,
            generation_config=generation_config
        )

        result_text = response.text
        print("Received response from Gemini API.")

        # JSON文字列の最初と最後に```json ... ``` が付く場合があるので除去
        json_text = result_text.strip().removeprefix("```json").removesuffix("```").strip()

        # 結果をJSONとしてパース
        events = json.loads(json_text)
        if isinstance(events, list):
            print(f"Successfully extracted {len(events)} events from search results.")
            return events
        else:
            print("Error: Gemini response was not a JSON list.")
            print(f"Raw response: {result_text[:500]}...") # デバッグ用に一部表示
            return []

    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON response from Gemini: {e}")
        if 'response' in locals() and hasattr(response, 'text'):
            print(f"Raw response: {response.text[:500]}...")
        return []
    except Exception as e:
        print(f"An error occurred during Gemini API call: {e}")
        return []

def main():
    """メイン関数"""
    print("Running search_api.py as main script...")
    # .envファイルをロード（APIキーを読み込むため）
    load_dotenv()

    # 設定ファイルを読み込む
    config = load_config()
    if not config:
        print("Could not load configuration. Exiting.")
        sys.exit(1)

    # 検索APIソースを探す
    search_sources = []
    if 'target_sources' in config:
        for source in config['target_sources']:
            if source.get('type') == 'search_api' and 'query' in source:
                search_sources.append(source)

    if not search_sources:
        print("No search API sources found in config.")
        print("Please add a 'search_api' type source with a 'query' to your config.yaml.")
        sys.exit(1)

    # 各検索ソースで処理を実行
    for source in search_sources:
        print(f"\nProcessing search source: {source.get('name', 'Unknown')}")
        query = source['query']

        # 検索実行
        search_results = search_query(query, config)

        # 検索結果からイベント情報を抽出
        events = extract_events_from_search(search_results, config)

        # 結果を表示
        if events:
            print(f"\nExtracting events for '{source.get('name', 'Unknown')}' completed.")
            print(json.dumps(events, ensure_ascii=False, indent=2))
        else:
            print(f"\nNo events extracted for '{source.get('name', 'Unknown')}'.")

    print("\nSearch API processing completed.")

if __name__ == "__main__":
    main()