import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
from geomdl import NURBS, knotvector
import matplotlib.image as mpimg
import json
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials
import os

# --- Google Sheets 認証設定 (元のコードを維持) ---
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

try:
    if "credentials_json" in st.secrets:
        credentials_info = dict(st.secrets["credentials_json"])
        if "private_key" in credentials_info:
            credentials_info["private_key"] = credentials_info["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(credentials_info, scopes=scope)
        client = gspread.authorize(creds)
    else:
        client = None
except Exception as e:
    client = None

st.set_page_config(page_title="NURBS Car Editor", layout="wide")
st.title(" NURBS Car Silhouette Editor ")

st.markdown("""
本アンケートは、**早稲田大学の研究プロジェクト**の一環として実施しているものです。  
「**言葉によるエンジニアリング**」というテーマのもと、**言葉から理想的な自動車の形状を導出すること**を目的としています。  
本アンケートでは、参加者の皆さまの操作結果をもとに、**言葉と形状の関係性**を分析いたします。  
本研究以外の目的で個人情報を使用することはありません。
本研究の内容にご理解・ご同意いただける方のみ、ご回答をお願いいたします。

実施者：早稲田大学 情報生産システム研究科 荒川研究室 尾﨑椋太  

This survey is being conducted as part of a research project at Waseda University.
Under the theme of "Engineering starts with words," the project aims to derive the ideal car shape from words.
In this survey, we will analyze the relationship between words and shapes based on the participants' actions.
Your personal information will not be used for any purpose other than this research.
Please respond only if you understand and agree to the contents of this research.

Implemented by: Ryota Ozaki, Arakawa Laboratory, Graduate School of Information, Production and Systems, Waseda University

---

⚠️ 操作はPCでのご利用を推奨しています。 
    We recommend using a PC for this operation.

---

## 操作方法 (Updated)
1. まず、ページ上部の **回答者情報** を入力し、これから作成する **車の印象（言葉）** を選択してください。
2. 左のサイドバーで **車種を選択** してください。それぞれの車種は異なる実寸比率で表示されます。  
3. 点の順番は左下から順に0から始まります。
4. 車の先端を丸くしたり尖らせたりしたい場合は、**重み** を調整してください。  
5. 各 **位置X** スライダーで点を左右に、**位置Y** スライダーで上下に動かすことができます。
   **(※始点と終点の高さ(Y)は固定されています。)**
6. 可动域は、車種の実際の寸法（全長、車高）に合わせて自動的に調整されます。Kei Carの可動域は狭く、Minivanの可動域は広くなります。
7. 基本的には 点の**重み**を好みに調整 し、必要に応じて位置を微調整すると自然な形になります。  
8. 調整後、**透明度スライダー** で車体を黒くし、形状を確認してください。異なる車種を比較できます。
9. **複数の車種を回答する場合**は、1つの車種が終わったら 「保存」ボタンを押し、ページを更新してください。  
10. 回答は何度でも行うことができます。

---
""")

# 自動翻訳を無効化 (元のコードを維持)
st.markdown(
    """
    <meta name="google" content="notranslate">
    <style>
    body { -webkit-user-select: text; }
    div[data-testid="column"] button {
        width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ユーザー入力欄
st.markdown("### 回回答者情報(Respondent Information)")

col_info1, col_info2, col_info3 = st.columns(3)
with col_info1:
    name = st.text_input("ニックネーム(NickName)")
with col_info2:
    gender = st.radio("性別(gender)", ["男性(M)", "女性(F)"], horizontal=True)
with col_info3:
    age_group = st.selectbox("年代", ["10代未満(Under 10s)", "10代(10s)", "20代(20s)", "30代(30s)", "40代(40s)", "50代(50s)", "60代(60s)", "70代以上(70s and older)"])

st.markdown("### これから作る自動車の印象を決めてください(Please Decide the impression of the car you are going to make.)")
adjective = st.selectbox(
    "車を一言で表すと？(How would you describe the car in one word?)",
    ["かわいい(cute)", "かっこいい(cool)", "頑丈そう(sturdy)", "速そう(fast)", "高級な(luxury)", "親しみのある(familiar)"]
)

st.markdown("---")

# --- 車種データの統合と寸法の調整 
CAR_MODELS = {
    "Kei Car": {
        "ctrlpts": [[-0.5, 0.0], [-0.5, 1.8], [0.0, 2.8], [1.5, 3.8], [2.5, 4.9], [7.0, 5.0], [9.5, 4.8], [10.0, 2.0], [10.0, 0.0]],
        "weights": [0.1, 0.2, 0.9, 2.8, 6.6, 0.7, 1.3, 0.9, 0.1],
        "tire_coords": [(1.1, 0.0), (8.9, 0.0)],
        "tire_radius": 1.0,
        "ground_y": 0.0,
        "bg_image": "kei.jpg",
        "image_extent": [-1, 11, -1.5, 6],
        "x_range": 0.5, # 車種ごとの全長に基づく可動域（％または固定値）
        "y_range": 0.3
    },
    "Compact Car": {
        "ctrlpts": [[-0.8, -0.2], [-0.8, 1.5], [0.5, 3.0], [3.5, 4.8], [7.0, 5.1], [10.5, 4.5], [11.5, 2.5], [11.5, -0.2]],
        "weights": [0.1, 0.6, 0.3, 0.5, 0.5, 0.6, 0.5, 0.3],
        "tire_coords": [(1.5, 0.0), (10.0, 0.0)],
        "tire_radius": 1.1,
        "ground_y": -0.2,
        "bg_image": "compact.jpg",
        "image_extent": [-1.2, 12.5, -1.5, 6.5],
        "x_range": 0.7,
        "y_range": 0.4
    },
    "Sedan": {
        "ctrlpts": [[-0.5, 0.6], [-0.5, 2.0], [2.0, 2.8], [5.0, 4.5], [8.5, 4.5], [11.5, 3.2], [13.0, 2.8], [13.0, 0.6]],
        "weights": [0.1, 1.5, 2.0, 9.2, 10.0, 10.0, 10.0, 1.4],
        "tire_coords": [(2.3, 1.0), (10.7, 1.0)],
        "tire_radius": 1.2,
        "ground_y": 0.6,
        "bg_image": "sedan.jpg",
        "image_extent": [-2.0, 14.5, -1.5, 6.5],
        "x_range": 1.0,
        "y_range": 0.5
    },
    "Coupe": {
        "ctrlpts": [[0.0, 0.8], [0.0, 1.8], [2.0, 2.8], [5.0, 4.0], [8.0, 4.0], [11.0, 3.2], [12.0, 2.0], [12.0, 0.8]],
        "weights": [0.1, 0.9, 1.5, 3.0, 5.3, 3.0, 5.6, 2.0],
        "tire_coords": [(2.3, 1.0), (10.2, 1.0)],
        "tire_radius": 1.2,
        "ground_y": 0.8,
        "bg_image": "coupe.jpg",
        "image_extent": [-1.5, 13.5, -1.5, 6.0],
        "x_range": 1.0,
        "y_range": 0.4
    },
    "SUV": {
        "ctrlpts": [[-0.3, -0.5], [-0.3, 2.0], [1.5, 3.2], [4.5, 5.0], [9.0, 5.4], [12.5, 4.5], [13.0, 2.5], [13.0, -0.5]],
        "weights": [0.1, 0.5, 0.2, 0.4, 1.0, 0.6, 4.2, 2.8],
        "tire_coords": [(2.0, 0.0), (10.5, 0.0)],
        "tire_radius": 1.4,
        "ground_y": -0.5,
        "bg_image": "suv.jpg",
        "image_extent": [-1.5, 14.5, -1.5, 7.5],
        "x_range": 1.2,
        "y_range": 0.8
    },
    "Minivan": {
        "ctrlpts": [[-0.8, 0.1], [-0.8, 2.5], [1.0, 4.0], [4.0, 5.8], [9.5, 6.0], [12.5, 5.0], [12.5, 0.1]],
        "weights": [0.1, 0.9, 1.5, 3.0, 5.3, 1.5, 5.6],
        "tire_coords": [(2.1, 0.2), (10.4, 0.2)],
        "tire_radius": 1.4,
        "ground_y": 0.1,
        "bg_image": "minivan.jpg",
        "image_extent": [-1.5, 14.0, -1.5, 7.5],
        "x_range": 1.2,
        "y_range": 0.9
    }
}

# --- Undo (履歴) 機能の実装 ---
if "history" not in st.session_state:
    st.session_state.history = []

def save_state_to_history():
    current_state = {}
    for key in st.session_state:
        if ("_x_" in key) or ("_y_" in key) or ("_w_" in key) or (key == "alpha"):
            current_state[key] = st.session_state[key]
    
    st.session_state.history.append(current_state)
    if len(st.session_state.history) > 50:
        st.session_state.history.pop(0)

def undo_action():
    if st.session_state.history:
        st.session_state.history.pop()
        if st.session_state.history:
            last_state = st.session_state.history[-1]
            st.session_state.update(last_state)

# サイドバー
selected_model = st.sidebar.selectbox("車種を選択(Select a vehicle)", list(CAR_MODELS.keys()), on_change=lambda: st.session_state.history.clear())
model_data = CAR_MODELS[selected_model]

initial_ctrlpts = model_data["ctrlpts"]
initial_weights = model_data.get("weights", [])

# 重みデータの補完 
if len(initial_weights) < len(initial_ctrlpts):
    if len(initial_weights) == 0:
        initial_weights = [1.0] * len(initial_ctrlpts)
    else:
        initial_weights = initial_weights + [initial_weights[-1]] * (len(initial_ctrlpts) - len(initial_weights))
elif len(initial_weights) > len(initial_ctrlpts):
    initial_weights = initial_weights[:len(initial_ctrlpts)]

st.sidebar.markdown("### 制御点と重み調整(Control points and weight adjustment)")

# Undo/Reset
col_undo, col_reset = st.sidebar.columns([1, 1])
with col_undo:
    if st.button("↶ 戻る(Undo)"):
        undo_action()
        st.rerun()

with col_reset:
    if st.button("リセット(Reset)"):
        reset_state = {}
        for i, (pt, w) in enumerate(zip(initial_ctrlpts, initial_weights)):
            reset_state[f"{selected_model}_x_{i}"] = float(pt[0])
            reset_state[f"{selected_model}_y_{i}"] = float(pt[1])
            reset_state[f"{selected_model}_w_{i}"] = float(w)
        reset_state["alpha"] = 0.3
        st.session_state.update(reset_state)
        st.session_state.history = []
        st.rerun()

# セッションでalphaを保持 
if "alpha" not in st.session_state:
    st.session_state.alpha = 0.3

st.session_state.alpha = st.sidebar.slider(
    "透明度(transparency)", 0.0, 1.0, st.session_state.alpha, 0.05,
    on_change=save_state_to_history
)

# 固定Y座標 
fixed_ground_y = model_data["ground_y"]

new_ctrlpts, new_weights = [], []
num_points = len(initial_ctrlpts)

for i, (pt, w) in enumerate(zip(initial_ctrlpts, initial_weights)):
    x_key, y_key, w_key = f"{selected_model}_x_{i}", f"{selected_model}_y_{i}", f"{selected_model}_w_{i}"

    if x_key not in st.session_state:
        st.session_state[x_key] = float(pt[0])
    if y_key not in st.session_state:
        st.session_state[y_key] = float(pt[1])
    if w_key not in st.session_state:
        st.session_state[w_key] = float(w)

    st.sidebar.markdown(f"**Point {i}**")
    ww = st.sidebar.slider(f"重み(weight) {i}", 0.1, 15.0, st.session_state[w_key], 0.1, key=w_key, on_change=save_state_to_history)
    
    # === スライダーの可動域を車種ごとの寸法に合わせて調整 ===
    x_range = model_data["x_range"]
    y_range = model_data["y_range"]
    
    x = st.sidebar.slider(f"位置(point)X {i} ", float(pt[0]-x_range), float(pt[0]+x_range), st.session_state[x_key], 0.1, key=x_key, on_change=save_state_to_history)
    
    if i == 0 or i == num_points - 1:
        y = fixed_ground_y
        st.sidebar.caption(f"位置(point)Y {i} : Fixed ({fixed_ground_y})")
        st.session_state[y_key] = fixed_ground_y
    else:
        y = st.sidebar.slider(f"位置(point)Y {i} ", float(pt[1]-y_range), float(pt[1]+y_range), st.session_state[y_key], 0.1, key=y_key, on_change=save_state_to_history)

    new_ctrlpts.append([float(x), float(y)])
    new_weights.append(float(ww))
    st.sidebar.markdown("---")

# NURBS生成
curve = NURBS.Curve()
curve.degree = 3
curve.ctrlpts = new_ctrlpts
curve.weights = new_weights
curve.knotvector = knotvector.generate(curve.degree, len(new_ctrlpts))
curve.delta = 0.01
curve.evaluate()

# 描画
fig, ax = plt.subplots(figsize=(10, 7))
try:
    bg_image_path = model_data.get("bg_image", "")
    if bg_image_path and os.path.exists(bg_image_path):
        bg = mpimg.imread(bg_image_path)
        ext = model_data.get("image_extent", [-2, 14, -1.5, 7.5]) # デフォルト
        ax.imshow(bg, extent=ext, aspect='auto', alpha=0.3) # 背景画像の透明度を調整
    else:
        st.warning(f"背景画像 {bg_image_path} が見つかりません。")
except Exception:
    pass

# タイヤ描画 (車種ごとの座標と半径を使用)
tire_radius = model_data.get("tire_radius", 1.0)
for t in model_data.get("tire_coords", []):
    ax.add_patch(Circle((t[0], t[1]), tire_radius, color='black', zorder=1))

# 地面の線描画 (車種ごとの地面の高さを使用)
ground_line = model_data.get("ground_line", [])
current_start_x = new_ctrlpts[0][0]
current_end_x = new_ctrlpts[-1][0]
y_ground = fixed_ground_y
ax.plot([current_start_x, current_end_x], [y_ground, y_ground], '-', color='black', linewidth=1)

# NURBS曲線の描画 
curve_pts = np.array(curve.evalpts)
ax.plot(curve_pts[:, 0], curve_pts[:, 1], color='blue', linewidth=2)

# コントロールポイントの描画 
ctrl_np = np.array(new_ctrlpts)
ax.plot(ctrl_np[:, 0], ctrl_np[:, 1], '--', color='tab:red', marker='o')

for i in range(len(ctrl_np)):
    ax.text(ctrl_np[i, 0] + 0.2, ctrl_np[i, 1] + 0.2, str(i), fontsize=10, color='red', fontweight='bold')

# ポリゴンの描画 (透明度を適用) 
poly_pts = curve.evalpts + [new_ctrlpts[-1], new_ctrlpts[0]]
ax.add_patch(Polygon(poly_pts, closed=True, color='black', alpha=st.session_state.alpha))

# === ここで全車種統一のスケールを設定 ===
ax.set_xlim(-3, 16)
ax.set_ylim(-3, 9)
ax.set_aspect('equal')
ax.grid(True)

st.pyplot(fig)

# === Google Sheets保存 ===
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
# ユーザーのスプレッドシートURLを設定してください。
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1-mgxO9tqejwKehnbLS5B2JhCocdHH_xDWSZRLGKAE3A/edit?usp=sharing"

def save_to_google_sheet(name, gender, age_group, model, ctrlpts, weights, alpha_value, adjective):
    try:
        if client is None:
            raise RuntimeError("Google Sheetsへの接続設定がありません (Streamlit Secretsを確認してください)")

        spreadsheet = client.open_by_url(SPREADSHEET_URL)
        worksheet = spreadsheet.sheet1

        jst_time = datetime.utcnow() + timedelta(hours=9)
        timestamp = jst_time.strftime("%Y-%m-%d %H:%M:%S")

        ctrlpts_str = json.dumps(ctrlpts, ensure_ascii=False)
        weights_str = json.dumps(weights, ensure_ascii=False)

        row = [timestamp, name, gender, age_group, model, ctrlpts_str, weights_str, alpha_value, adjective]
        row = [str(v).encode("utf-8", "ignore").decode("utf-8") for v in row]

        worksheet.append_row(row, value_input_option="USER_ENTERED")
        return True, None
    except Exception as e:
        return False, str(e)

# === 送信ボタン ===
if st.button("保存する(save)"):
    if not name.strip():
        st.error("⚠️ 記入事項に回答してください。(please answer the questions)")
    else:
        ok, err = save_to_google_sheet(
            name,
            gender,
            age_group,
            selected_model,
            new_ctrlpts,
            new_weights,
            st.session_state.alpha,
            adjective
        )

        if ok:
            st.success("✅ 保存しました！(saved)")
        else:
            st.error("❌ 保存に失敗しました。(save failed)")
            with st.expander("エラー内容を表示"):
                st.code(err, language="text")