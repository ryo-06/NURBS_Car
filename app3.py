#test
import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
from geomdl import NURBS, knotvector
import matplotlib.image as mpimg
import pandas as pd
import datetime
import os
import gspread
from google.oauth2.service_account import Credentials
import json
from datetime import datetime, timedelta

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

# Streamlit Secrets から credentials_json を取得
credentials_info = dict(st.secrets["credentials_json"])
if "private_key" in credentials_info:
    credentials_info["private_key"] = credentials_info["private_key"].replace("\\n", "\n")
creds = Credentials.from_service_account_info(credentials_info, scopes=scope)
client = gspread.authorize(creds)

# ページ設定
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

## 操作方法
1. 左のサイドバーで **車種を選択** してください。  
2. 点の順番は左下から順に0から始まります。
3. 車の先端を丸くしたり尖らせたりしたい場合は、**重み** を調整してください。  
4. 各 **位置X** スライダーで点を左右に、**位置Y** スライダーで上下に動かすことができます。  
5. 基本的には 点の**重み**を好みに調整 し、必要に応じて位置を微調整すると自然な形になります。  
6. 調整後、**透明度スライダー** で車体を黒くし、その印象に合う言葉を選んで評価してください。  
7. **複数の車種を回答する場合**は、1つの車種が終わったら 「保存」ボタンを押し、ページを更新してください。  
8. 回答は何度でも行うことができます。

