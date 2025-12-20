# app.py
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
from geomdl import NURBS, knotvector
import matplotlib.image as mpimg
import json

st.set_page_config(page_title="NURBS Car Editor", layout="wide")
st.title("🚗 NURBS Car Silhouette Editor (Streamlit)")
st.markdown("左のサイドバーで車種を選び、制御点と重みを調整してください。")

# === 元の CAR_MODELS をそのまま流用（あなたが最初に送ってくれたもの） ===
CAR_MODELS = {
    "Kei car": {
        "ctrlpts": [[-0.5, 0], [-0.5, 2.0], [-0.2, 2.65], [1.5, 3.0], [2.6, 4.75], [3.5, 5.1], [6.5, 5.1], [9.2, 5.1], [9.8, 4.5], [9.88, 1.75], [10.1, 1.58], [10.0, 0]],
        "weights": [1.0, 2.0, 2.0, 5.0, 5.0, 2.0, 1.0, 7.0, 12.5, 1.0, 1.0, 1.0],
        "tire_coords": [(0.85, 0.1), (8.5, 0.1)],
        "ground_line": [-0.5, 10.0, 0.0],
        "bg_image": "kei_car.jpg"
    },
    "Compact": {
        "ctrlpts": [[-0.6, -0.2], [-0.8, 2.0], [0.6, 3.2], [1.9, 3.4], [3.8, 4.6], [6.6, 4.9], [10.0, 4.6], [9.8, 3.9], [10.3, 2.0], [10.6, 1.2], [10.3, -0.2]],
        "weights": [1.0, 6.0, 3.0, 5.0, 5.0, 6.0, 5.0, 3.0, 2.0, 1.0, 1.0],
        "tire_coords": [(0.85, -0.2), (8.8, -0.2)],
        "ground_line": [-0.6, 10.3, -0.2],
        "bg_image": "compact_car.jpg"
    },
    "SUV": {
        "ctrlpts": [[-0.1, -0.5], [-0.15, 1.8], [0.8, 2.3], [2.8, 2.7], [4.4, 4.2], [7.0, 4.45], [9.7, 4.0], [9.35, 3.4], [10.0, 2.4], [10.0, 0.2], [9.8, -0.6], [9.2, -0.5]],
        "weights": [1.0, 5.0, 1.8, 4.4, 10.0, 6.0, 15.0, 18.5, 28.8, 28.8, 22.5, 10.0, 1.0],
        "tire_coords": [(1.8, -0.5), (8.1, -0.5)],
        "ground_line": [-0.1, 9.2, -0.5],
        "bg_image": "SUV.jpg"
    },
    "Sedan": {
        "ctrlpts": [[-0.4, 0.6], [-0.2, 2.1], [1.2, 2.8], [2.4, 2.9], [4.0, 4.0], [7.2, 4.0], [9.0, 3.1], [10.2, 3.0], [10.2, 2.2], [10.35, 1.6],[10.2, 0.6]],
        "weights": [1.0, 14.6, 20.2, 91.8, 100.0, 100.0, 100.0, 100.0, 14.3, 15.0, 1.0],
        "tire_coords": [(1.6, 1.0), (8.2, 1.0)],
        "ground_line": [-0.4, 10.2, 0.6],
        "bg_image": "sedan2.jpg"
    },
    "Minivan": {
        "ctrlpts": [[-0.5, 0], [-0.4, 2.0], [0, 2.5], [1.4, 2.9], [3.7, 5.0], [6.5, 5.0], [10.1, 5.0], [9.8, 4.6], [10.2,2.9], [10.1, 1.5], [10.1, 0]],
        "weights": [1.0, 9.1, 15.1, 30.2, 52.9, 15.1, 56.2, 17.8, 12.0, 11.8, 1.0],
        "tire_coords": [(1.6, 0.2), (8.3, 0.2)],
        "ground_line": [-0.5, 10.1, 0],
        "bg_image": "Minivan.jpg"
    },
    "Coupe": {
        "ctrlpts": [[0, 0.8], [0.1, 2.25], [0.8, 2.7], [3.4, 3.2], [4.6, 3.85], [6.0, 4.0], [7.2, 3.7], [8.4, 3.5], [9.4, 3.0], [9.8, 2.0], [9.5, 0.8]],
        "weights": [1.0, 9.1, 15.1, 30.2, 52.9, 30.0, 56.2, 20.0, 17.8, 11.8, 1.0],
        "tire_coords": [(1.8, 1.0), (8.0, 1.0)],
        "ground_line": [0, 9.4, 0.8],
        "bg_image": "coope.jpg"
    }
}

# === サイドバー：車種選択 ===
selected_model = st.sidebar.selectbox("車種を選択", list(CAR_MODELS.keys()))
model_data = CAR_MODELS[selected_model]

# 制御点と重み（元データ）
initial_ctrlpts = model_data["ctrlpts"]
initial_weights = model_data.get("weights", [])

