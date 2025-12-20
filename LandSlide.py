import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import classification_report

# CSV読み込み（先頭2行スキップ）
df = pd.read_csv("コピー下関1980.csv", skiprows=2)

# カラム名を設定
df.columns = ["Month", "Day", "Hour", "Hourly_rain", "Cumulative_rain", "Output"]

# 欠損値を除去
df = df.dropna()

# Outputを疑似的に再定義
df["Output"] = (
    (df["Hourly_rain"] >= 30) | (df["Cumulative_rain"] >= 200)
).astype(int)

# 特徴量とラベル
X = df[["Hourly_rain", "Cumulative_rain"]]
y = df["Output"]

# クラスの分布を表示
print("疑似崩壊ラベルの分布:")
print(y.value_counts())

# データ分割（stratifyでクラス比率を維持）
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# RBFカーネルのSVMを学習
model = SVC(kernel='rbf', C=1.0, gamma='scale')
model.fit(X_train, y_train)

# 予測と評価
y_pred = model.predict(X_test)

print("\n=== 土砂崩れ危険性（疑似）予測レポート ===")
print(classification_report(y_test, y_pred))

