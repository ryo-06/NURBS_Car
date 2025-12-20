import tkinter as tk #Tkinter（GUI作成ライブラリ）を tk としてインポート
from tkinter import ttk #Tkinter の拡張ウィジェット（ttk：テーマ対応）を使えるようにした
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg #matplotlib のグラフを Tkinter 内に表示するためのブリッジ
import matplotlib.pyplot as plt #グラフ描画ライブラリ matplotlib を plt という名前で使用
from matplotlib.patches import Polygon #グラフ上に図形（多角形）を描画するために使う
from geomdl import NURBS #NURBS 曲線を作成・操作するためのライブラリ
from geomdl import knotvector #NURBS に必要なノットベクトルを生成するための関数
import matplotlib.image as mpimg #画像読み込み用（背景画像を読み込むために使用）

# 制御点と重み
ctrlpts = [ 
    [-0.35, -0.2], [-0.4, 1.3], [-0.2, 2.0], [1.2, 2.7], 
    [2.5, 2.9], [4.0, 4.35], [7.2, 4.35], [9.0, 3.1], 
    [9.8, 3.1], [9.9, 2.0], [10.05, 1.3], [9.95, -0.2]
]

weights = [
    1.0, 3.4, 4.4, 4.5, 
    25.6, 100.0, 100.0, 21.9, 
    14.3, 1.0, 3.1, 1.0
]

#制御点と重みをもとに NURBS 曲線を生成する関数の定義
def make_curve(ctrlpts, weights):
    curve = NURBS.Curve() #NURBS 曲線オブジェクトを生成
    curve.degree = 3 #曲線の階数を設定（3は三次曲線で滑らか）
    curve.ctrlpts = ctrlpts #制御点を設定
    curve.weights = weights #重みを設定
    curve.knotvector = knotvector.generate(curve.degree, len(ctrlpts)) #ノットベクトルを自動生成
    curve.delta = 0.01 #曲線を評価する粒度を設定
    curve.evaluate() #曲線を評価して描画用の点列を計算
    return curve #完成した NURBS 曲線オブジェクトを返す

