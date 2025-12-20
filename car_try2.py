import tkinter as tk #GUI作成用のTkinterをtkという名前でインポート
from tkinter import ttk #高機能なウィジェット（ボタンやスライダーなど）用のttkモジュール
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg #MatplotlibのグラフをTkinterに埋め込むためのツール
import matplotlib.pyplot as plt #グラフ描画の標準的なモジュール
from geomdl import NURBS #NURBS（非一様有理Bスプライン）を定義するためのライブラリ
from geomdl import knotvector #	NURBSのノットベクトルを生成するための関数
import matplotlib.image as mpimg #	画像読み込み用（背景画像を表示する）

# 制御点と重み
ctrlpts = [
    [-1, 0], [-1, 1], [0, 2.5], [2, 3.5],
    [3, 4.2], [5, 5.3], [7, 5.5], [9, 5.2],
    [10, 4], [10.8, 2.5], [11, 1.5], [11, 0]
]
weights = [1.0, 10.0, 10.0, 0.9, 1.1, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 1.4]

# NURBS曲線準備関数
def make_curve(ctrlpts, weights):
    curve = NURBS.Curve() #曲線オブジェクトを作成
    curve.degree = 3 #曲線の次数を3に設定（3次NURBS）
    curve.ctrlpts = ctrlpts #制御点を設定
    curve.weights = weights #重みを設定
    curve.knotvector = knotvector.generate (curve.degree, len(ctrlpts)) #ノットベクトル（曲線の区切り）を自動生成
    curve.delta = 0.01 #曲線の分解能（細かさ）
    curve.evaluate() #曲線を評価（描画できる点を計算）
    return curve #完成した曲線を返す

