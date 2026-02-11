import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
from geomdl import NURBS, knotvector
import json
import ast
import os
import matplotlib.gridspec as gridspec
import platform

# === Settings ===
CSV_FILE = "car_data.csv"
OUTPUT_FILE = "summary_english_aligned.png"

# === ID Specification ===
TARGET_IDS = {
    "Base": [137, 138, 139, 140, 141, 142],
    "Cute": [10, 128, 108],
    "Cool": [39, 60, 112],
    "Fast": [1, 15, 131],
    "Familiar": [22, 45, 96],
    "Sturdy": [24, 57, 96], 
    "Luxury": [27, 76, 102]
}

ROW2_BLOCKS = ["Cute", "Cool", "Fast"]
ROW3_BLOCKS = ["Familiar", "Sturdy", "Luxury"]

# Labels (English)
LABELS = {
    "Base": "Initial Shapes",
    "Cute": "Cute",
    "Cool": "Cool",
    "Fast": "Fast",
    "Familiar": "Familiar",
    "Sturdy": "Sturdy",
    "Luxury": "Luxury"
}

# Tire Positions (Keys updated to English)
CAR_MODELS = {
    "Kei Car": { "tire": [(0.85, 0.1), (8.5, 0.1)] },
    "Compact": { "tire": [(0.85, -0.2), (8.8, -0.2)] },
    "SUV":     { "tire": [(1.8, -0.5), (8.1, -0.5)] },
    "Sedan":   { "tire": [(1.6, 1.0), (8.2, 1.0)] },
    "Minivan": { "tire": [(1.6, 0.2), (8.3, 0.2)] },
    "Coupe":   { "tire": [(1.8, 1.0), (8.0, 1.0)] }
}

# === Font Settings ===
# English only, so standard sans-serif is sufficient, 
# but keeping system font logic just in case to maintain style.
plt.rcParams['font.family'] = 'sans-serif'

# === Data Loading ===
try:
    df = pd.read_csv(CSV_FILE, header=None, encoding='utf-8-sig', on_bad_lines='skip')
except:
    df = pd.read_csv(CSV_FILE, header=None, encoding='cp932', on_bad_lines='skip')

# === Model Name Helper (Returns English) ===
def get_model_name(row_list, ctrl_idx):
    model_raw = row_list[ctrl_idx - 1]
    m = str(model_raw)
    # Detect Japanese or English keywords and return English names
    if "Light" in m or "軽" in m: return "Kei Car"
    elif "Compact" in m or "コンパクト" in m: return "Compact"
    elif "SUV" in m: return "SUV"
    elif "Sedan" in m or "セダン" in m: return "Sedan"
    elif "Minivan" in m or "ミニバン" in m: return "Minivan"
    elif "Coupe" in m or "coupe" in m or "クー" in m: return "Coupe"
    return "Unknown"

# === Drawing Function ===
def draw_car_on_ax(ax, row_data, title=None, is_base=False):
    try:
        row_list = [str(x) for x in row_data.tolist()]
        ctrl_idx = -1
        for i, val in enumerate(row_list):
            if val.strip().startswith('[['):
                ctrl_idx = i
                break
        
        if ctrl_idx == -1:
            ax.axis('off')
            return

        ctrl_raw = row_list[ctrl_idx]
        weight_raw = row_list[ctrl_idx + 1]
        model_name = get_model_name(row_list, ctrl_idx)

        try:
            ctrlpts = json.loads(ctrl_raw)
            weights = json.loads(weight_raw)
        except:
            ctrlpts = ast.literal_eval(ctrl_raw)
            weights = ast.literal_eval(weight_raw)

        # === Alignment Logic ===
        tire_info = CAR_MODELS.get(model_name, {}).get("tire", [])
        
        offset_y = 0.0
        if len(tire_info) > 0:
            current_tire_y = tire_info[0][1]
            offset_y = -current_tire_y

        adjusted_ctrlpts = []
        for pt in ctrlpts:
            new_pt = list(pt)
            new_pt[1] += offset_y
            adjusted_ctrlpts.append(new_pt)

        curve = NURBS.Curve()
        curve.degree = 3
        curve.ctrlpts = adjusted_ctrlpts
        curve.weights = weights
        curve.knotvector = knotvector.generate(curve.degree, len(adjusted_ctrlpts))
        curve.delta = 0.01
        curve.evaluate()

        if len(tire_info) > 0:
            for t in tire_info:
                ax.add_patch(Circle((t[0], t[1] + offset_y), 0.9, color='black', zorder=10))

        poly_pts = curve.evalpts + [adjusted_ctrlpts[-1], adjusted_ctrlpts[0]]
        ax.add_patch(Polygon(poly_pts, closed=True, color='black', alpha=1.0, zorder=10))

        ax.set_aspect('equal')
        
        # Adjust View Limits
        ax.set_xlim(-2, 12) 
        ax.set_ylim(-3, 10) 
        
        ax.axis('off')
        ax.patch.set_alpha(0)
        
        if title:
            # Title is now English Model Name
            ax.set_title(model_name, fontsize=10, pad=-10, color='black', y=1.0)

    except Exception as e:
        ax.axis('off')

