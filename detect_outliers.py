import pandas as pd
from scipy.stats import zscore

# Excelファイル名
file_path = "判定済みデータ.xlsx"
xls = pd.ExcelFile(file_path)
sheet_names = xls.sheet_names

# シートごとの列名対応辞書 
column_map = {
    "Pattern1": {"amps": "Amps", "lower": "区間の下限値", "upper": "区間の上限値", "center": "中心値", "judge": "判定"},
    "Pattern2": {"amps": "Amp",  "lower": "区間の下限値", "upper": "区間の上限値", "center": "中心値", "judge": "判定"},
    "Pattern3": {"amps": "Amps", "lower": "区間の下限値", "upper": "区間の上限値", "center": "中心値", "judge": "判定"},
    "Pattern4": {"amps": "Amps", "lower": "区間の下限値", "upper": "区間の上限値", "center": "中心値", "judge": "判定"},
}

# 結果の格納リスト
all_results = []

# 各シート処理 
for sheet in sheet_names:
    print(f"\n=== {sheet} の処理開始 ===")

    df = pd.read_excel(file_path, sheet_name=sheet)
    df.columns = df.columns.str.strip() # 空白除去

    if sheet not in column_map:
        print(f"{sheet} は列マップが未定義のためスキップします")
        continue

    cols = column_map[sheet]
    try:
        for _, row in df.iterrows():
            # NaN 判定回避と正常行のスキップ
            if pd.notna(row[cols["judge"]]) and row[cols["judge"]] != "正常":
                lower = row[cols["lower"]]
                upper = row[cols["upper"]]

                amps_in_range = df[(df[cols["amps"]] >= lower) & (df[cols["amps"]] < upper)][cols["amps"]]

                if len(amps_in_range) >= 3:
                    zs = zscore(amps_in_range)
                    outliers = amps_in_range[abs(zs) >= 2].drop_duplicates()

                    if not outliers.empty:
                        all_results.append({
                            "シート": sheet,
                            "区間中心": row[cols["center"]],
                            "判定": row[cols["judge"]],
                            "異常値数": len(outliers),
                            "異常値一覧": list(outliers)
                        })
    except KeyError as e:
        print(f"列名エラー: {e}")
    except Exception as e:
        print(f"その他のエラー: {e}")

# 出力
print("\n【異常値検出結果（全シート）】")
for r in all_results:
    print(f"{r['シート']} | 区間中心 = {r['区間中心']:.3f} | 判定 = {r['判定']} | 異常値数 = {r['異常値数']}")
    print("  異常値:", r['異常値一覧'])