class NURBSApp(tk.Tk): #アプリ全体の GUI クラスを定義。tk.Tk を継承
    def __init__(self): 
        super().__init__() #コンストラクタを定義し、親クラスの初期化を呼ぶ
        self.title("compact car") #ウィンドウタイトルを設定
        self.geometry("1200x800") #ウィンドウの初期サイズを設定

        self.fig, self.ax = plt.subplots(figsize=(10, 7)) #matplotlib の Figure と Axes を生成（描画領域の設定）
        self.canvas = FigureCanvasTkAgg(self.fig, master=self) #matplotlib の描画を Tkinter ウィンドウに組み込む
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=1) #グラフ領域を画面左に表示

        #背景画像を読み込んで表示（透明度 0.2）、位置範囲を指定
        try:
            bg_image = mpimg.imread("sedan_car.jpg")
            self.ax.imshow(bg_image, extent=[-1, 11, -1.5, 5.5], aspect='auto', alpha=0.2)
        except Exception as e:
            print("画像の読み込みに失敗しました:", e) #画像読み込みに失敗したら、エラー内容を表示

        self.curve = make_curve(ctrlpts, weights) #制御点と重みから NURBS 曲線を生成
        self.curve_plot, = self.ax.plot(
            [pt[0] for pt in self.curve.evalpts],
            [pt[1] for pt in self.curve.evalpts],
            label='NURBS Curve'
        ) #評価された NURBS 曲線をプロット
        self.scatter_plot = self.ax.scatter(
            [pt[0] for pt in ctrlpts],
            [pt[1] for pt in ctrlpts],
            color='black',
            label='Control Points'
        ) #制御点を黒い点で表示

        #車のタイヤを円で表現
        self.tire1 = plt.Circle((1.75, -0.2), 0.7, fill=False, color='gray')
        self.tire2 = plt.Circle((8.0, -0.2), 0.7, fill=False, color='gray')
        #タイヤをグラフに追加
        self.ax.add_patch(self.tire1)
        self.ax.add_patch(self.tire2)
        #地面を灰色の直線で描画
        self.ax.plot([-0.35, 9.95], [-0.2, -0.2], linestyle='-', color='gray', linewidth=1, label='Under Line')

        #表示範囲と縦横比（1:1）を設定
        self.ax.set_xlim(-3, 13)
        self.ax.set_ylim(-3, 8)
        self.ax.set_aspect('equal')
        #タイトルと凡例を表示、x軸は非表示
        self.ax.set_title("Sedan")
        self.ax.legend()

        #上部に重みをテキストで表示
        self.weight_text = self.fig.text(0.5, 0.95, "", ha='center', va='bottom', fontsize=12, fontweight='bold')
        self.update_weight_text(weights)

        # 塗りつぶしの修正: コントロールポイントの始点と終点を使って閉じる
        filled_points = self.curve.evalpts + [ctrlpts[-1], ctrlpts[0]]
        self.filled_patch = Polygon(filled_points, closed=True, color='black', alpha=0.3)
        self.ax.add_patch(self.filled_patch)

        #スライダーエリアを右側に作成して、スライダー生成関数を呼び出す
        self.slider_frame = ttk.Frame(self)
        self.slider_frame.pack(side=tk.RIGHT, fill=tk.Y)
        self.create_scrollable_sliders()

    #重みリストをテキスト形式に変換して表示更新
    def update_weight_text(self, weights):
        wt_text = "Weights: " + ", ".join([f"{w:.1f}" for w in weights])
        self.weight_text.set_text(wt_text)

    def create_scrollable_sliders(self): #制御点（X・Y）と重み（W）を操作するスライダーを生成し、スクロール可能なエリアに配置する関数
        canvas = tk.Canvas(self.slider_frame, width=500)
        scrollbar = ttk.Scrollbar(self.slider_frame, orient="vertical", command=canvas.yview)
        self.sliders_container = ttk.Frame(canvas)

        #スライダーをたくさん並べても、スクロールバーが正しく働くようになり、これが無いとスクロールバーがあるのに下が見えない
        self.sliders_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.sliders_container, anchor="nw") #sliders_container（スライダーたちが入ってるFrame）を、canvasの中にウィンドウとして貼り付ける。
        canvas.configure(yscrollcommand=scrollbar.set) #このスクロールバーと連携して動いてね
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.sliders_x = []
        self.sliders_y = []
        self.sliders_w = []

        slider_height = 40
        padding_y = 30

        for i, (pt, w) in enumerate(zip(ctrlpts, weights)):
            label = ttk.Label(self.sliders_container, text=f"Control Point {i}") #各制御点の番号ラベルを作成
            label.pack(pady=(padding_y, 0))

            frame_x = ttk.Frame(self.sliders_container)
            frame_x.pack(fill=tk.X, padx=5) #frame_x を横いっぱいに広げて表示
            lbl_x = ttk.Label(frame_x, text=f"X{i}")
            lbl_x.pack(side=tk.LEFT)
            slider_x = tk.Scale(frame_x, from_=-2.0, to=12.0, resolution=0.1, orient=tk.HORIZONTAL, length=400, showvalue=False) #実際のXスライダーを作成
            slider_x.set(pt[0]) #スライダーの初期値を設定 → pt[0]（X座標）
            slider_x.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=5) #作成したスライダーを frame_x に表示
            self.sliders_x.append(slider_x)

            frame_y = ttk.Frame(self.sliders_container)
            frame_y.pack(fill=tk.X, padx=5)
            lbl_y = ttk.Label(frame_y, text=f"Y{i}")
            lbl_y.pack(side=tk.LEFT)
            slider_y = tk.Scale(frame_y, from_=-4.0, to=8.0, resolution=0.1, orient=tk.HORIZONTAL, length=400, showvalue=False)
            slider_y.set(pt[1])
            slider_y.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=5)
            self.sliders_y.append(slider_y)

            frame_w = ttk.Frame(self.sliders_container)
            frame_w.pack(fill=tk.X, padx=5, pady=(0, 10))
            lbl_w = ttk.Label(frame_w, text=f"W{i}")
            lbl_w.pack(side=tk.LEFT)
            slider_w = tk.Scale(frame_w, from_=1.0, to=50.0, resolution=0.1, orient=tk.HORIZONTAL, length=400, showvalue=False)
            slider_w.set(w)
            slider_w.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=5)
            self.sliders_w.append(slider_w)

        def on_slider_change(event): #イベントハンドラ関数の定義でスライダーが操作されたときに実行
            self.update_curve()

        for slider in self.sliders_x + self.sliders_y + self.sliders_w:
            slider.bind("<ButtonRelease-1>", on_slider_change)
            slider.bind("<B1-Motion>", on_slider_change)

        label_alpha = ttk.Label(self.sliders_container, text="Fill Opacity")
        label_alpha.pack(pady=(20, 0))
        self.alpha_slider = tk.Scale(self.sliders_container, from_=0.0, to=1.0, resolution=0.05, orient=tk.HORIZONTAL, length=400, showvalue=True)
        self.alpha_slider.set(0.3)
        self.alpha_slider.pack(pady=(0, 20))

        def on_alpha_change(event):
            if hasattr(self, 'filled_patch'):
                self.filled_patch.set_alpha(self.alpha_slider.get())
                self.canvas.draw_idle()

        self.alpha_slider.bind("<ButtonRelease-1>", on_alpha_change)
        self.alpha_slider.bind("<B1-Motion>", on_alpha_change)

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

        if hasattr(self, 'filled_patch'):
            self.filled_patch.remove()

        filled_points = self.curve.evalpts + [new_ctrlpts[-1], new_ctrlpts[0]]
        self.filled_patch = Polygon(filled_points, closed=True, color='black', alpha=self.alpha_slider.get())
        self.ax.add_patch(self.filled_patch)

        self.canvas.draw_idle()

if __name__ == "__main__":
    app = NURBSApp()
    app.mainloop()