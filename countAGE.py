import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# ==========================================
# 設定エリア
# ==========================================
# 手元にある認証用JSONファイルの名前を指定してください
JSON_KEY_FILE = 'credentials.json' 

# 集計したいスプレッドシートのURL
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1-mgxO9tqejwKehnbLS5B2JhCocdHH_xDWSZRLGKAE3A/edit?usp=sharing"
# ==========================================

def main():
    try:
        # 1. Google Sheets APIへの認証
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_file(JSON_KEY_FILE, scopes=scope)
        client = gspread.authorize(creds)

        # 2. スプレッドシートを開く
        print("スプレッドシートに接続中...")
        spreadsheet = client.open_by_url(SPREADSHEET_URL)
        worksheet = spreadsheet.sheet1
        
        # 3. 全データを取得
        data = worksheet.get_all_values()
        
        # データがない場合のチェック
        if not data:
            print("データが見つかりませんでした。")
            return

        # 4. DataFrameに変換
        # あなたの保存コードの並び順に合わせてカラム名を定義します
        # row = [timestamp, name, gender, age_group, model, ctrlpts_str, weights_str, alpha_value, adjective]
        cols = ["timestamp", "name", "gender", "age_group", "model", "ctrlpts", "weights", "alpha", "adjective"]
        
        # スプレッドシートのデータ数とカラム数が合わない場合の対策（足りない列を埋めるなど）も含めDF化
        df = pd.DataFrame(data)
        
        # 列数が足りているか確認してリネーム
        if len(df.columns) >= 4:
            # 4列目(index 3)がage_group
            df.rename(columns={3: 'age_group'}, inplace=True)
        else:
            print("エラー：データの列数が不足しています。")
            return

        # もし1行目がヘッダー（見出し）として保存されている場合は、次の行のコメントアウトを外してスキップしてください
        # df = df[1:] 

        # 5. 集計 (age_group列をカウント)
        # 空白のデータは除外
        df_clean = df[df['age_group'] != '']
        age_counts = df_clean['age_group'].value_counts()

        # 6. 結果の表示
        print("\n" + "="*20)
        print("   年代別 集計結果")
        print("="*20)
        
        for age, count in age_counts.items():
            print(f"{age}：{count}人")
            
        print("="*20)
        print(f"合計：{age_counts.sum()}人")

    except FileNotFoundError:
        print(f"エラー：'{JSON_KEY_FILE}' が見つかりません。パスを確認してください。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()