import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from geomdl import NURBS
from geomdl import knotvector

ctrlpts = [   [0, -0.75], [-0.5, -0.48], [-0.9, 0], [-0.95, 0.4], [-1, 1], [-0.25, 2.55],  
    [2, 3.5], [3, 4.2], [4, 5], [5.5, 5.5], [7, 5.5], [9.5, 5.2],
    [10, 4], [10.65, 3.25],
    [10.8, 2.5], [11, 1.5], [10.8, 0], [10.3, -0.75]
    ]

weights = [ 1.0, 1.0, 1.0, 1.0, 10.0,
    20.0, 10.0, 10.0, 10.0,
    10.0, 10.0, 10.0, 1.0,
    1.0, 1.0, 10.0, 10.0, 1.0]

def make_curve(ctrlpts, weights):
    curve = NURBS.Curve()
    curve.degree = 3
    curve.ctrlpts = ctrlpts
    curve.weights =  weights
    curve.knotvector = knotvector.generate(curve.degree, len(ctrlpts))
    curve.delta = 0.01
    curve.evaluate()
    return curve

class NURBSApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Practice")
        self.geometry("1200x800")

        self.fig, self.ax = plt.subplots(figsize=(10, 7))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=1)

        self.ax.set_facecolor('green')
        
        self.curve = make_curve(ctrlpts, weights)
        self.curve_plot, = self.ax.plot(
            [pt[0] for pt in self.curve.evalpts],
            [pt[1] for pt in self.curve.evalpts],
            label = 'NURBS Curve'
        )
        self.scatter_plot = self.ax.scatter(
            [pt[0] for pt in ctrlpts],
            [pt[1] for pt in ctrlpts],
            color = 'red', label = 'ctlpts'
        )

        self.tire1 = plt.Circle((1.3, -0.8), 1.0, fill=False, color = 'blue')
        self.tire2 = plt.Circle((8.7, -0.8), 1.0, fill = False, color = 'blue')
        self.ax.add_patch(self.tire1)
        self.ax.add_patch(self.tire2)

        self.ax.plot([0, 10.3], [-0.75, -0.75], linestyle = '-', color = 'green', linewidth = 1, label = 'Under Line')

        self.ax.set_xlim(-3, 13)
        self.ax.set_ylim(-3, 8)
        self.ax.set_aspect('equal')
        self.ax.set_title("Editable")
        self.ax.xaxis.set_visible(False)
        self.ax.legend()

        self.weight_text = self.fig.text(0.5, 0.95, "", ha='center', va='bottom', fontsize=12, fontweight='bold')
        self.update_weight_text(weights)

        filled_points = self.curve.evalpts + [ctrlpts[-1], ctrlpts[0]]
        self.filled_patch = Polygon(filled_points, closed=True, color='black', alpha=0.3)
        self.ax.add_patch(self.filled_patch)

        self.slider_frame = ttk.Frame(self)
        self.slider_frame.pack(side = tk.RIGHT, fill = tk.Y)
        self.create_scrollable_sliders()

    def update_weight_text(self, weights):
            wt_text = "Weights: " + ", ".join([f"{w:.1f}" for w in weights])
            self.weight_text.set_text(wt_text)

    def create_scrollable_sliders(self):
            canvas = tk.Canvas(self.slider_frame, width = 500)
            scrollbar = ttk.Scrollbar(self.slider_frame, orient = "vertical", command = canvas.yview)
            self.sliders_container = ttk.Frame(canvas)

            self.sliders_container.bind(
                "<Configure>",
                lambda e : canvas.configure(scrollregion = canvas.bbox("all"))
            )

            canvas.create_window((0, 0), window = self.sliders_container, anchor = "nw")
            canvas.configure(yscrollcommand = scrollbar.set)
            canvas.pack(side = tk.LEFT, fill = tk.BOTH, expand = True)
            scrollbar.pack(side=tk.RIGHT, fill = tk.Y)

            
            self.sliders_x = []
            self.sliders_y = []
            self.sliders_w = []

            for i, (pt, w) in enumerate(zip(ctrlpts, weights)):
                label = ttk.Label(self.sliders_container, text = f"Control Point {i}") 
                label.pack(pady=(30, 0))

                frame_x = ttk.Frame(self.sliders_container)
                frame_x.pack(fill=tk.X, padx=5)
                slider_x = tk.Scale(frame_x, from_= -2.0, to=12.0, resolution=0.1, orient=tk.HORIZONTAL, length=400, showvalue=False)
                slider_x.set(pt[0])
                slider_x.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=5)
                self.sliders_x.append(slider_x)

                frame_y = ttk.Frame(self.sliders_container)
                frame_y.pack(fill=tk.X, padx=5)
                slider_y = tk.Scale(frame_y, from_=-4.0, to=8.0, resolution=0.1, orient=tk.HORIZONTAL, length=400, showvalue=False)
                slider_y.set(pt[1])
                slider_y.pack(fill=tk.X, expand=True, side=tk.LEFT, padx=5)
                self.sliders_y.append(slider_y)

                frame_w = ttk.Frame(self.sliders_container)
                frame_w.pack(fill=tk.X, padx=5, pady=(0, 10))
                slider_w = tk.Scale(frame_w, from_=0.1, to=20, resolution=0.1, orient=tk.HORIZONTAL, length=400, showvalue=False)
                slider_w.set(w)
                self.sliders_w.append(slider_w)

            def on_alpha_change(event):
                if hasattr(self, 'filled_patch'):
                    self.filled_patch.set_alpha(self.alpha_slider.get())
                    self.canvas.draw_idle()
            
            self.alpha_slider = tk.Scale(self.sliders_container, from_=0.0, to=1.0, resolution=0.05, orient=tk.HORIZONTAL, length=400, showvalue=True)
            self.alpha_slider.set(0.3)
            self.alpha_slider.pack(pady=(0, 20))

            self.alpha_slider.bind("<ButtonRelease-1>", on_alpha_change)
            self.alpha_slider.bind("<B1-Motion>", on_alpha_change)

            for slider in self.sliders_x + self.sliders_y + self.sliders_w:
                slider.bind("<ButtonRelease-1>", lambda e: self.update_curve())
                slider.bind("<B1-Motion>", lambda e: self.update_curve())

def update_curve(self):
            new_ctrlpts = [[sx.get(), sy.get()]for sx, sy in zip(self.sliders_x, self.sliders_y)]
            new_weights = [sw.get() for sw in self.sliders_w]

            self.curve.ctrlpts = new_ctrlpts
            self.curve.weights = new_weights
            self.curve.evaluate()

            self.curve_plot.set_xdate(pt[0] for pt in self.curve.evalpts)
            self.curve_plot.set_ydate(pt[1] for pt in self.curve.evalpts)
            self.scatter_plot.set_offsets(new_ctrlpts)
            self.update_weight_text(new_weights)

            if hasattr(self, 'filled_patch'):
                self.filled_patch.remove()

            filled_points = self.curve.evalpts + [new_ctrlpts[-1], new_ctrlpts[0]]
            self.filled_patch = Polygon(filled_points, closed=True, color='black', alpha=self.alpha_slider.get())

            self.canvas.draw_idle()

if __name__=="__main__":
    app = NURBSApp()
    app.mainloop()








