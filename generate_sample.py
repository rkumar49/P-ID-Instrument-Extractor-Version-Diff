"""
Generates a synthetic CAD-style drawing of a sheet metal bracket
with dimensions, hole callouts, radius, and a title block.
Output: data/sample_bracket.png
"""
import os
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Arc, FancyArrowPatch
import matplotlib.patheffects as pe
import numpy as np

os.makedirs("data", exist_ok=True)

fig, ax = plt.subplots(figsize=(11, 8.5), dpi=150)
ax.set_xlim(0, 1100)
ax.set_ylim(0, 850)
ax.set_aspect('equal')
ax.axis('off')
fig.patch.set_facecolor('white')

# ---------- helper: dimension line with arrows + text ----------
def dim_line(x1, y1, x2, y2, label, offset=0, text_offset=0,
             horizontal=True, fontsize=11, color='black'):
    # main line
    ax.plot([x1, x2], [y1, y2], color=color, lw=1.0)
    # arrowheads (simple)
    if horizontal:
        ax.annotate("", xy=(x1, y1), xytext=(x1+15, y1),
                    arrowprops=dict(arrowstyle='-|>', color=color, lw=1))
        ax.annotate("", xy=(x2, y2), xytext=(x2-15, y2),
                    arrowprops=dict(arrowstyle='-|>', color=color, lw=1))
        ax.text((x1+x2)/2, y1 + text_offset, label,
                ha='center', va='bottom', fontsize=fontsize)
    else:
        ax.annotate("", xy=(x1, y1), xytext=(x1, y1+15),
                    arrowprops=dict(arrowstyle='-|>', color=color, lw=1))
        ax.annotate("", xy=(x2, y2), xytext=(x2, y2-15),
                    arrowprops=dict(arrowstyle='-|>', color=color, lw=1))
        ax.text(x1 + text_offset, (y1+y2)/2, label,
                ha='left', va='center', fontsize=fontsize, rotation=90)

def extension_line(x1, y1, x2, y2, color='black'):
    ax.plot([x1, x2], [y1, y2], color=color, lw=0.7, ls='-')

# ---------- main part outline ----------
# A rectangular bracket 250 x 150 with a rounded corner (R10)
ox, oy = 200, 300          # origin (bottom-left)
W, H = 250, 150
R = 10                     # corner radius

# draw outline as path with rounded top-right corner
theta = np.linspace(0, np.pi/2, 50)
# bottom edge
ax.plot([ox, ox+W], [oy, oy], 'k-', lw=2)
# right edge up to start of radius
ax.plot([ox+W, ox+W], [oy, oy+H-R], 'k-', lw=2)
# rounded corner
arc_x = ox + W - R + R*np.cos(theta)
arc_y = oy + H - R + R*np.sin(theta)
ax.plot(arc_x, arc_y, 'k-', lw=2)
# top edge
ax.plot([ox+W-R, ox], [oy+H, oy+H], 'k-', lw=2)
# left edge
ax.plot([ox, ox], [oy+H, oy], 'k-', lw=2)

# ---------- holes ----------
# 4 corner holes Ø12, one central hole Ø25
hole_r = 6
corner_inset = 25
holes = [
    (ox+corner_inset,       oy+corner_inset),
    (ox+W-corner_inset,     oy+corner_inset),
    (ox+corner_inset,       oy+H-corner_inset),
    (ox+W-corner_inset,     oy+H-corner_inset),
]
for (hx, hy) in holes:
    ax.add_patch(Circle((hx, hy), hole_r, fill=False, ec='black', lw=1.5))
    # centerlines
    ax.plot([hx-10, hx+10], [hy, hy], 'k-.', lw=0.5)
    ax.plot([hx, hx], [hy-10, hy+10], 'k-.', lw=0.5)

# central hole
ax.add_patch(Circle((ox+W/2, oy+H/2), 12.5, fill=False, ec='black', lw=1.5))
ax.plot([ox+W/2-20, ox+W/2+20], [oy+H/2, oy+H/2], 'k-.', lw=0.5)
ax.plot([ox+W/2, ox+W/2], [oy+H/2-20, oy+H/2+20], 'k-.', lw=0.5)