# tk.Tkを継承してGUIアプリ全体を定義
class NURBSApp(tk.Tk):
    def __init__(self):
        super().__init__() #親クラスtk.Tkの初期化
        self.title("Scrollable NURBS Car Silhouette Editor") #ウィンドウのタイトルを設定
        self.geometry("1200x800") #	ウィンドウサイズ（横1200px × 縦800px）

        # Matplotlib FigureとAxes
        self.fig, self.ax = plt.subplots(figsize=(10, 7)) #plt.subplots(...):Matplotlibの図と軸を作成
        self.canvas = FigureCanvasTkAgg(self.fig, master=self) #FigureCanvasTkAgg(...):MatplotlibをTkinterに埋め込む
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=1) #pack(...):GUI上に表示

        # 背景画像読み込み（アップロードした画像パスに合わせる）
        try:
            bg_image = mpimg.imread("car_image1.jpg")  # PNG名を変更可能
            self.ax.imshow(bg_image, extent=[-1, 11, -1.5, 5.5], aspect='auto', alpha=0.2) #extentで画像の表示領域（座標）を指定、alphaで透明度調整
        except Exception as e:
            print("画像の読み込みに失敗しました:", e)

        # 曲線と制御点初期描画
        self.curve = make_curve(ctrlpts, weights) #NURBS曲線を作成
        self.curve_plot, = self.ax.plot(
            [pt[0] for pt in self.curve.evalpts],
            [pt[1] for pt in self.curve.evalpts],
            label='NURBS Curve'
        ) #plot(...)で曲線の線を描画
        self.scatter_plot = self.ax.scatter(
            [pt[0] for pt in ctrlpts],
            [pt[1] for pt in ctrlpts],
            color='black',
            label='Control Points'
        ) #scatter(...)で制御点（黒点）を描画

        # タイヤ描画
        self.tire1 = plt.Circle((1.0, 0), 0.8, fill=False, color='gray')
        self.tire2 = plt.Circle((9.0, 0), 0.8, fill=False, color='gray') #Circle(...)でタイヤ（円）を描画
        self.ax.add_patch(self.tire1)
        self.ax.add_patch(self.tire2) #add_patch()でMatplotlib上に追加

        self.ax.plot([-1, 11], [0, 0], linestyle='-', color='gray', linewidth=1, label='Under Line')

        self.ax.set_xlim(-3, 13)
        self.ax.set_ylim(-3, 8)
        self.ax.set_aspect('equal')
        self.ax.set_title("Editable NURBS Car Silhouette")
        self.ax.xaxis.set_visible(False)
        self.ax.legend()

        # 重みテキスト表示
        self.weight_text = self.fig.text(0.5, 0.95, "", ha='center', va='bottom', fontsize=12, fontweight='bold')
        self.update_weight_text(weights) #update_weight_text()で内容更新

        # スライダー用フレーム（スクロール可能）
        self.slider_frame = ttk.Frame(self) #ttk.Frame(self)：ウィンドウの中に「枠（フレーム）」を作る
        self.slider_frame.pack(side=tk.RIGHT, fill=tk.Y) #pack(side=tk.RIGHT)：このフレームを右側に配置する、fill=tk.Y：縦方向（Y方向）にいっぱいに広がるようにする

        self.create_scrollable_sliders() #実際にスライダーを作る関数 create_scrollable_sliders() を呼ぶ

    #画面上に「現在の重み」を表示する
    def update_weight_text(self, weights):
        wt_text = "Weights: " + ", ".join([f"{w:.1f}" for w in weights]) #", ".join(...)：リストをカンマ区切りで文字列に変換する、f"{w:.1f}"：重みを小数第1位まで表示する書き方
        self.weight_text.set_text(wt_text)#self.weight_text.set_text(...)：そのテキストを表示エリアに反映する

    def create_scrollable_sliders(self):
        canvas = tk.Canvas(self.slider_frame, width=500) #Canvas：中にフレームを置くための土台でスクロール対応の領域
        scrollbar = ttk.Scrollbar(self.slider_frame, orient="vertical", command=canvas.yview) #Scrollbar：縦スクロールバーを作成
        self.sliders_container = ttk.Frame(canvas) #sliders_container：実際にスライダー群を入れるための入れ物

        #スライダーの数が変わったとき、scrollregion（スクロール範囲）を更新
        self.sliders_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        ) #canvas.bbox("all")：すべてのウィジェットの範囲を計算

        canvas.create_window((0, 0), window=self.sliders_container, anchor="nw") #create_window(...)：Canvasの中に sliders_containerを置く
        canvas.configure(yscrollcommand=scrollbar.set) #yscrollcommand=...：スクロールバーがちゃんと動くようにする

        #canvas を左に、scrollbar を右に並べて表示する
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.sliders_x = []
        self.sliders_y = []
        self.sliders_w = []

        slider_height = 40
        padding_y = 30

        #制御点（座標）と重みの組を1個ずつ取り出して、i番目として扱う
        for i, (pt, w) in enumerate(zip(ctrlpts, weights)):
            label = ttk.Label(self.sliders_container, text=f"Control Point {i}")
            label.pack(pady=(padding_y, 0))

            # Xスライダー
            frame_x = ttk.Frame(self.sliders_container)
            frame_x.pack(fill=tk.X, padx=5)
            lbl_x = ttk.Label(frame_x, text=f"X{i}")
            lbl_x.pack(side=tk.LEFT)
            slider_x = ttk.Scale(frame_x, from_=-2.0, to=12.0, orient=tk.HORIZONTAL, length=400)
            slider_x.set(pt[0])
            slider_x.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=5)
            self.sliders_x.append(slider_x)

            # Yスライダー
            frame_y = ttk.Frame(self.sliders_container)
            frame_y.pack(fill=tk.X, padx=5)
            lbl_y = ttk.Label(frame_y, text=f"Y{i}")
            lbl_y.pack(side=tk.LEFT)
            slider_y = ttk.Scale(frame_y, from_=-4.0, to=8.0, orient=tk.HORIZONTAL, length=400)
            slider_y.set(pt[1])
            slider_y.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=5)
            self.sliders_y.append(slider_y)

            # Wスライダー
            frame_w = ttk.Frame(self.sliders_container)
            frame_w.pack(fill=tk.X, padx=5, pady=(0, 10))
            lbl_w = ttk.Label(frame_w, text=f"W{i}")
            lbl_w.pack(side=tk.LEFT)
            slider_w = ttk.Scale(frame_w, from_=0.1, to=20.0, orient=tk.HORIZONTAL, length=400)
            slider_w.set(w)
            slider_w.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=5)
            self.sliders_w.append(slider_w)

        #on_slider_change：スライダーを動かしたときに曲線を更新する関数
        def on_slider_change(event):
            self.update_curve()

        for slider in self.sliders_x + self.sliders_y + self.sliders_w:
            slider.bind("<ButtonRelease-1>", on_slider_change)
            slider.bind("<B1-Motion>", on_slider_change) #bind(...)：スライダーを「動かす」 or 「離す」動作に反応させる

        #スライダーの値に応じてNURBS曲線を再計算して表示を更新
    def update_curve(self):
        new_ctrlpts = [[sx.get(), sy.get()] for sx, sy in zip(self.sliders_x, self.sliders_y)]
        new_weights = [sw.get() for sw in self.sliders_w]

        self.curve.ctrlpts = new_ctrlpts
        self.curve.weights = new_weights
        self.curve.evaluate()

        self.curve_plot.set_xdata([pt[0] for pt in self.curve.evalpts])
        self.curve_plot.set_ydata([pt[1] for pt in self.curve.evalpts])

        self.scatter_plot.set_offsets(new_ctrlpts)
        self.update_weight_text(new_weights)
        self.canvas.draw_idle()


if __name__ == "__main__": #__name__ == "__main__"：このファイルが直接実行されたときだけ、アプリを起動する
    app = NURBSApp() #NURBSApp()：上で作ったGUIクラスを使ってウィンドウを表示
    app.mainloop() #mainloop()：ウィンドウを閉じるまでイベント（操作）を受け付け続ける

