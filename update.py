import streamlit as st
import json
import gspread
from google.oauth2.service_account import Credentials
import time

# ページ設定
st.set_page_config(page_title="データ一括更新ツール")
st.title("既存データの座標変化量 一括更新ツール")
st.markdown("スプレッドシート内の空の「座標変化量」列（G列）を自動計算して埋めます。")
st.warning("実行前に、各車種のシートでも「座標変化量」用の空のG列を作成しておいてください！")

# Google Sheets 認証設定
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/spreadsheets"]

try:
    if "credentials_json" in st.secrets:
        credentials_info = dict(st.secrets["credentials_json"])
        if "private_key" in credentials_info:
            credentials_info["private_key"] = credentials_info["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(credentials_info, scopes=scope)
        client = gspread.authorize(creds)
    else:
        st.error("Secretsにcredentials_jsonが見つかりません。")
        st.stop()
except Exception as e:
    st.error(f"認証エラー: {e}")
    st.stop()

# 各車種の初期座標（計算用）
CAR_MODELS_CTRLPTS = {
    "軽自動車(Kei_car)": [[-0.5, 0], [-0.5, 2.0], [-0.2, 2.65], [1.5, 3.0], [2.8, 5.0], [6.5, 5.1], [9.2, 5.1], [9.8, 4.5], [10.1, 1.58], [10.0, 0]],
    "コンパクトカー(Compact car)": [[-0.8, -0.2], [-0.9, 2.3], [0.7, 3.5], [2.1, 3.7], [4.2, 5.0], [7.3, 5.3], [11.3, 4.8], [10.8, 4.2], [11.6, 2.2], [11.7, -0.2]],
    "SUV": [[-0.3, -0.5], [-0.4, 2.4], [1.0, 3.0], [3.6, 3.4], [5.7, 5.3], [9.1, 5.6], [12.6, 5.0], [12.2, 4.2], [13.2, 3.0], [13.2, 0.3], [12.8, -0.5]],
    "セダン(Sedan)": [[-0.5, 0.6], [-0.3, 2.1], [1.5, 2.8], [3.0, 3.2], [5.0, 4.6], [9.0, 4.6], [11.6, 3.5], [13.0, 3.2], [13.0, 2.2], [13.2, 1.6], [13.0, 0.6]],
    "ミニバン(Minivan)": [[-0.8, 0.1], [-0.8, 2.8], [0.4, 3.7], [1.8, 3.9], [4.6, 6.0], [8.1, 6.3], [12.6, 6.2], [12.3, 5.4], [12.8, 3.2], [12.7, 0.1]],
    "クーペ(Coupe)": [[0, 0.8], [0.1, 2.25], [1.0, 2.9], [4.0, 3.4], [5.8, 4.2], [7.6, 4.3], [9.1, 3.9], [10.7, 3.7], [11.8, 3.2], [12.3, 2.0]]
}

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1-mgxO9tqejwKehnbLS5B2JhCocdHH_xDWSZRLGKAE3A/edit?usp=sharing"

if st.button("既存データを一括更新する"):
    with st.spinner("スプレッドシートを読み込み・更新中です。少し時間がかかります..."):
        try:
            spreadsheet = client.open_by_url(SPREADSHEET_URL)
            worksheets = spreadsheet.worksheets() # 「全体」シートだけでなく、各車種シートもすべて取得
            
            for ws in worksheets:
                st.write(f"▶ **{ws.title}** シートをチェック中...")
                all_values = ws.get_all_values()
                
                updates = [] # このシートで更新するセルのリスト
                
                for i, row in enumerate(all_values):
                    row_index = i + 1 # スプレッドシートは1行目からスタート
                    
                    # 列数が足りない場合は空白で埋める（エラー防止）
                    if len(row) < 7:
                        row.extend([""] * (7 - len(row)))
                        
                    model_name = row[4]    # E列: 車種
                    ctrlpts_str = row[5]   # F列: 保存されている座標
                    diff_str = row[6]      # G列: 座標変化量（ここが空なら補完する）
                    
                    # G列が空っぽ（まだ変化量が計算されていない）かつ、車種が辞書にある場合のみ処理
                    if diff_str.strip() == "" and model_name in CAR_MODELS_CTRLPTS:
                        try:
                            current_pts = json.loads(ctrlpts_str)
                            initial_pts = CAR_MODELS_CTRLPTS[model_name]
                            
                            # ポイント数が一致しているか確認
                            if len(current_pts) == len(initial_pts):
                                diffs = []
                                for c, init in zip(current_pts, initial_pts):
                                    diff_x = round(float(c[0]) - float(init[0]), 2)
                                    diff_y = round(float(c[1]) - float(init[1]), 2)
                                    diffs.append([diff_x, diff_y])
                                
                                new_diff_str = json.dumps(diffs, ensure_ascii=False)
                                
                                # 一括更新リストに追加（G列の該当行）
                                updates.append({
                                    'range': f'G{row_index}',
                                    'values': [[new_diff_str]]
                                })
                        except Exception as parse_e:
                            pass # JSON解析エラーの場合はスキップ

                # もし更新するデータがあれば、まとめて書き込む
                if updates:
                    ws.batch_update(updates)
                    st.success(f"{ws.title}シート: {len(updates)} 件のデータを更新しました！")
                    time.sleep(1) # Google APIのリクエスト制限を防ぐための待機時間
                else:
                    st.info(f"{ws.title}シート: 更新が必要なデータはありませんでした。")
                    
            st.balloons()
            st.success("🎉 すべてのシートの更新が完了しました！")
            
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")