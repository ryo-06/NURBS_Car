import matplotlib.pyplot as plt #グラフを描くライブラリ
from matplotlib.widgets import Slider #スライダーウィジェットを使うためのもの
from geomdl import NURBS #NURBS曲線を扱うライブラリ

# 初期コントロールポイント(制御点)
ctrlpts = [[0, 0], [1, 2], [2, 0], [4, 4]]

# NURBS 曲線の作成
curve = NURBS.Curve() #NURBS曲線オブジェクトの作成
curve.degree = 3 #曲線の次数
curve.ctrlpts = ctrlpts 
curve.knotvector = [0, 0, 0, 0, 1, 1, 1, 1] #ノットベクトル
curve.delta = 0.01 #小さいほど曲線は滑らか

# スライダーが動かされた時に呼ばれる関数
def update_curve(val):
    for i in range(len(ctrlpts)):
        ctrlpts[i][0] = sliders_x[i].val
        ctrlpts[i][1] = sliders_y[i].val
    curve.ctrlpts = ctrlpts #制御点の再設定
    curve.evaluate() #曲線の再計算
    curve_plot.set_xdata([pt[0] for pt in curve.evalpts])
    curve_plot.set_ydata([pt[1] for pt in curve.evalpts])
    fig.canvas.draw_idle() #再描画

# プロット作成
fig, ax = plt.subplots() #グラフウィンドウの準備
plt.subplots_adjust(left=0.25, bottom=0.25) #スライダーを表示するために余白を確保
curve.evaluate() #曲線の計算
curve_plot, = plt.plot([pt[0] for pt in curve.evalpts], [pt[1] for pt in curve.evalpts], label='NURBS Curve')
plt.scatter([pt[0] for pt in ctrlpts], [pt[1] for pt in ctrlpts], color='red', label='Control Points')
plt.legend() #ラベルの表示

# スライダー作成
sliders_x = []
sliders_y = []
for i in range(len(ctrlpts)):
    ax_slider_x = plt.axes([0.25, 0.1 + i*0.05, 0.65, 0.03]) #plt.axes([左, 下, 幅, 高さ])
    ax_slider_y = plt.axes([0.25, 0.15 + i*0.05, 0.65, 0.03])
    slider_x = Slider(ax_slider_x, f'X{i}', -5.0, 5.0, valinit=ctrlpts[i][0]) #スライダーの作成(範囲は-5.0 ~ 5.0)
    slider_y = Slider(ax_slider_y, f'Y{i}', -5.0, 5.0, valinit=ctrlpts[i][1])
    slider_x.on_changed(update_curve) #スライダーが動いたとき、update_curve()が呼ばれて曲線が更新
    slider_y.on_changed(update_curve)
    sliders_x.append(slider_x) #リストにスライダーを保存
    sliders_y.append(slider_y)

plt.show() #スライダーや曲線の表示