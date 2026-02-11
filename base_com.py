import os
import math
import json
import ast
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import platform
import numpy as np
from matplotlib.patches import Polygon, Circle
from geomdl import NURBS, knotvector

# === 設定 ===
CSV_FILE = "car_data.csv"               # ベース形状のデータ元
INPUT_DIR = "output_images_attributes"  # 回答者の画像フォルダ
OUTPUT_DIR = "summary_final_base"       # 保存先
COLS = 3                                # 3列レイアウト

# === ベース形状の定義 (行番号) ===
# ユーザー指定: 137行目〜142行目
# プログラムは0始まりのインデックスなので、-1 して指定します
BASE_INFO = {
    "軽自動車": 136,      # 137行目
    "コンパクトカー": 137, # 138行目
    "SUV": 138,           # 139行目
    "セダン": 139,         # 140行目
    "ミニバン": 140,       # 141行目
    "クーペ": 141          # 142行目
}

# 除外するIDリスト（回答者データとして表示しないようにする）
# 137〜142行目に対応するID
EXCLUDE_IDS = [137, 138, 139, 140, 141, 142]

# === タイヤなどの定義（描画用） ===
CAR_MODELS_INFO = {
    "軽自動車": { "tire": [(0.85, 0.1), (8.5, 0.1)] },
    "コンパクトカー": { "tire": [(0.85, -0.2), (8.8, -0.2)] },
    "SUV": { "tire": [(1.8, -0.5), (8.1, -0.5)] },
    "セダン": { "tire": [(1.6, 1.0), (8.2, 1.0)] },
    "ミニバン": { "tire": [(1.6, 0.2), (8.3, 0.2)] },
    "クーペ": { "tire": [(1.8, 1.0), (8.0, 1.0)] }
}

# === 日本語フォント設定 ===
system_name = platform.system()
if system_name == "Windows":
    plt.rcParams['font.family'] = 'MS Gothic'
elif system_name == "Darwin":
    plt.rcParams['font.family'] = 'AppleGothic'

# === 関数: ベース画像の生成 ===
def generate_base_image(row, model_name, save_path):
    try:
        # データのパース
        ctrl_raw = row.iloc[5]
        weight_raw = row.iloc[6]
        try:
            ctrlpts = json.loads(ctrl_raw)
            weights = json.loads(weight_raw)
        except:
            ctrlpts = ast.literal_eval(ctrl_raw)
            weights = ast.literal_eval(weight_raw)

        # NURBS計算
        curve = NURBS.Curve()
        curve.degree = 3
        curve.ctrlpts = ctrlpts
        curve.weights = weights
        curve.knotvector = knotvector.generate(curve.degree, len(ctrlpts))
        curve.delta = 0.01
        curve.evaluate()

        # 描画
        fig, ax = plt.subplots(figsize=(10, 7))
        ax.set_axis_off()

        # タイヤ
        tire_info = CAR_MODELS_INFO.get(model_name, {}).get("tire", [])
        for t in tire_info:
            ax.add_patch(Circle((t[0], t[1]), 0.9, color='black', zorder=1))

        # シルエット
        poly_pts = curve.evalpts + [ctrlpts[-1], ctrlpts[0]]
        ax.add_patch(Polygon(poly_pts, closed=True, color='black', alpha=1.0))

        ax.set_aspect('equal')
        ax.set_xlim(-3, 13)
        ax.set_ylim(-3, 8)

        plt.savefig(save_path, bbox_inches='tight', pad_inches=0)
        plt.close(fig)
        return True
    except Exception as e:
        print(f"  ❌ ベース生成エラー ({model_name}): {e}")
        return False

# === メイン処理 ===
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)
    
# 一時フォルダ（ベース画像用）
TEMP_BASE_DIR = "_temp_base_images"
if not os.path.exists(TEMP_BASE_DIR):
    os.makedirs(TEMP_BASE_DIR)

print("--- 1. CSVからベース形状を生成します ---")
try:
    df = pd.read_csv(CSV_FILE, header=None, encoding='utf-8-sig', on_bad_lines='skip')
except:
    df = pd.read_csv(CSV_FILE, header=None, encoding='cp932', on_bad_lines='skip')

# ベース画像を生成して保存
base_image_paths = {} # {"SUV": "path/to/suv_base.png"}

