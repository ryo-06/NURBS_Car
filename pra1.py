import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import matplotlib.patches as patches

class MultiCircleApp:
    def __init__(self, master):
        self.master = master
        self.master.title("複数の円")
        self.master.geometry("600x700")

        self.fig, self.ax = plt.subplots(figsize=(5,5))
        self.ax.set_xlim(-10, 10)
        self.ax.set_ylim(-10, 10)
        self.ax.set_aspect('equal')

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.master)
        self.canvas.get_tk_widget().pack()

        frame = tk.Frame(master)
        frame.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(frame)
        scrollbar = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.create_window((0,0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.circles = []
        self.circle_data = [(0,0,1), (3,3,1), (-4,2,1)]

        for x, y, r in self.circle_data:
            circle = patches.Circle((x, y), radius=r, color='skyblue')
            self.ax.add_patch(circle)
            self.circles.append(circle)

        self.sliders_x = []
        self.sliders_y = []
        self.sliders_r = []

        for i in range(len(self.circles)):
            tk.Label(self.scrollable_frame, text=f"Circle{i}").pack()

            sx = tk.Scale(self.scrollable_frame, from_=-10, to=10, resolution=0.1, orient=tk.HORIZONTAL, label=f"x{i}", command=lambda val, idx=i: self.update_circle(idx))
            sx.set(self.circle_data[i][0])
            sx.pack()
            self.sliders_x.append(sx)

            sy=tk.Scale(self.scrollable_frame, from_=-10, to=10, resolution=0.1, orient=tk.HORIZONTAL, label=f"y{i}", command=lambda val, idx=i: self.update_circle(idx))
            sy.set(self.circle_data[i][1])
            sy.pack()
            self.sliders_y.append(sy)

            sr = tk.Scale(self.scrollable_frame, from_=0.1, to=5, resolution=0.1, orient=tk.HORIZONTAL, label=f"radius{i}", command=lambda val, idx=i: self.update_circle(idx))
            sr.set(self.circle_data[i][2])
            sr.pack()
            self.sliders_r.append(sr)

            self.canvas.draw_idle()

    def update_circle(self, idx):
        x = self.sliders_x[idx].get()
        y = self.sliders_y[idx].get()
        r = self.sliders_r[idx].get()

        self.circles[idx].center = (x, y)
        self.circles[idx].radius = r
        self.canvas.draw_idle()

if __name__ == "__main__":
    root = tk.Tk()
    app = MultiCircleApp(root)
    root.mainloop()