# sanity: 重みと制御点数が合わない場合は調整（trim / pad）
if len(initial_weights) < len(initial_ctrlpts):
    if len(initial_weights) == 0:
        # default all 1.0
        initial_weights = [1.0] * len(initial_ctrlpts)
    else:
        initial_weights = initial_weights + [initial_weights[-1]] * (len(initial_ctrlpts) - len(initial_weights))
elif len(initial_weights) > len(initial_ctrlpts):
    initial_weights = initial_weights[:len(initial_ctrlpts)]

st.sidebar.markdown("### ⚙️ 制御点（X,Y）と重み（W）の調整")
alpha = st.sidebar.slider("塗りつぶしの不透明度", 0.0, 1.0, 0.3, 0.05)

# =========== スライダー（キーを用いて session state を保持） ===========
new_ctrlpts = []
new_weights = []

for i, (pt, w) in enumerate(zip(initial_ctrlpts, initial_weights)):
    x_key = f"{selected_model}_x_{i}"
    y_key = f"{selected_model}_y_{i}"
    w_key = f"{selected_model}_w_{i}"

    # 初期値設定（session_state にまだないとき）
    if x_key not in st.session_state:
        st.session_state[x_key] = float(pt[0])
    if y_key not in st.session_state:
        st.session_state[y_key] = float(pt[1])
    if w_key not in st.session_state:
        st.session_state[w_key] = float(w)

    # スライダー（float に統一）
    x = st.sidebar.slider(f"Point {i} X", float(pt[0] - 1.0), float(pt[0] + 1.0), st.session_state[x_key], 0.1, key=x_key)
    y = st.sidebar.slider(f"Point {i} Y", float(pt[1] - 1.0), float(pt[1] + 1.0), st.session_state[y_key], 0.1, key=y_key)
    ww = st.sidebar.slider(f"Weight {i}", 0.1, 150.0, st.session_state[w_key], 0.1, key=w_key)

    new_ctrlpts.append([float(x), float(y)])
    new_weights.append(float(ww))

# リセットボタン（押すとそのモデルの session_state を初期値で上書きして再実行）
if st.sidebar.button("初期値にリセット"):
    reset_data = {}
    for i, (pt, w) in enumerate(zip(initial_ctrlpts, initial_weights)):
        reset_data[f"{selected_model}_x_{i}"] = float(pt[0])
        reset_data[f"{selected_model}_y_{i}"] = float(pt[1])
        reset_data[f"{selected_model}_w_{i}"] = float(w)
    # セッション全体をクリアして再設定（安全）
    for key, value in reset_data.items():
        st.session_state[key] = value
    st.rerun()


# =========== NURBS 曲線生成 ===========
curve = NURBS.Curve()
curve.degree = 3
curve.ctrlpts = new_ctrlpts
curve.weights = new_weights
curve.knotvector = knotvector.generate(curve.degree, len(new_ctrlpts))
curve.delta = 0.01
curve.evaluate()

# =========== 描画 ===========
fig, ax = plt.subplots(figsize=(10, 7))

# 背景画像（あれば透かして表示）
try:
    bg = mpimg.imread(model_data.get("bg_image", ""))
    ax.imshow(bg, extent=[-1, 11, -1.5, 6], aspect='auto', alpha=0.2)
except Exception:
    pass  # 画像が無ければ無視

# タイヤ
for t in model_data.get("tire_coords", []):
    ax.add_patch(Circle((t[0], t[1]), 0.9, color='black', zorder=1))

# 地面ライン
if "ground_line" in model_data:
    x0, x1, y_ground = model_data["ground_line"]
    ax.plot([x0, x1], [y_ground, y_ground], '-', color='black', linewidth=1)

# NURBS 曲線
curve_pts = np.array(curve.evalpts)
ax.plot(curve_pts[:, 0], curve_pts[:, 1], color='blue', linewidth=2, label='NURBS Curve')

# 制御点とポリライン
ctrl_np = np.array(new_ctrlpts)
ax.plot(ctrl_np[:, 0], ctrl_np[:, 1], '--', color='tab:red', marker='o', label='Control Points')

# 塗りつぶし（元の Tkinter と同じロジック：曲線の点列 + 最後の制御点 + 最初の制御点）
poly_pts = curve.evalpts + [new_ctrlpts[-1], new_ctrlpts[0]]
ax.add_patch(Polygon(poly_pts, closed=True, color='black', alpha=alpha))

ax.set_xlim(-3, 13)
ax.set_ylim(-3, 8)
ax.set_aspect('equal')
ax.grid(True)
ax.legend()

st.pyplot(fig)

# JSON ダウンロード（任意）
payload = {
    "model": selected_model,
    "ctrlpts": new_ctrlpts,
    "weights": new_weights
}
st.download_button("現在の形状をJSONでダウンロード", json.dumps(payload, ensure_ascii=False, indent=2), file_name=f"{selected_model}_shape.json", mime="application/json")





