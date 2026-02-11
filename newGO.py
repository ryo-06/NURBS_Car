import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
from geomdl import NURBS, knotvector
import json
import os
import ast
import re
import shutil

# === 設定 ===
# スプレッドシートID (URLの /d/ と /edit の間の文字列)
SPREADSHEET_ID = "1-mgxO9tqejwKehnbLS5B2JhCocdHH_xDWSZRLGKAE3A"
# 公開CSVダウンロード用URL
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv"

CSV_FILE = "car_data.csv"
OUTPUT_DIR = "output_images_attributes"

# === 0. 最新データをダウンロード (公開リンク方式) ===
def fetch_latest_data():
    print("--- [Step 0] スプレッドシートから最新データをダウンロード中... ---")
    try:
        # 認証不要で直接CSVとして読み込む
        df = pd.read_csv(CSV_URL, header=None)
        
        # 保存（BOM付きUTF-8）
        df.to_csv(CSV_FILE, index=False, header=False, encoding='utf-8-sig')
        print(f"✅ 最新データを取得し、{CSV_FILE} を更新しました！ (全 {len(df)} 行)")
        return True
    except Exception as e:
        print(f"❌ ダウンロードに失敗しました: {e}")
        print("ヒント: スプレッドシートの共有設定が「リンクを知っている全員」になっているか確認してください。")
        print("既存の car_data.csv を使用して処理を続行します。")
        return False

# === 1. ヘルパー関数群 ===
def find_keyword(text, keywords, default="unknown"):
    text_str = str(text).lower()
    for k in keywords:
        if k.lower() in text_str:
            return k
    return default

def get_age_label(text):
    match = re.search(r'(\d+s)', str(text))
    if match:
        return match.group(1)
    return "unknown"

def get_gender_label(text):
    text_str = str(text).upper()
    if "(M)" in text_str or "男性" in text_str: return "M"
    if "(F)" in text_str or "女性" in text_str: return "F"
    if "M" in text_str and "F" not in text_str: return "M"
    if "F" in text_str and "M" not in text_str: return "F"
    return "unknown"

# 定数定義
ADJECTIVES = ["cute", "cool", "sturdy", "fast", "luxury", "familiar", 
              "かわいい", "かっこいい", "頑丈そう", "速そう", "高級な", "親しみのある"]
ADJ_MAP = {
    "かわいい": "cute", "かっこいい": "cool", "頑丈そう": "sturdy",
    "速そう": "fast", "高級な": "luxury", "親しみのある": "familiar"
}
CAR_MODELS = {
    "軽自動車": { "tire": [(0.85, 0.1), (8.5, 0.1)] },
    "コンパクトカー": { "tire": [(0.85, -0.2), (8.8, -0.2)] },
    "SUV": { "tire": [(1.8, -0.5), (8.1, -0.5)] },
    "セダン": { "tire": [(1.6, 1.0), (8.2, 1.0)] },
    "ミニバン": { "tire": [(1.6, 0.2), (8.3, 0.2)] },
    "クーペ": { "tire": [(1.8, 1.0), (8.0, 1.0)] }
}