for model, row_idx in BASE_INFO.items():
    if row_idx < len(df):
        print(f"  ベース生成中: {model} (Row {row_idx + 1})")
        row = df.iloc[row_idx]
        save_path = os.path.join(TEMP_BASE_DIR, f"{model}_base.png")
        if generate_base_image(row, model, save_path):
            base_image_paths[model] = save_path
    else:
        print(f"  ⚠️ 警告: {model} のデータ行 ({row_idx+1}) がCSVに存在しません")

print("\n--- 2. 回答者データを読み込みます ---")
all_images = []
for root, dirs, files in os.walk(INPUT_DIR):
    for file in files:
        if file.lower().endswith(".png"):
            # ファイル名からIDを取得して、ベース用のデータ(137-142)なら除外する
            try:
                file_id = int(file.split('_')[0])
                if file_id in EXCLUDE_IDS:
                    continue 
            except:
                pass
            all_images.append(os.path.join(root, file))

if not all_images:
    print("回答画像が見つかりませんでした。")
    exit()

# データを分類
data = {} # data[adj][model] = [list of images]
for img_path in all_images:
    filename = os.path.basename(img_path)
    name_without_ext = os.path.splitext(filename)[0]
    parts = name_without_ext.split('_')
    if len(parts) >= 5:
        model = parts[1]
        adj = parts[-1]
        if adj not in data: data[adj] = {}
        if model not in data[adj]: data[adj][model] = []
        data[adj][model].append(img_path)

print("\n--- 3. まとめ画像の作成を開始します (ベース付き) ---")
count_created = 0

for adj, models in data.items():
    for model, images in models.items():
        
        # ID順にソート
        images.sort(key=lambda x: os.path.basename(x))
        num_images = len(images)
        
        # 行数計算: ベース行(1) + データ行
        data_rows = math.ceil(num_images / COLS)
        total_rows = 1 + data_rows
        
        print(f"作成中: {adj} - {model} ({num_images}枚 + ベース)")

        fig_width = 15
        fig_height = total_rows * 3.5
        fig, axes = plt.subplots(total_rows, COLS, figsize=(fig_width, fig_height))
        
        if total_rows == 1 and COLS == 1: axes = [axes]
        else: axes = axes.flatten()

        fig.suptitle(f"Category: {adj} - {model}", fontsize=20, y=0.99)

        base_center_index = COLS // 2 # 3列なら1番目(真ん中)

        for i, ax in enumerate(axes):
            # --- 1行目: ベース形状 ---
            if i < COLS:
                if i == base_center_index:
                    # ベース画像を表示
                    if model in base_image_paths:
                        try:
                            b_img = mpimg.imread(base_image_paths[model])
                            ax.imshow(b_img)
                            ax.set_title("Base Shape", fontsize=14, color='blue', fontweight='bold')
                            ax.axis('off')
                        except:
                            ax.text(0.5, 0.5, "Base Load Error", ha='center', va='center')
                            ax.axis('off')
                    else:
                        ax.text(0.5, 0.5, "No Base Data", ha='center', va='center', color='gray')
                        ax.axis('off')
                else:
                    ax.axis('off')
            
            # --- 2行目以降: 回答データ ---
            else:
                img_idx = i - COLS
                if img_idx < num_images:
                    img_path = images[img_idx]
                    try:
                        img = mpimg.imread(img_path)
                        ax.imshow(img)
                        fname = os.path.basename(img_path)
                        parts = os.path.splitext(fname)[0].split('_')
                        if len(parts) >= 5:
                            # ID(年代/性別)
                            label = f"ID:{parts[0]}\n({parts[2]} / {parts[3]})"
                        else:
                            label = fname
                        ax.set_title(label, fontsize=12)
                        ax.axis('off')
                    except:
                        ax.axis('off')
                else:
                    ax.axis('off')

        plt.tight_layout(rect=[0, 0, 1, 0.97])
        save_path = os.path.join(OUTPUT_DIR, f"{adj}_{model}.png")
        plt.savefig(save_path, bbox_inches='tight')
        plt.close(fig)
        count_created += 1

print(f"\n✅ すべて完了しました！")
print(f"作成数: {count_created} 枚")
print(f"保存先: {os.path.abspath(OUTPUT_DIR)}")