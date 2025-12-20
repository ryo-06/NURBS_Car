import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from geomdl import NURBS
from seaborn import scatterplot

# 初期コントロールポイント
ctrlpts = [[0, 0], [1, 2], [2, 0], [4, 4]]
weights = [3, 4, 2, 5]

# NURBS 曲線の作成
curve = NURBS.Curve()
curve.degree = 3
curve.ctrlpts = ctrlpts
curve.weights = weights
curve.knotvector = [0, 0, 0, 0, 1, 1, 1, 1]
curve.delta = 0.01
curve.evaluate()

# 図とレイアウトの設定
fig = plt.figure(figsize=(12, 6))  # 幅広めのキャンバス
gs = fig.add_gridspec(1, 2, width_ratios=[2, 1])  # 左2:右1 の比率で分割

# 左側：グラフ表示
ax_plot = fig.add_subplot(gs[0, 0])
curve_plot, = ax_plot.plot([pt[0] for pt in curve.evalpts], [pt[1] for pt in curve.evalpts], label='NURBS Curve')
plt.scatter([pt[0] for pt in ctrlpts], [pt[1] for pt in ctrlpts], color='red', label='Control Points')
ax_plot.legend()
ax_plot.set_xlim(-6, 6)
ax_plot.set_ylim(-6, 6)
ax_plot.set_title("NURBS Curve")

# 右側：スライダー領域
slider_axes = []
sliders_x = []
sliders_y = []
slider_area = gs[0, 1]  # 右側の領域

# スライダーを配置するための基準座標（右パネル内）
slider_height = 0.03
slider_spacing = 0.1

for i in range(len(ctrlpts)):
    ypos = 0.85 - i * 2 * slider_spacing  # スライダーの縦位置

    # Xスライダー
    ax_slider_x = fig.add_axes([0.68, ypos, 0.25, slider_height])
    slider_x = Slider(ax_slider_x, f'X{i}', -5.0, 5.0, valinit=ctrlpts[i][0])
    sliders_x.append(slider_x)

    # Yスライダー
    ax_slider_y = fig.add_axes([0.68, ypos - slider_spacing, 0.25, slider_height])
    slider_y = Slider(ax_slider_y, f'Y{i}', -5.0, 5.0, valinit=ctrlpts[i][1])
    sliders_y.append(slider_y)

# スライダー動作：曲線を更新
def update_curve(val):
    for i in range(len(ctrlpts)):
        ctrlpts[i][0] = sliders_x[i].val
        ctrlpts[i][1] = sliders_y[i].val
    curve.ctrlpts = ctrlpts
    curve.evaluate()
    curve_plot.set_xdata([pt[0] for pt in curve.evalpts])
    curve_plot.set_ydata([pt[1] for pt in curve.evalpts])
    scatterplot.set_offsets(ctrlpts)
    fig.canvas.draw_idle()

# 各スライダーにコールバックを設定
for sx, sy in zip(sliders_x, sliders_y):
    sx.on_changed(update_curve)
    sy.on_changed(update_curve)

plt.show()
