import pandas as pd

# Excelファイルのパス
file_path = "判定済みデータ.xlsx"  # ファイル名が違う場合は変更してください

# Excelファイルを読み込み
xls = pd.ExcelFile(file_path)
sheet_names = xls.sheet_names

# 各シートの列名を表示
for sheet in sheet_names:
    df = pd.read_excel(file_path, sheet_name=sheet)
    df.columns = df.columns.str.strip()  # 空白を除去

    print(f"\n📄 {sheet} の列名一覧:")
    print(list(df.columns))
