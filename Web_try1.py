import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from geomdl import NURBS, knotvector

Web_NURBS = {
    "NURBS":{
        "ctrlpts":[[-0.5, 0], [-0.4, 2.0], [-0.1, 2.75], [1.0, 4.0], [1.5, 4.5]],
        "weights":[1.0, 2.0, 3.0, 4.0, 3.0]
    }
}

data = Web_NURBS["NURBS"]
ctrlpts = []
weights = []

st.write("### 制御点と重みの調整")
for i, (pt, initial_weight) in enumerate(zip(data["ctrlpts"], data["weights"])):
    x_val = pt[0]
    y_val = pt[1]
    x = st.slider(f"X{i}", -5.0, 15.0, float(x_val), 0.1)
    y = st.slider(f"Y{i}", -5.0, 15.0, float(y_val), 0.1)
    weight = st.slider(f"W{i}", 0.1, 100.0, float(initial_weight), 0.1)
    ctrlpts.append([x, y])
    weights.append(weight)

if len(ctrlpts) >= 4:
    curve = NURBS.Curve()
    curve.degree = 3
    curve.ctrlpts = ctrlpts
    curve.weights = weights
    curve.knotvector = knotvector.generate(curve.degree, len(ctrlpts))
    curve.evaluate()

    fig, ax = plt.subplots()
    ax.plot(*zip(*curve.evalpts), label="NURBS")
    ax.scatter(*zip(*ctrlpts), color='black', label="Control Points")
    ax.set_aspect('equal')
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)
else:
    st.warning("制御点の数は 4 点以上にしてください（degree + 1）")