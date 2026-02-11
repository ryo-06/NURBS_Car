import os
import math
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import platform

# === 設定 ===
INPUT_DIR = "output_images_attributes"  # 整理された画像があるフォルダ
OUTPUT_DIR = "summary_images"           # まとめ画像の保存先
COLS = 5                                # 横に並べる画像の数

# === 日本語フォント設定（ここを追加しました） ===
system_name = platform.system()
if system_name == "Windows":
    plt.rcParams['font.family'] = 'MS Gothic' # Windows用
elif system_name == "Darwin":
    plt.rcParams['font.family'] = 'AppleGothic' # Mac用
else:
    # Linuxなど（Colab含む）の場合はIPAgothicなどを指定する必要があるが
    # 今回はPC実行と仮定してデフォルト設定のままにします
    pass

# === 処理開始 ===
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

if not os.path.exists(INPUT_DIR):
    print(f"エラー: '{INPUT_DIR}' が見つかりません。先に以前のプログラムを実行してください。")
    exit()

# フォルダ一覧を取得
folders = [f for f in os.listdir(INPUT_DIR) if os.path.isdir(os.path.join(INPUT_DIR, f))]

print(f"--- 画像のまとめ作成を開始します（全 {len(folders)} カテゴリ） ---")

for folder_name in folders:
    folder_path = os.path.join(INPUT_DIR, folder_name)
    
    # 画像ファイルを取得
    images = [f for f in os.listdir(folder_path) if f.lower().endswith('.png')]
    
    if not images:
        continue

    # 並べ替え
    images.sort()

    num_images = len(images)
    rows = math.ceil(num_images / COLS)

    print(f"カテゴリ '{folder_name}': {num_images}枚 -> {rows}行 x {COLS}列 で作成中...")

    # 画像サイズ設定
    fig_width = 20
    fig_height = rows * 3.5  # 高さを少し広げました（文字が切れないように）
    
    fig, axes = plt.subplots(rows, COLS, figsize=(fig_width, fig_height))
    
    # axesの配列調整
    if rows == 1 and COLS == 1:
        axes = [axes]
    elif rows == 1 or COLS == 1:
        axes = axes.flatten()
    elif rows > 1 and COLS > 1:
        axes = axes.flatten()

    # タイトル
    fig.suptitle(f"Category: {folder_name} (Total: {num_images})", fontsize=24, y=0.99)

    # 各画像を配置
    for i, ax in enumerate(axes):
        if i < num_images:
            img_path = os.path.join(folder_path, images[i])
            try:
                img = mpimg.imread(img_path)
                ax.imshow(img)
                
                # ファイル名から情報を表示
                # 例: 001_SUV_20s_M_cool.png
                fname = os.path.splitext(images[i])[0]
                parts = fname.split('_')
                if len(parts) >= 5: # ID, 車種, 年代, 性別, 形容詞
                    # 日本語や記号も文字化けせずに表示されます
                    label = f"ID:{parts[0]} {parts[1]}\n({parts[2]} / {parts[3]})"
                else:
                    label = fname
                
                ax.set_title(label, fontsize=12)
                ax.axis('off')
            except Exception as e:
                print(f"  読み込みエラー: {images[i]}")
                ax.axis('off')
        else:
            # 余白
            ax.axis('off')

    # レイアウト調整
    plt.tight_layout(rect=[0, 0, 1, 0.97])
    
    # 保存
    save_path = os.path.join(OUTPUT_DIR, f"{folder_name}_summary.png")
    plt.savefig(save_path, bbox_inches='tight')
    plt.close(fig)

print(f"\n✅ すべて完了しました！")
print(f"保存先: {os.path.abspath(OUTPUT_DIR)}")