# ---------- dimensions ----------
# overall width (below part)
extension_line(ox, oy-5, ox, oy-40)
extension_line(ox+W, oy-5, ox+W, oy-40)
dim_line(ox, oy-35, ox+W, oy-35, "250", text_offset=5)

# overall height (left of part)
extension_line(ox-5, oy, ox-40, oy)
extension_line(ox-5, oy+H, ox-40, oy+H)
dim_line(ox-35, oy, ox-35, oy+H, "150", text_offset=-8, horizontal=False)

# hole spacing horizontal (top)
extension_line(holes[0][0], oy+H+5, holes[0][0], oy+H+40)
extension_line(holes[1][0], oy+H+5, holes[1][0], oy+H+40)
dim_line(holes[0][0], oy+H+35, holes[1][0], oy+H+35, "200", text_offset=5)

# hole diameter callout (leader line)
ax.annotate("", xy=(holes[0][0]+hole_r*0.7, holes[0][1]+hole_r*0.7),
            xytext=(ox-60, oy-80),
            arrowprops=dict(arrowstyle='-', color='black', lw=1))
ax.plot([ox-60, ox-60], [oy-80, oy-100], 'k-', lw=1)
ax.text(ox-60, oy-115, "4x \u2300 12", fontsize=12, ha='center')

# central hole callout
ax.annotate("", xy=(ox+W/2+12.5, oy+H/2),
            xytext=(ox+W+80, oy+H/2+60),
            arrowprops=dict(arrowstyle='-', color='black', lw=1))
ax.plot([ox+W+80, ox+W+80], [oy+H/2+60, oy+H/2+80], 'k-', lw=1)
ax.text(ox+W+80, oy+H/2+90, "\u2300 25", fontsize=12, ha='center')

# radius callout
ax.annotate("", xy=(ox+W-R*0.3, oy+H-R*0.3),
            xytext=(ox+W+70, oy+H+70),
            arrowprops=dict(arrowstyle='-', color='black', lw=1))
ax.text(ox+W+75, oy+H+75, "R10", fontsize=12, ha='left')

# thickness note
ax.text(ox+W+30, oy+20, "THK = 2 mm", fontsize=11, ha='left', style='italic')

# material note
ax.text(ox+W+30, oy-5, "MATERIAL: MILD STEEL", fontsize=10, ha='left')

# ---------- title block ----------
tb_x, tb_y, tb_w, tb_h = 700, 60, 380, 130
ax.add_patch(Rectangle((tb_x, tb_y), tb_w, tb_h,
                       fill=False, ec='black', lw=1.5))
ax.plot([tb_x, tb_x+tb_w], [tb_y+40, tb_y+40], 'k-', lw=1)
ax.plot([tb_x, tb_x+tb_w], [tb_y+85, tb_y+85], 'k-', lw=1)
ax.plot([tb_x+180, tb_x+180], [tb_y, tb_y+tb_h], 'k-', lw=1)

ax.text(tb_x+10, tb_y+105, "PART: BRACKET-001", fontsize=12, weight='bold')
ax.text(tb_x+10, tb_y+65, "DRAWN BY: ATA ENGINEERING", fontsize=10)
ax.text(tb_x+10, tb_y+20, "SCALE: 1:1     UNITS: mm", fontsize=10)
ax.text(tb_x+190, tb_y+65, "REV: A", fontsize=10)
ax.text(tb_x+190, tb_y+20, "DATE: 2026-01-15", fontsize=10)

# ---------- sheet border ----------
ax.add_patch(Rectangle((20, 20), 1060, 810, fill=False, ec='black', lw=1))
ax.text(550, 835, "SAMPLE SHEET METAL BRACKET — DIMENSION DETECTION TEST",
        fontsize=13, weight='bold', ha='center')

plt.savefig("data/sample_bracket.png", dpi=150,
            bbox_inches='tight', facecolor='white')
print("✅ Saved: data/sample_bracket.png")