# === Layout Creation ===
fig = plt.figure(figsize=(15, 11))
gs = gridspec.GridSpec(3, 18, figure=fig, wspace=0.0, hspace=0.4)

def draw_block_frame(fig, gs_slice, title, color='black', is_base=False):
    ax_frame = fig.add_subplot(gs_slice)
    ax_frame.set_xticks([])
    ax_frame.set_yticks([])
    ax_frame.patch.set_alpha(0)
    
    for spine in ax_frame.spines.values():
        spine.set_visible(True)
        spine.set_color('black')
        spine.set_linewidth(1)
    
    font_weight = 'bold'
    font_size = 14
    
    # Title Position
    ax_frame.text(0.5, 1.02, title, 
                  ha='center', va='bottom',
                  fontsize=font_size, fontweight=font_weight, color=color,
                  transform=ax_frame.transAxes)
    
    ax_frame.set_zorder(0)
    return ax_frame

# --- 1. Base Row ---
draw_block_frame(fig, gs[0, :], LABELS["Base"], color='black', is_base=True)

for i, car_id in enumerate(TARGET_IDS["Base"]):
    ax = fig.add_subplot(gs[0, i*3 : (i+1)*3]) 
    ax.set_zorder(10)
    if car_id - 1 < len(df):
        row_data = df.iloc[car_id - 1]
        draw_car_on_ax(ax, row_data, title=True, is_base=True)
    else:
        ax.axis('off')

# --- 2. Second Row ---
for block_idx, adj_key in enumerate(ROW2_BLOCKS):
    start_col = block_idx * 6
    end_col = start_col + 6
    draw_block_frame(fig, gs[1, start_col:end_col], LABELS[adj_key], color='red')
    
    ids = TARGET_IDS[adj_key]
    for i in range(3): 
        ax = fig.add_subplot(gs[1, start_col + i*2 : start_col + (i+1)*2])
        ax.set_zorder(10)
        if i < len(ids):
            car_id = ids[i]
            if car_id - 1 < len(df):
                row_data = df.iloc[car_id - 1]
                draw_car_on_ax(ax, row_data, title=True)
            else:
                ax.axis('off')
        else:
            ax.axis('off')

# --- 3. Third Row ---
for block_idx, adj_key in enumerate(ROW3_BLOCKS):
    start_col = block_idx * 6
    end_col = start_col + 6
    draw_block_frame(fig, gs[2, start_col:end_col], LABELS[adj_key], color='red')
    
    ids = TARGET_IDS[adj_key]
    if not ids: 
         pass
    else:
        for i in range(3): 
            ax = fig.add_subplot(gs[2, start_col + i*2 : start_col + (i+1)*2])
            ax.set_zorder(10)
            if i < len(ids):
                car_id = ids[i]
                if car_id - 1 < len(df):
                    row_data = df.iloc[car_id - 1]
                    draw_car_on_ax(ax, row_data, title=True)
                else:
                    ax.axis('off')
            else:
                ax.axis('off')

plt.tight_layout(rect=[0.01, 0.01, 0.99, 0.93])
plt.savefig(OUTPUT_FILE, bbox_inches='tight')
plt.close()

print(f"✅ Created: {OUTPUT_FILE}")