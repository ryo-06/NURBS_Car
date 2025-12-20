import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from geomdl import NURBS
from geomdl import knotvector
import matplotlib.image as mpimg

CAR_MODELS = {
    "Kei car": {
        "ctrlpts": [[-0.5, 0], [-0.5, 2.0], [-0.2, 2.75], [1.5, 3.0], [2.6, 4.7], [3.5, 5.0], [6.5, 5.0], [9.0, 5.0], [9.75, 4.0], [9.85, 1.58], [10.1, 1.25], [10.0, 0]],
        "weights": [1.0, 2.0, 2.0, 5.0, 5.0, 2.0, 1.0, 7.0, 12.5, 1.0, 1.0, 1.0],
        "tire_coords": [(0.85, 0.1), (8.5, 0.1)],
        "ground_line": [-0.5, 10.0, 0.0],
        "bg_image": "kei_car.jpg"
    },
    "Compact": {
        "ctrlpts": [[-0.6, -0.2], [-0.8, 2.0], [0.6, 3.2], [1.9, 3.4], [3.8, 4.6], [6.6, 4.9], [10.0, 4.6], [9.8, 3.9], [10.3, 2.0], [10.6, 1.2], [10.3, -0.2]],
        "weights": [1.0, 6.0, 3.0, 5.0, 5.0, 6.0, 5.0, 3.0, 2.0, 1.0, 1.0],
        "tire_coords": [(0.85, -0.2), (8.8, -0.2)],
        "ground_line": [-0.6, 10.3, -0.2],
        "bg_image": "compact_car.jpg"
    },
    "SUV": {
        "ctrlpts": [[-0.1, -0.5], [-0.1, 2.0], [1.5, 2.4], [2.8, 2.7], [4.0, 4.0], [4.8, 4.3], [7.0, 4.4], [9.8, 3.8], [9.4, 3.4], [10.0, 2.4], [10.0, 0.2], [9.2, -0.5]],
        "weights": [1.0, 5.0, 1.8, 4.4, 3.9, 2.9, 2.3, 18.5, 28.8, 28.8, 22.5, 1.0],
        "tire_coords": [(1.8, -0.5), (8.1, -0.5)],
        "ground_line": [-0.1, 9.2, -0.5],
        "bg_image": "SUV.jpg"
    },
    "Sedan": {
        "ctrlpts": [[-0.35, -0.2], [-0.4, 1.3], [-0.2, 2.1], [1.2, 3.0], [2.5, 3.3], [4.0, 4.8], [7.2, 4.8], [9.0, 3.4], [9.8, 3.5], [9.9, 2.0], [10.05, 1.3], [9.95, -0.2]],
        "weights": [1.0, 3.4, 4.4, 4.5, 25.6, 100.0, 100.0, 21.9, 14.3, 1.0, 3.1, 1.0],
        "tire_coords": [(1.75, -0.2), (8.0, -0.2)],
        "ground_line": [-0.35, 9.95, -0.2],
        "bg_image": "sedan2.jpg"
    }
}

class NURBSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NURBS Car Editor")
        self.geometry("1300x900")
        self.selected_model = tk.StringVar(value="Kei car")

        model_menu = ttk.OptionMenu(
            self,
            self.selected_model,
            self.selected_model.get(),
            *CAR_MODELS.keys(),
            command=self.load_model
        )
        model_menu.pack(side=tk.TOP, pady=10)

        self.fig, self.ax = plt.subplots(figsize=(10, 7))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.slider_frame = ttk.Frame(self)
        self.slider_frame.pack(side=tk.RIGHT, fill=tk.Y)

        canvas = tk.Canvas(self.slider_frame)
        scrollbar = ttk.Scrollbar(self.slider_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self.slider_canvas = canvas

        self.alpha_slider = tk.Scale(self.slider_frame, from_=0, to=1.0, resolution=0.05, orient=tk.HORIZONTAL, label="Fill Opacity")
        self.alpha_slider.set(0.3)
        self.alpha_slider.pack(pady=(0, 10))
        self.alpha_slider.bind("<B1-Motion>", self.update_curve)
        self.alpha_slider.bind("<ButtonRelease-1>", self.update_curve)

        self.load_model(self.selected_model.get())

    def load_model(self, model_name):
        self.model_data = CAR_MODELS[model_name]
        self.ctrlpts = self.model_data["ctrlpts"]
        self.weights = self.model_data["weights"]

        self.curve = NURBS.Curve()
        self.curve.degree = 3
        self.curve.ctrlpts = self.ctrlpts
        self.curve.weights = self.weights
        self.curve.knotvector = knotvector.generate(self.curve.degree, len(self.ctrlpts))
        self.curve.delta = 0.01
        self.curve.evaluate()

        self.ax.clear()
        self.draw_background()

        self.curve_plot, = self.ax.plot(*zip(*self.curve.evalpts), label="NURBS Curve")
        self.scatter_plot = self.ax.scatter(*zip(*self.ctrlpts), color='black', label="Control Points")

        self.filled_patch = Polygon(self.curve.evalpts + [self.ctrlpts[-1], self.ctrlpts[0]], closed=True, color='black', alpha=self.alpha_slider.get())
        self.ax.add_patch(self.filled_patch)

        self.ax.legend()
        self.ax.set_xlim(-3, 13)
        self.ax.set_ylim(-3, 8)
        self.ax.set_aspect('equal')
        self.canvas.draw_idle()

        self.create_sliders()

    def draw_background(self):
        try:
            bg = mpimg.imread(self.model_data["bg_image"])
            self.ax.imshow(bg, extent=[-1, 11, -1.5, 6], aspect='auto', alpha=0.2)
        except Exception as e:
            print("背景画像読み込みエラー:", e)

        for (x, y) in self.model_data["tire_coords"]:
            self.ax.add_patch(plt.Circle((x, y), 0.9, fill=True, color='black'))

        x0, x1, y = self.model_data["ground_line"]
        self.ax.plot([x0, x1], [y, y], linestyle='-', color='black', linewidth=1)

    def create_sliders(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.sliders_x, self.sliders_y, self.sliders_w = [], [], []
        self.weight_labels = []

        for i, (pt, w) in enumerate(zip(self.ctrlpts, self.weights)):
            ttk.Label(self.scrollable_frame, text=f"Control Point {i}").pack(pady=(10, 0))

            for val, label, lst in zip(pt, ["X", "Y"], [self.sliders_x, self.sliders_y]):
                f = ttk.Frame(self.scrollable_frame)
                f.pack()
                ttk.Label(f, text=label).pack(side=tk.LEFT)
                s = tk.Scale(f, from_=-5, to=15, resolution=0.1, orient=tk.HORIZONTAL, length=300)
                s.set(val)
                s.pack(side=tk.LEFT)
                s.bind("<B1-Motion>", self.update_curve)
                s.bind("<ButtonRelease-1>", self.update_curve)
                lst.append(s)

            # Weightスライダーとラベル
            f = ttk.Frame(self.scrollable_frame)
            f.pack()
            ttk.Label(f, text="W").pack(side=tk.LEFT)
            sw = tk.Scale(f, from_=0.1, to=100, resolution=0.1, orient=tk.HORIZONTAL, length=300)
            sw.set(w)
            sw.pack(side=tk.LEFT)

            lbl = ttk.Label(f, text=f"{w:.1f}")
            lbl.pack(side=tk.LEFT, padx=5)
            self.weight_labels.append(lbl)

            sw.bind("<B1-Motion>", self.update_curve)
            sw.bind("<ButtonRelease-1>", self.update_curve)
            self.sliders_w.append(sw)

    def update_curve(self, event=None):
        new_ctrlpts = [[self.sliders_x[i].get(), self.sliders_y[i].get()] for i in range(len(self.sliders_x))]
        new_weights = [self.sliders_w[i].get() for i in range(len(self.sliders_w))]

        self.curve.ctrlpts = new_ctrlpts
        self.curve.weights = new_weights
        self.curve.knotvector = knotvector.generate(self.curve.degree, len(new_ctrlpts))
        self.curve.evaluate()

        self.curve_plot.set_xdata([pt[0] for pt in self.curve.evalpts])
        self.curve_plot.set_ydata([pt[1] for pt in self.curve.evalpts])
        self.scatter_plot.set_offsets(new_ctrlpts)

        if hasattr(self, 'filled_patch'):
            self.filled_patch.remove()
        self.filled_patch = Polygon(self.curve.evalpts + [new_ctrlpts[-1], new_ctrlpts[0]], closed=True, color='black', alpha=self.alpha_slider.get())
        self.ax.add_patch(self.filled_patch)

        # 重みラベル更新
        for i, lbl in enumerate(self.weight_labels):
            lbl.config(text=f"{self.sliders_w[i].get():.1f}")

        self.canvas.draw_idle()


if __name__ == "__main__":
    app = NURBSApp()
    app.mainloop()


