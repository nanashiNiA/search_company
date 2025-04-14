import yaml
import os

# プロジェクトルートからの相対パスで設定ファイルのデフォルトパスを定義
DEFAULT_CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'config.yaml')

def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> dict | None:
    """
    指定されたパスからYAML設定ファイルを読み込み、辞書として返します。

    Args:
        config_path: 設定ファイルのパス。デフォルトはプロジェクトルートの config/config.yaml です。

    Returns:
        設定内容を格納した辞書。ファイルが見つからない場合や
        YAMLのパースに失敗した場合は None を返します。
    """
    try:
        # 絶対パスに変換してファイルを開く
        absolute_config_path = os.path.abspath(config_path)
        print(f"Attempting to load config from: {absolute_config_path}") # デバッグ用出力
        with open(absolute_config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        print("Config loaded successfully.") # デバッグ用出力
        return config
    except FileNotFoundError:
        print(f"Error: Config file not found at {absolute_config_path}")
        return None
    except yaml.YAMLError as e:
        print(f"Error: Failed to parse YAML file at {absolute_config_path}: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred while loading config: {e}")
        return None

if __name__ == '__main__':
    # このスクリプトが直接実行された場合に設定ファイルを読み込んで表示する
    print("Running config_loader.py as main script...")
    config_data = load_config()
    if config_data:
        print("\n--- Configuration Data ---")
        # 簡単に見るために一部だけ表示（例: target_sources）
        if 'target_sources' in config_data:
            print("Target Sources:")
            for source in config_data['target_sources']:
                print(f"  - Name: {source.get('name', 'N/A')}, URL: {source.get('url', 'N/A')}")
        else:
            print("target_sources not found in config.")
        # print("\nFull Config:")
        # import json
        # print(json.dumps(config_data, indent=2, ensure_ascii=False))
    else:
        print("Failed to load configuration.")
