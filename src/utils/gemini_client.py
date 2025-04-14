# src/utils/gemini_client.py
import google.generativeai as genai
import os
from dotenv import load_dotenv
import sys

def initialize_gemini(config: dict) -> genai.GenerativeModel | None:
    """
    環境変数からAPIキーを読み込み、設定に基づいてGeminiモデルを初期化します。

    Args:
        config: 設定ファイルから読み込んだ辞書。
                'gemini_model', 'safety_settings' を参照します。

    Returns:
        初期化されたGenerativeModelオブジェクト。
        APIキーが見つからない場合や初期化に失敗した場合は None を返します。
    """
    load_dotenv() # .envファイルから環境変数を読み込む
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables.")
        print("Please ensure it is set in your .env file or environment.")
        return None

    if not config:
        print("Error: Configuration dictionary is required for Gemini initialization.")
        return None

    model_name = config.get('gemini_model', 'gemini-1.5-flash') # デフォルトモデル指定
    safety_settings = config.get('safety_settings') # config.yaml から読み込む

    try:
        genai.configure(api_key=api_key)
        # safety_settings が config.yaml に存在する場合のみ適用
        if safety_settings:
            model = genai.GenerativeModel(model_name=model_name, safety_settings=safety_settings)
            print(f"Gemini model '{model_name}' initialized with custom safety settings.")
        else:
            model = genai.GenerativeModel(model_name=model_name)
            print(f"Gemini model '{model_name}' initialized with default safety settings.")
        return model
    except Exception as e:
        print(f"Error initializing Gemini model '{model_name}': {e}")
        return None

if __name__ == '__main__':
    # テスト用: config_loaderを使って設定を読み込み、初期化を試す
    print("Running gemini_client.py as main script...")

    # config_loader.py があるディレクトリをパスに追加
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.join(current_dir, '..', '..') # プロジェクトルート想定
    utils_dir = os.path.join(project_root, 'src', 'utils')
    config_path = os.path.join(project_root, 'config', 'config.yaml')

    if utils_dir not in sys.path:
        sys.path.append(utils_dir)

    try:
        from config_loader import load_config
        print(f"Loading config from: {config_path}")
        # 設定ファイルのトップレベルに Gemini 設定があると仮定して修正
        # app_config = load_config(config_path)
        app_config = load_config(config_path)

        if app_config:
            print("Config loaded successfully. Initializing Gemini...")
            # 設定ファイルのトップレベルにGemini関連設定があると仮定
            # gemini_model = initialize_gemini(app_config.get('gemini_api_settings', {})) # 設定の階層を仮定
            gemini_model = initialize_gemini(app_config) # トップレベルの設定を渡す
            if gemini_model:
                print("Gemini client initialized successfully.")
                # ここで簡単なAPIコールテストも可能 (例: model.count_tokens("test"))
            else:
                print("Failed to initialize Gemini client.")
        else:
            print("Failed to load config, cannot initialize Gemini.")

    except ImportError:
        print("Could not import load_config. Ensure config_loader.py is accessible.")
    except Exception as e:
        print(f"An error occurred during testing: {e}")