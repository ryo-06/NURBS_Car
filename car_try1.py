import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from geomdl import NURBS
from geomdl import knotvector

# 制御点と重み
ctrlpts = [
    [-1, 0], [-1, 1], [0, 2], [2, 3],
    [3, 4], [5, 4], [7, 4], [9, 4],
    [10, 3], [11, 1.5], [11, 0]
]
weights = [1.0, 10.0, 1.1, 10.0, 1.1, 1.3, 5.0, 0.9, 1.0, 1.2, 1.4]

# NURBS曲線準備関数
def make_curve(ctrlpts, weights):
    curve = NURBS.Curve()
    curve.degree = 3
    curve.ctrlpts = ctrlpts
    curve.weights = weights
    curve.knotvector = knotvector.generate(curve.degree, len(ctrlpts))
    curve.delta = 0.01
    curve.evaluate()
    return curve

# Tkinterアプリ
class NURBSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Scrollable NURBS Car Silhouette Editor")
        self.geometry("1100x700")

        # Matplotlib FigureとAxes
        self.fig, self.ax = plt.subplots(figsize=(8,7))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        # 曲線と制御点初期描画
        self.curve = make_curve(ctrlpts, weights)
        self.curve_plot, = self.ax.plot(
            [pt[0] for pt in self.curve.evalpts],
            [pt[1] for pt in self.curve.evalpts],
            label='NURBS Curve'
        )
        self.scatter_plot = self.ax.scatter(
            [pt[0] for pt in ctrlpts],
            [pt[1] for pt in ctrlpts],
            color='black',
            label='Control Points'
        )
        # タイヤ描画
        self.tire1 = plt.Circle((2, 0), 0.8, fill=False, color='gray')
        self.tire2 = plt.Circle((8, 0), 0.8, fill=False, color='gray')
        self.ax.add_patch(self.tire1)
        self.ax.add_patch(self.tire2)

        self.ax.plot([-1, 11], [0, 0], linestyle='-', color='gray', linewidth=1, label='Under Line')

        self.ax.set_xlim(-3, 13)
        self.ax.set_ylim(-3, 8)
        self.ax.set_aspect('equal')
        self.ax.set_title("Editable NURBS Car Silhouette")
        self.ax.xaxis.set_visible(False)
        self.ax.legend()

        # 重みテキスト表示
        self.weight_text = self.fig.text(0.5, 0.95, "", ha='center', va='bottom', fontsize=12, fontweight='bold')
        self.update_weight_text(weights)

        # スライダー用フレーム（スクロール可能）
        self.slider_frame = ttk.Frame(self)
        self.slider_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.create_scrollable_sliders()

    def update_weight_text(self, weights):
        wt_text = "Weights: " + ", ".join([f"{w:.1f}" for w in weights])
        self.weight_text.set_text(wt_text)

    def create_scrollable_sliders(self):
        # Canvas + scrollbar setup
        canvas = tk.Canvas(self.slider_frame, width=500)
        scrollbar = ttk.Scrollbar(self.slider_frame, orient="vertical", command=canvas.yview)
        self.sliders_container = ttk.Frame(canvas)

        self.sliders_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.sliders_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # スライダーリスト
        self.sliders_x = []
        self.sliders_y = []
        self.sliders_w = []

        # Slider間隔調整用
        slider_height = 40 # px
        padding_y = 30

        # 各制御点ごとにX,Y,Wスライダーを作成
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
            frame_w.pack(fill=tk.X, padx=5)
            lbl_w = ttk.Label(frame_w, text=f"W{i}")
            lbl_w.pack(side=tk.LEFT)
            slider_w = ttk.Scale(frame_w, from_=0.1, to=20.0, orient=tk.HORIZONTAL, length=400)
            slider_w.set(w)
            slider_w.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=5)
            self.sliders_w.append(slider_w)

        # スライダーの値変更イベントをまとめてバインド
        def on_slider_change(event):
            self.update_curve()

        for slider in self.sliders_x + self.sliders_y + self.sliders_w:
            slider.bind("<ButtonRelease-1>", on_slider_change)
            slider.bind("<B1-Motion>", on_slider_change)

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

if __name__ == "__main__":
    app = NURBSApp()
    app.mainloop()