## Instructions
1. **Select a vehicle model** from the left sidebar.
2. The order of the points starts from the bottom left, beginning with 0.            
3. If you want to make the car's tip rounded or pointed, adjust the **Weight**.
4. You can move points left and right using the **Point X** sliders and up and down using the **Point Y** sliders.
5. Basically, adjust the **Weight** of the points to your liking and fine-tune the position as needed to achieve a natural shape.
6. After adjustments, use the **Transparency slider** to make the car body black, and rate it using words that best represent its impression.
7. If you are **answering multiple vehicle models**, after finishing one vehicle model, press the "Save" button and refresh the page.
8. You can answer as many times as you like.
---
""")

# 自動翻訳を無効化
st.markdown(
    """
    <meta name="google" content="notranslate">
    <style>
    body { -webkit-user-select: text; }
    </style>
    """,
    unsafe_allow_html=True
)

# 車種データ
CAR_MODELS = {
    "軽自動車(Light Vehicle)": {
        "ctrlpts": [[-0.5, 0], [-0.5, 2.0], [-0.2, 2.65], [1.5, 3.0],
                    [2.6, 4.75], [3.5, 5.1], [6.5, 5.1], [9.2, 5.1],
                    [9.8, 4.5], [9.88, 1.75], [10.1, 1.58], [10.0, 0]],
        "weights": [1.0, 2.0, 2.0, 5.0, 5.0, 2.0, 1.0, 7.0,
                    12.5, 1.0, 1.0, 1.0],
        "tire_coords": [(0.85, 0.1), (8.5, 0.1)],
        "ground_line": [-0.5, 10.0, 0.0],
        "bg_image": "Kei_car.jpg"
    },
    "コンパクトカー(Compact car)": {
        "ctrlpts": [[-0.6, -0.2], [-0.8, 2.0], [0.6, 3.2], [1.9, 3.4],
                    [3.8, 4.6], [6.6, 4.9], [10.0, 4.6], [9.8, 3.9],
                    [10.3, 2.0], [10.6, 1.2], [10.3, -0.2]],
        "weights": [1.0, 6.0, 3.0, 5.0, 5.0, 6.0, 5.0, 3.0, 2.0, 1.0, 1.0],
        "tire_coords": [(0.85, -0.2), (8.8, -0.2)],
        "ground_line": [-0.6, 10.3, -0.2],
        "bg_image": "compact_car.jpg"
    },
    "SUV": {
        "ctrlpts": [[-0.1, -0.5], [-0.15, 1.8], [0.8, 2.3], [2.8, 2.7],
                    [4.4, 4.2], [7.0, 4.45], [9.7, 4.0], [9.35, 3.4],
                    [10.0, 2.4], [10.0, 0.2], [9.8, -0.6], [9.2, -0.5]],
        "weights": [1.0, 5.0, 1.8, 4.4, 10.0, 6.0, 15.0,
                    18.5, 28.8, 28.8, 22.5, 10.0],
        "tire_coords": [(1.8, -0.5), (8.1, -0.5)],
        "ground_line": [-0.1, 9.2, -0.5],
        "bg_image": "SUV.jpg"
    },
    "セダン(Sedan)": {
        "ctrlpts": [[-0.4, 0.6], [-0.2, 2.1], [1.2, 2.8], [2.4, 2.9],
                    [4.0, 4.0], [7.2, 4.0], [9.0, 3.1], [10.2, 3.0],
                    [10.2, 2.2], [10.35, 1.6], [10.2, 0.6]],
        "weights": [1.0, 14.6, 20.2, 91.8, 100.0, 100.0,
                    100.0, 100.0, 14.3, 15.0, 1.0],
        "tire_coords": [(1.6, 1.0), (8.2, 1.0)],
        "ground_line": [-0.4, 10.2, 0.6],
        "bg_image": "sedan2.jpg"
    },
    "ミニバン(Minivan)": {
        "ctrlpts": [[-0.5, 0], [-0.4, 2.0], [0, 2.5], [1.4, 2.9],
                    [3.7, 5.0], [6.5, 5.0], [10.1, 5.0], [9.8, 4.6],
                    [10.2, 2.9], [10.1, 1.5], [10.1, 0]],
        "weights": [1.0, 9.1, 15.1, 30.2, 52.9, 15.1,
                    56.2, 17.8, 12.0, 11.8, 1.0],
        "tire_coords": [(1.6, 0.2), (8.3, 0.2)],
        "ground_line": [-0.5, 10.1, 0],
        "bg_image": "Minivan.jpg"
    },
    "クーペ(coupe)": {
        "ctrlpts": [[0, 0.8], [0.1, 2.25], [0.8, 2.7], [3.4, 3.2],
                    [4.6, 3.85], [6.0, 4.0], [7.2, 3.7],
                    [8.4, 3.5], [9.4, 3.0], [9.8, 2.0], [9.5, 0.8]],
        "weights": [1.0, 9.1, 15.1, 30.2, 52.9, 30.0,
                    56.2, 20.0, 17.8, 11.8, 1.0],
        "tire_coords": [(1.8, 1.0), (8.0, 1.0)],
        "ground_line": [0, 9.4, 0.8],
        "bg_image": "coope.jpg"
    }
}

# サイドバー
selected_model = st.sidebar.selectbox("車種を選択(Select a vehicle)", list(CAR_MODELS.keys()))
model_data = CAR_MODELS[selected_model]

initial_ctrlpts = model_data["ctrlpts"]
initial_weights = model_data.get("weights", [])

if len(initial_weights) < len(initial_ctrlpts):
    if len(initial_weights) == 0:
        initial_weights = [1.0] * len(initial_ctrlpts)
    else:
        initial_weights = initial_weights + [initial_weights[-1]] * (len(initial_ctrlpts) - len(initial_weights))
elif len(initial_weights) > len(initial_ctrlpts):
    initial_weights = initial_weights[:len(initial_ctrlpts)]

st.sidebar.markdown("### ⚙️ 制御点と重み調整(Control points and weight adjustment)")

# --- 不透明スライダーとリセット連動 ---
if st.sidebar.button("初期値にリセット(Reset to default)"):
    reset_state = {}
    for i, (pt, w) in enumerate(zip(initial_ctrlpts, initial_weights)):
        reset_state[f"{selected_model}_x_{i}"] = float(pt[0])
        reset_state[f"{selected_model}_y_{i}"] = float(pt[1])
        reset_state[f"{selected_model}_w_{i}"] = float(w)
    reset_state["alpha"] = 0.3  # 不透明度も初期化
    st.session_state.update(reset_state)
    st.rerun()

# セッションでalphaを保持
if "alpha" not in st.session_state:
    st.session_state.alpha = 0.3

st.session_state.alpha = st.sidebar.slider(
    "透明度(transparency)", 0.0, 1.0, st.session_state.alpha, 0.05
)

new_ctrlpts, new_weights = [], []
for i, (pt, w) in enumerate(zip(initial_ctrlpts, initial_weights)):
    x_key, y_key, w_key = f"{selected_model}_x_{i}", f"{selected_model}_y_{i}", f"{selected_model}_w_{i}"

    if x_key not in st.session_state:
        st.session_state[x_key] = float(pt[0])
    if y_key not in st.session_state:
        st.session_state[y_key] = float(pt[1])
    if w_key not in st.session_state:
        st.session_state[w_key] = float(w)

    ww = st.sidebar.slider(f"重み(weight) {i}", 0.1, 150.0, st.session_state[w_key], 0.1, key=w_key)
    x = st.sidebar.slider(f"位置(point)X {i} ", float(pt[0]-1), float(pt[0]+1), st.session_state[x_key], 0.1, key=x_key)
    y = st.sidebar.slider(f"位置(point)Y {i} ", float(pt[1]-1), float(pt[1]+1), st.session_state[y_key], 0.1, key=y_key)

    new_ctrlpts.append([float(x), float(y)])
    new_weights.append(float(ww))

# NURBS曲線生成
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
    bg = mpimg.imread(model_data.get("bg_image", ""))
    ax.imshow(bg, extent=[-1, 11, -1.5, 6], aspect='auto', alpha=0.2)
except Exception:
    pass

for t in model_data.get("tire_coords", []):
    ax.add_patch(Circle((t[0], t[1]), 0.9, color='black', zorder=1))

if "ground_line" in model_data:
    x0, x1, y_ground = model_data["ground_line"]
    ax.plot([x0, x1], [y_ground, y_ground], '-', color='black', linewidth=1)

curve_pts = np.array(curve.evalpts)
ax.plot(curve_pts[:, 0], curve_pts[:, 1], color='blue', linewidth=2)

ctrl_np = np.array(new_ctrlpts)
ax.plot(ctrl_np[:, 0], ctrl_np[:, 1], '--', color='tab:red', marker='o')

poly_pts = curve.evalpts + [new_ctrlpts[-1], new_ctrlpts[0]]
ax.add_patch(Polygon(poly_pts, closed=True, color='black', alpha=st.session_state.alpha))

ax.set_xlim(-3, 13)
ax.set_ylim(-3, 8)
ax.set_aspect('equal')
ax.grid(True)

st.pyplot(fig)

# --- ユーザー入力欄 ---
st.markdown("---")
st.markdown("### 回答者情報(Respondent Information)")

name = st.text_input("ニックネーム(NickName)")
gender = st.radio("性別(gender)", ["男性(M)", "女性(F)"], horizontal=True)
age_group = st.selectbox("年代", ["10代未満(Under 10s)", "10代(10s)", "20代(20s)", "30代(30s)", "40代(40s)", "50代(50s)", "60代(60s)", "70代以上(70s and older)"])

st.markdown("### この車の印象を教えてください(What are your impression of this car?)")
adjective = st.selectbox(
    "あなたの作った車を一言で表すと？(How would you describe it?)",
    ["かわいい(cute)", "かっこいい(cool)", "頑丈そう(sturdy)", "速そう(fast)", "高級な(luxury)", "親しみのある(familiar)"]
)

# === Google Sheets保存設定 ===
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1-mgxO9tqejwKehnbLS5B2JhCocdHH_xDWSZRLGKAE3A/edit?usp=sharing"


def save_to_google_sheet(name, gender, age_group, model, ctrlpts, weights, alpha_value, adjective):
    try:
        if "credentials_json" not in st.secrets:
            raise RuntimeError("Streamlit secrets に 'credentials_json' が見つかりません。")

        credentials_info = dict(st.secrets["credentials_json"])
        creds = Credentials.from_service_account_info(credentials_info, scopes=SCOPES)
        client = gspread.authorize(creds)

        spreadsheet = client.open_by_url(SPREADSHEET_URL)
        worksheet = spreadsheet.sheet1

        # ✅ JST（日本時間）で保存
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