# === メイン処理開始 ===
if __name__ == "__main__":
    
    # 1. スプレッドシート更新を実行
    fetch_latest_data()
    
    # 保存先フォルダ作成
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 2. データの読み込みと修復
    print("\n--- [Step 1] ローカルデータの読み込みと解析 ---")
    try:
        df_raw = pd.read_csv(CSV_FILE, header=None, encoding='utf-8-sig', on_bad_lines='skip')
    except:
        print("UTF-8での読み込みに失敗、cp932で試行します...")
        df_raw = pd.read_csv(CSV_FILE, header=None, encoding='cp932', on_bad_lines='skip')

    cleaned_data = []

    for index, row in df_raw.iterrows():
        try:
            row_list = [str(x) for x in row.tolist()]
            
            # 制御点データの位置を探す（[[...]] を目印にする）
            ctrl_idx = -1
            for i, val in enumerate(row_list):
                if val.strip().startswith('[['):
                    ctrl_idx = i
                    break
            
            if ctrl_idx == -1:
                continue

            # 相対位置からデータを取得
            gender_raw = row_list[ctrl_idx - 3] if ctrl_idx >= 3 else ""
            age_raw    = row_list[ctrl_idx - 2] if ctrl_idx >= 2 else ""
            model_raw  = row_list[ctrl_idx - 1]
            ctrl_raw   = row_list[ctrl_idx]
            weight_raw = row_list[ctrl_idx + 1]
            adj_raw    = row_list[ctrl_idx + 3] if len(row_list) > ctrl_idx + 3 else "unknown"
            
            # 車種名の正規化
            model_clean = "UnknownModel"
            m = model_raw
            if "Light" in m or "軽" in m: model_clean = "軽自動車"
            elif "Compact" in m or "コンパクト" in m: model_clean = "コンパクトカー"
            elif "SUV" in m: model_clean = "SUV"
            elif "Sedan" in m or "セダン" in m: model_clean = "セダン"
            elif "Minivan" in m or "ミニバン" in m: model_clean = "ミニバン"
            elif "Coupe" in m or "coupe" in m or "クー" in m: model_clean = "クーペ"

            # 形容詞の抽出と英語変換
            found_adj = find_keyword(adj_raw, ADJECTIVES, default="unknown")
            if found_adj in ADJ_MAP:
                found_adj = ADJ_MAP[found_adj]
            
            cleaned_data.append({
                "gender": get_gender_label(gender_raw),
                "age": get_age_label(age_raw),
                "model": model_clean,
                "adjective": found_adj,
                "ctrlpts": ctrl_raw,
                "weights": weight_raw,
                "idx": index + 1  # 【修正点】スプレッドシートの行番号(1始まり)に合わせるため +1 する
            })

        except Exception:
            pass

    # 3. 画像生成（差分更新）
    print(f"--- [Step 2] 画像生成を開始します ({len(cleaned_data)}件) ---")
    
    count_gen = 0
    count_skipped = 0

    for row in cleaned_data:
        try:
            filename = f"{row['idx']:03d}_{row['model']}_{row['age']}_{row['gender']}_{row['adjective']}.png"
            
            # 既存チェック（サブフォルダ内 or ルート直下）
            target_path_in_subfolder = os.path.join(OUTPUT_DIR, row['adjective'], filename)
            target_path_direct = os.path.join(OUTPUT_DIR, filename)
            
            # すでに作成済みならスキップ
            if os.path.exists(target_path_in_subfolder) or os.path.exists(target_path_direct):
                count_skipped += 1
                continue

            # === 画像描画処理 ===
            model_name = row['model']
            try:
                ctrlpts = json.loads(row['ctrlpts'])
                weights = json.loads(row['weights'])
            except:
                ctrlpts = ast.literal_eval(row['ctrlpts'])
                weights = ast.literal_eval(row['weights'])

            curve = NURBS.Curve()
            curve.degree = 3
            curve.ctrlpts = ctrlpts
            curve.weights = weights
            curve.knotvector = knotvector.generate(curve.degree, len(ctrlpts))
            curve.delta = 0.01
            curve.evaluate()

            fig, ax = plt.subplots(figsize=(10, 7))
            ax.set_axis_off()

            tire_info = CAR_MODELS.get(model_name, {}).get("tire", [])
            for t in tire_info:
                ax.add_patch(Circle((t[0], t[1]), 0.9, color='black', zorder=1))

            poly_pts = curve.evalpts + [ctrlpts[-1], ctrlpts[0]]
            ax.add_patch(Polygon(poly_pts, closed=True, color='black', alpha=1.0))

            ax.set_aspect('equal')
            ax.set_xlim(-3, 13)
            ax.set_ylim(-3, 8)

            plt.savefig(target_path_direct, bbox_inches='tight', pad_inches=0)
            plt.close(fig)
            
            count_gen += 1
            if count_gen % 5 == 0:
                print(f"... 新規 {count_gen}枚 生成")

        except Exception as e:
            print(f"Error generating image for row {row['idx']}: {e}")

    print(f"✅ 生成完了: 新規 {count_gen}枚 (スキップ {count_skipped}枚)")

    # 4. フォルダ整理
    print(f"--- [Step 3] フォルダ整理を開始します ---")
    files = [f for f in os.listdir(OUTPUT_DIR) if f.lower().endswith('.png')]
    count_moved = 0
    
    for filename in files:
        try:
            name_without_ext = os.path.splitext(filename)[0]
            parts = name_without_ext.split('_')
            
            if len(parts) >= 2:
                adjective = parts[-1]
                # 形容詞ごとのフォルダを作成
                folder_path = os.path.join(OUTPUT_DIR, adjective)
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                
                src_path = os.path.join(OUTPUT_DIR, filename)
                dst_path = os.path.join(folder_path, filename)
                
                # 移動先に同名ファイルがあれば一度削除（上書き用）
                if os.path.exists(dst_path):
                    os.remove(dst_path)
                
                shutil.move(src_path, dst_path)
                count_moved += 1
        except Exception:
            pass

    print(f"✅ フォルダ整理完了: {count_moved}件移動")
    print(f"\n=== 全工程完了 ===")