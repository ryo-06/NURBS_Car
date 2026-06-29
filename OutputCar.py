import os
import json
import gspread
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
from geomdl import NURBS, knotvector
from google.oauth2.service_account import Credentials

# --- 1. Google Sheets 認証設定 ---
# ローカルで実行するため、GCPで取得したサービスアカウントのJSONファイルを指定します。
CREDENTIALS_FILE = "credentials.json" 
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1-mgxO9tqejwKehnbLS5B2JhCocdHH_xDWSZRLGKAE3A/edit?usp=sharing"

# --- 2. 車種の基本データ（タイヤ描画用などに使用） ---
CAR_MODELS = {
    "軽自動車(Kei_car)": {"tire_coords": [(0.85, 0.1), (8.5, 0.1)], "tire_radius": 0.85},
    "コンパクトカー(Compact car)": {"tire_coords": [(1.3, 0.0), (10.0, 0.0)], "tire_radius": 1.05},
    "SUV": {"tire_coords": [(2.0, 0.0), (10.5, 0.0)], "tire_radius": 1.25},
    "セダン(Sedan)": {"tire_coords": [(2.1, 1.0), (10.4, 1.0)], "tire_radius": 1.05},
    "ミニバン(Minivan)": {"tire_coords": [(1.9, 0.2), (10.4, 0.2)], "tire_radius": 1.1},
    "クーペ(Coupe)": {"tire_coords": [(2.2, 1.0), (10.1, 1.0)], "tire_radius": 1.15}
}

def main():
    # スプレッドシートへの接続
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
    client = gspread.authorize(creds)

    print("スプレッドシートのデータを取得中...")
    sheet = client.open_by_url(SPREADSHEET_URL).worksheet("全体")
    records = sheet.get_all_values()

    # ヘッダー行をスキップ（1行目がヘッダーであると仮定）
    if len(records) > 0 and "かっこいい" not in records[0] and "かわいい" not in records[0]:
        records = records[1:]

    print(f"合計 {len(records)} 件のデータを処理します。")

    # 画像の出力先ルートフォルダ
    output_base_dir = "output_car_images"
    os.makedirs(output_base_dir, exist_ok=True)

    for i, row in enumerate(records):
        try:
            # データのパース (保存時の列順に基づく)
            # 順番: [言葉, 名前, 性別, 年代, 車種, 座標, 重み, 重み倍率, 透明度, 時間]
            adjective = row[0]
            name = row[1]
            model = row[4]
            ctrlpts = json.loads(row[5])
            weights = json.loads(row[6])
            
            # タイムスタンプをファイル名に使用できるように「:」を「-」に置換
            timestamp = row[9].replace(":", "-").replace(" ", "_")
            
            # --- 保存先ディレクトリの作成 (車種 > 言葉) ---
            # 例: output_car_images/SUV/かっこいい(cool)
            save_dir = os.path.join(output_base_dir, model, adjective)
            os.makedirs(save_dir, exist_ok=True)
            
            file_name = f"{timestamp}_{name}.png"
            file_path = os.path.join(save_dir, file_name)

            # --- NURBS曲線の生成 ---
            curve = NURBS.Curve()
            curve.degree = 3
            curve.ctrlpts = ctrlpts
            curve.weights = weights
            curve.knotvector = knotvector.generate(curve.degree, len(ctrlpts))
            curve.delta = 0.01
            curve.evaluate()

            # --- 描画 ---
            fig, ax = plt.subplots(figsize=(10, 7))
            
            # タイヤの描画
            model_data = CAR_MODELS.get(model, {})
            tire_radius = model_data.get("tire_radius", 0.9)
            for t in model_data.get("tire_coords", []):
                ax.add_patch(Circle((t[0], t[1]), tire_radius, color='black', zorder=1))

            # シルエット（ポリゴン）の描画
            # 透過度はアンケート時と同様に真っ黒（alpha=1.0）にしてシルエットを見やすくします
            poly_pts = curve.evalpts + [ctrlpts[-1], ctrlpts[0]]
            ax.add_patch(Polygon(poly_pts, closed=True, color='black', alpha=1.0))

            # グラフのスケール設定（Streamlitアプリと統一）
            ax.set_xlim(-3, 15)
            ax.set_ylim(-3, 8)
            ax.set_aspect('equal')
            ax.axis('off') # 枠線や目盛りを消す場合は有効化

            # 画像として保存し、メモリ解放のために閉じる
            plt.savefig(file_path, bbox_inches='tight', pad_inches=0.1)
            plt.close(fig)

            print(f"[{i+1}/{len(records)}] 保存完了: {file_path}")

        except Exception as e:
            print(f"行 {i+1} の処理中にエラーが発生しました（データスキップ）: {e}")

    print("すべての画像の出力が完了しました！")

if __name__ == "__main__":
    main()