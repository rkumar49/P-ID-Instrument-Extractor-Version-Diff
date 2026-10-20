"""
Generates a COMPLEX multi-view CAD drawing of a sheet metal bracket
with tolerances, GD&T, bend lines, countersinks, section view,
and full title block — designed to stress-test OCR + parsing.
Output: data/complex_bracket.png
"""
import os
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Arc, Polygon, FancyArrow
import matplotlib.patheffects as pe
import numpy as np

os.makedirs("data", exist_ok=True)

fig, ax = plt.subplots(figsize=(16, 11), dpi=200)
ax.set_xlim(0, 1600)
ax.set_ylim(0, 1100)
ax.set_aspect('equal')
ax.axis('off')
fig.patch.set_facecolor('white')

LW_MAIN = 1.8      # visible edge
LW_HIDDEN = 0.9    # hidden line
LW_DIM = 0.8       # dimension
LW_CENTER = 0.6    # centerline
FONT_DIM = 9
FONT_NOTE = 8.5

# ============================================================
# HELPER FUNCTIONS
# ============================================================
def dim_line_h(x1, x2, y, label, tick=8, fontsize=FONT_DIM):
    """Horizontal dimension with slanted tick marks + text."""
    ax.plot([x1, x2], [y, y], 'k-', lw=LW_DIM)
    ax.plot([x1-tick/2, x1+tick/2], [y-tick/2, y+tick/2], 'k-', lw=LW_DIM)
    ax.plot([x2-tick/2, x2+tick/2], [y-tick/2, y+tick/2], 'k-', lw=LW_DIM)
    ax.text((x1+x2)/2, y+4, label, ha='center', va='bottom',
            fontsize=fontsize, bbox=dict(fc='white', ec='none', pad=1))

def dim_line_v(y1, y2, x, label, tick=8, fontsize=FONT_DIM):
    ax.plot([x, x], [y1, y2], 'k-', lw=LW_DIM)
    ax.plot([x-tick/2, x+tick/2], [y1-tick/2, y1+tick/2], 'k-', lw=LW_DIM)
    ax.plot([x-tick/2, x+tick/2], [y2-tick/2, y2+tick/2], 'k-', lw=LW_DIM)
    ax.text(x-4, (y1+y2)/2, label, ha='right', va='center',
            fontsize=fontsize, rotation=90,
            bbox=dict(fc='white', ec='none', pad=1))

def ext_line(x1, y1, x2, y2):
    ax.plot([x1, x2], [y1, y2], 'k-', lw=0.5)

def leader(x1, y1, x2, y2, text, ha='left', va='center', fontsize=FONT_DIM,
           text_offset=10):
    """Leader line with arrow at (x1,y1) pointing to feature."""
    ax.annotate("", xy=(x1, y1), xytext=(x2, y2),
                arrowprops=dict(arrowstyle='-|>', color='k', lw=0.8,
                                mutation_scale=8))
    # horizontal tail
    tail_x = x2 + (text_offset if ha == 'left' else -text_offset)
    ax.plot([x2, tail_x], [y2, y2], 'k-', lw=0.8)
    ax.text(tail_x + (4 if ha == 'left' else -4), y2, text,
            ha=ha, va='center', fontsize=fontsize,
            bbox=dict(fc='white', ec='none', pad=1))

def centerline_h(x1, x2, y):
    ax.plot([x1, x2], [y, y], 'k-.', lw=LW_CENTER,
            dashes=(12, 3, 2, 3))

def centerline_v(x, y1, y2):
    ax.plot([x, x], [y1, y2], 'k-.', lw=LW_CENTER,
            dashes=(12, 3, 2, 3))

def hidden_h(x1, x2, y):
    ax.plot([x1, x2], [y, y], 'k--', lw=LW_HIDDEN, dashes=(6, 3))

def hidden_v(x, y1, y2):
    ax.plot([x, x], [y1, y2], 'k--', lw=LW_HIDDEN, dashes=(6, 3))

def gdt_frame(x, y, symbol, tolerance, datum=None, w=45, h=22):
    """Simple GD&T feature control frame."""
    cells = 2 + (1 if datum else 0)
    cw = w if not datum else w * 0.7
    ax.add_patch(Rectangle((x, y), w + (cw * (cells-1)), h,
                           fill=False, ec='k', lw=1.0))
    if datum:
        ax.plot([x+w, x+w], [y, y+h], 'k-', lw=1.0)
        ax.plot([x+w+cw, x+w+cw], [y, y+h], 'k-', lw=1.0)
    ax.text(x+4, y+h/2, symbol, ha='left', va='center', fontsize=8)
    ax.text(x+w+4 if not datum else x+w+4, y+h/2, tolerance,
            ha='left', va='center', fontsize=8)
    if datum:
        ax.text(x+w+cw+4, y+h/2, datum, ha='left', va='center', fontsize=8)

# ============================================================
# SHEET BORDER + ZONES
# ============================================================
ax.add_patch(Rectangle((15, 15), 1570, 1070, fill=False, ec='k', lw=1.6))
# zone markers (A-E on top/bottom, 1-4 on sides)
for i, letter in enumerate(['A','B','C','D','E']):
    xx = 200 + i*280
    ax.text(xx, 1072, letter, fontsize=7, ha='center', va='bottom')
    ax.text(xx, 12, letter, fontsize=7, ha='center', va='top')
for i, num in enumerate(['1','2','3','4']):
    yy = 200 + i*230
    ax.text(10, yy, num, fontsize=7, ha='right', va='center')
    ax.text(1588, yy, num, fontsize=7, ha='left', va='center')

# ============================================================
# FRONT VIEW (main part) — top-left quadrant
# ============================================================
FX, FY = 120, 640          # front view origin (bottom-left of part)
FW, FH = 320, 200          # overall size
RAD = 15                   # corner radius

# Outer profile with rounded corners (draw as polygon approximation)
theta = np.linspace(0, np.pi/2, 30)
# bottom-left corner arc
blx = FX + RAD + RAD*np.cos(theta + np.pi)
bly = FY + RAD + RAD*np.sin(theta + np.pi)
ax.plot(blx, bly, 'k-', lw=LW_MAIN)
# bottom edge
ax.plot([FX+RAD, FX+FW-RAD], [FY, FY], 'k-', lw=LW_MAIN)
# bottom-right arc
brx = FX + FW - RAD + RAD*np.cos(theta - np.pi/2)
bry = FY + RAD + RAD*np.sin(theta - np.pi/2)
ax.plot(brx, bry, 'k-', lw=LW_MAIN)
# right edge
ax.plot([FX+FW, FX+FW], [FY+RAD, FY+FH-RAD], 'k-', lw=LW_MAIN)
# top-right arc
trx = FX + FW - RAD + RAD*np.cos(theta)
try_ = FY + FH - RAD + RAD*np.sin(theta)
ax.plot(trx, try_, 'k-', lw=LW_MAIN)
# top edge
ax.plot([FX+FW-RAD, FX+RAD], [FY+FH, FY+FH], 'k-', lw=LW_MAIN)
# top-left arc
tlx = FX + RAD + RAD*np.cos(theta + np.pi/2)
tly = FY + FH - RAD + RAD*np.sin(theta + np.pi/2)
ax.plot(tlx, tly, 'k-', lw=LW_MAIN)
# left edge
ax.plot([FX, FX], [FY+FH-RAD, FY+RAD], 'k-', lw=LW_MAIN)

# 4 corner holes Ø10 THRU
hole_r = 5
INSET = 35
holes = [
    (FX+INSET,     FY+INSET),
    (FX+FW-INSET,  FY+INSET),
    (FX+INSET,     FY+FH-INSET),
    (FX+FW-INSET,  FY+FH-INSET),
]
for hx, hy in holes:
    ax.add_patch(Circle((hx, hy), hole_r, fill=False, ec='k', lw=LW_MAIN))
    centerline_h(hx-12, hx+12, hy)
    centerline_v(hx, hy-12, hy+12)

# Central slot (obround) 60 x 20
slot_w, slot_h = 60, 20
scx, scy = FX + FW/2, FY + FH/2
ax.add_patch(Rectangle((scx-slot_w/2, scy-slot_h/2), slot_w, slot_h,
                       fill=False, ec='k', lw=LW_MAIN))
ax.add_patch(Arc((scx-slot_w/2, scy), slot_h, slot_h,
                 theta1=90, theta2=270, ec='k', lw=LW_MAIN))
ax.add_patch(Arc((scx+slot_w/2, scy), slot_h, slot_h,
                 theta1=-90, theta2=90, ec='k', lw=LW_MAIN))
centerline_h(scx-slot_w/2-12, scx+slot_w/2+12, scy)
centerline_v(scx, scy-slot_h/2-10, scy+slot_h/2+10)

# 2 countersunk holes Ø6 CSK Ø12 on right side
csk_x = FX + FW - 60
for cy in [FY + 60, FY + FH - 60]:
    ax.add_patch(Circle((csk_x, cy), 3, fill=False, ec='k', lw=LW_MAIN))
    ax.add_patch(Circle((csk_x, cy), 6, fill=False, ec='k', lw=0.7,
                        ls='--'))
    centerline_h(csk_x-10, csk_x+10, cy)
    centerline_v(csk_x, cy-10, cy+10)

# ============================================================
# FRONT VIEW DIMENSIONS
# ============================================================
# Overall width
ext_line(FX, FY-8, FX, FY-50)
ext_line(FX+FW, FY-8, FX+FW, FY-50)
dim_line_h(FX, FX+FW, FY-40, "320")

# Overall height
ext_line(FX-8, FY, FX-50, FY)
ext_line(FX-8, FY+FH, FX-50, FY+FH)
dim_line_v(FY, FY+FH, FX-40, "200")

# Hole spacing
ext_line(holes[0][0], FY-8, holes[0][0], FY-70)
ext_line(holes[1][0], FY-8, holes[1][0], FY-70)
dim_line_h(holes[0][0], holes[1][0], FY-62, "250")

# Corner radius callout
leader(FX+FW-RAD*0.3, FY+FH-RAD*0.3, FX+FW+30, FY+FH+40, "R15 (4x)",
       fontsize=FONT_DIM)

# Hole callouts
leader(holes[0][0]+hole_r*0.7, holes[0][1]+hole_r*0.7,
       FX-60, FY-90, "4x \u2300 10 THRU", ha='right')

leader(csk_x+6, FY+60+6, FX+FW+30, FY+30,
       "\u2300 6 CSK \u2300 12\n(2x)", fontsize=FONT_DIM)

# Slot callout
leader(scx+slot_w/2, scy, scx+120, scy+90,
       "SLOT 60 x 20", fontsize=FONT_DIM)

# Thickness / material notes
ax.text(FX, FY-110, "THK = 3.0 mm", fontsize=FONT_NOTE,
        style='italic', weight='bold')
ax.text(FX, FY-125, "MATERIAL: STAINLESS STEEL 304", fontsize=FONT_NOTE,
        style='italic')
ax.text(FX, FY-140, "FINISH: Brushed #4  |  DEBURR ALL EDGES",
        fontsize=FONT_NOTE, style='italic')

# ============================================================
# SIDE VIEW (right of front, showing the bend)
# ============================================================
SX, SY = 620, 640
SW, SH = 60, 200      # thickness x height
ax.plot([SX, SX+SW, SX+SW, SX], [SY, SY, SY+SH, SY+SH], 'k-', lw=LW_MAIN)
ax.plot([SX, SX+SW], [SY+SH, SY+SH], 'k-', lw=LW_MAIN)
# hidden bend line
hidden_v(SX+SW/2, SY, SY+SH)
ax.text(SX+SW/2, SY+SH+10, "SIDE VIEW", fontsize=FONT_NOTE,
        ha='center', weight='bold')

# thickness dimension
ext_line(SX-8, SY+SH, SX-25, SY+SH)
ext_line(SX+SW+8, SY+SH, SX+SW+25, SY+SH)
dim_line_h(SX, SX+SW, SY+SH+40, "3.0", fontsize=8)

# ============================================================
# SECTION A-A VIEW (bottom-left)
# ============================================================
SEC_X, SEC_Y = 120, 300
SEC_W, SEC_H = 320, 100
# Outer rect with hatch
sec_rect = Rectangle((SEC_X, SEC_Y), SEC_W, SEC_H,
                     fill=False, ec='k', lw=LW_MAIN)
ax.add_patch(sec_rect)
# Hatch lines (section indicator)
for i in np.arange(0, SEC_W+SEC_H, 12):
    x1 = SEC_X + max(0, i - SEC_H)
    y1 = SEC_Y + min(i, SEC_H)
    x2 = SEC_X + min(i, SEC_W)
    y2 = SEC_Y + max(0, i - SEC_W)
    ax.plot([x1, x2], [y1, y2], 'k-', lw=0.4)

# center hole in section
ax.plot([SEC_X+SEC_W/2-10, SEC_X+SEC_W/2+10],
        [SEC_Y+SEC_H/2, SEC_Y+SEC_H/2], 'k-', lw=LW_MAIN)
ax.plot([SEC_X+SEC_W/2-10, SEC_X+SEC_W/2+10],
        [SEC_Y+SEC_H/2-4, SEC_Y+SEC_H/2-4], 'k-', lw=LW_MAIN)
ax.plot([SEC_X+SEC_W/2-10, SEC_X+SEC_W/2-10],
        [SEC_Y+SEC_H/2-4, SEC_Y+SEC_H/2], 'k-', lw=LW_MAIN)
ax.plot([SEC_X+SEC_W/2+10, SEC_X+SEC_W/2+10],
        [SEC_Y+SEC_H/2-4, SEC_Y+SEC_H/2], 'k-', lw=LW_MAIN)

ax.text(SEC_X+SEC_W/2, SEC_Y-25, "SECTION A-A", fontsize=FONT_NOTE,
        ha='center', weight='bold')

# section cut indicators on front view
ax.text(FX-20, FY+FH+8, "A", fontsize=10, weight='bold')
ax.text(FX+FW+8, FY+FH+8, "A", fontsize=10, weight='bold')
ax.plot([FX-15, FX-15], [FY-5, FY+FH+5], 'k-', lw=1.4)
ax.plot([FX+FW+15, FX+FW+15], [FY-5, FY+FH+5], 'k-', lw=1.4)
ax.annotate("", xy=(FX-15, FY+FH+5), xytext=(FX-15, FY-5),
            arrowprops=dict(arrowstyle='-|>', color='k', lw=1.2))
ax.annotate("", xy=(FX+FW+15, FY-5), xytext=(FX+FW+15, FY+FH+5),
            arrowprops=dict(arrowstyle='-|>', color='k', lw=1.2))

# ============================================================
# DETAIL VIEW B (zoomed corner — bottom-center)
# ============================================================
DET_X, DET_Y = 620, 300
DET_R = 55
ax.add_patch(Circle((DET_X, DET_Y), DET_R, fill=False, ec='k', lw=LW_MAIN))
# zoomed corner detail — a small radius
arc = Arc((DET_X-15, DET_Y-15), 40, 40, theta1=0, theta2=90,
          ec='k', lw=LW_MAIN)
ax.add_patch(arc)
ax.plot([DET_X-15, DET_X+30], [DET_Y-15, DET_Y-15], 'k-', lw=LW_MAIN)
ax.plot([DET_X-15, DET_X-15], [DET_Y-15, DET_Y+30], 'k-', lw=LW_MAIN)
leader(DET_X+5, DET_Y+5, DET_X+40, DET_Y+40, "R15", fontsize=8)
ax.text(DET_X, DET_Y-DET_R-15, "DETAIL B  (SCALE 2:1)",
        fontsize=FONT_NOTE, ha='center', weight='bold')

# ============================================================
# GD&T CALLOUTS
# ============================================================
# Position tolerance on the 4 corner holes
gdt_frame(FX-40, FY+FH+60, "\u2316", "\u2300 0.2 A B C",
          datum=None, w=60, h=20)
leader(FX-20, FY+FH+50, FX-20, FY+FH+15, "", fontsize=8)

# Flatness on top surface
gdt_frame(FX+FW+40, FY+FH-30, "\u25B1", "0.1", w=45, h=20)
leader(FX+FW+40, FY+FH-20, FX+FW+8, FY+FH-20, "", fontsize=8)

# Perpendicularity
gdt_frame(FX+FW+40, FY+FH-90, "\u27C2", "0.15 A", w=60, h=20)
leader(FX+FW+40, FY+FH-80, FX+FW+8, FY+FH-80, "", fontsize=8)

# ============================================================
# WELD SYMBOL (bottom-right, on side view) — optional flavor
# ============================================================
WX, WY = 850, 700
ax.plot([WX, WX+60], [WY, WY], 'k-', lw=1.2)  # reference line
ax.plot([WX, WX-20], [WY, WY-15], 'k-', lw=1.0)  # arrow
ax.plot([WX-20, WX-30], [WY-15, WY-15], 'k-', lw=1.0)
ax.plot([WX+10, WX+20, WX+30, WX+10], [WY, WY+10, WY, WY], 'k-', lw=1.0)
ax.text(WX+35, WY+5, "TYP", fontsize=7)

# ============================================================
# TITLE BLOCK (bottom-right)
# ============================================================
TB_X, TB_Y, TB_W, TB_H = 1140, 60, 430, 240
ax.add_patch(Rectangle((TB_X, TB_Y), TB_W, TB_H,
                       fill=False, ec='k', lw=1.8))
# horizontal dividers
ax.plot([TB_X, TB_X+TB_W], [TB_Y+180, TB_Y+180], 'k-', lw=1.0)
ax.plot([TB_X, TB_X+TB_W], [TB_Y+130, TB_Y+130], 'k-', lw=1.0)
ax.plot([TB_X, TB_X+TB_W], [TB_Y+90, TB_Y+90], 'k-', lw=1.0)
ax.plot([TB_X, TB_X+TB_W], [TB_Y+50, TB_Y+50], 'k-', lw=1.0)
# vertical dividers (in lower rows)
ax.plot([TB_X+TB_W*0.6, TB_X+TB_W*0.6], [TB_Y, TB_Y+130], 'k-', lw=1.0)
ax.plot([TB_X+TB_W*0.3, TB_X+TB_W*0.3], [TB_Y, TB_Y+50], 'k-', lw=1.0)

# Title block contents
ax.text(TB_X+10, TB_Y+215, "ATA MANUFACTURING GmbH",
        fontsize=13, weight='bold')
ax.text(TB_X+10, TB_Y+195, "Machine & Plant Components Division",
        fontsize=8, style='italic')

ax.text(TB_X+10, TB_Y+155, "PART NAME:", fontsize=8)
ax.text(TB_X+120, TB_Y+155, "MOUNTING BRACKET — REV C",
        fontsize=11, weight='bold')

ax.text(TB_X+10, TB_Y+110, "PART NO:", fontsize=8)
ax.text(TB_X+120, TB_Y+110, "ATA-BRK-4217-C", fontsize=10, weight='bold')

ax.text(TB_X+10, TB_Y+70, "MATERIAL:", fontsize=8)
ax.text(TB_X+90, TB_Y+70, "SS 304, 3.0mm", fontsize=9)

ax.text(TB_X+TB_W*0.65, TB_Y+70, "FINISH:", fontsize=8)
ax.text(TB_X+TB_W*0.75, TB_Y+70, "#4 BRUSHED", fontsize=9)

ax.text(TB_X+10, TB_Y+30, "DRAWN:", fontsize=7)
ax.text(TB_X+10, TB_Y+15, "K. Kumar", fontsize=8)
ax.text(TB_X+TB_W*0.3+10, TB_Y+30, "CHECKED:", fontsize=7)
ax.text(TB_X+TB_W*0.3+10, TB_Y+15, "M. Weber", fontsize=8)
ax.text(TB_X+TB_W*0.6+10, TB_Y+30, "APPROVED:", fontsize=7)
ax.text(TB_X+TB_W*0.6+10, TB_Y+15, "H. Schmidt", fontsize=8)

ax.text(TB_X+TB_W*0.3+10, TB_Y+95, "SCALE:", fontsize=8)
ax.text(TB_X+TB_W*0.3+60, TB_Y+95, "1:1", fontsize=10, weight='bold')
ax.text(TB_X+TB_W*0.6+10, TB_Y+95, "DATE:", fontsize=8)
ax.text(TB_X+TB_W*0.6+55, TB_Y+95, "2026-02-14", fontsize=9)

# Revision table (small, above title block)
REV_X, REV_Y = 1140, 320
ax.add_patch(Rectangle((REV_X, REV_Y), 430, 70,
                       fill=False, ec='k', lw=1.0))
ax.plot([REV_X, REV_X+430], [REV_Y+25, REV_Y+25], 'k-', lw=0.7)
ax.plot([REV_X+60, REV_X+60], [REV_Y, REV_Y+70], 'k-', lw=0.7)
ax.plot([REV_X+140, REV_X+140], [REV_Y, REV_Y+70], 'k-', lw=0.7)
ax.text(REV_X+15, REV_Y+50, "REV", fontsize=8, weight='bold')
ax.text(REV_X+75, REV_Y+50, "DESCRIPTION", fontsize=8, weight='bold')
ax.text(REV_X+250, REV_Y+50, "DATE", fontsize=8, weight='bold')
ax.text(REV_X+15, REV_Y+12, "A", fontsize=8)
ax.text(REV_X+75, REV_Y+12, "Initial release", fontsize=8)
ax.text(REV_X+250, REV_Y+12, "2025-08-01", fontsize=8)
ax.text(REV_X+15, REV_Y-15, "C", fontsize=8, weight='bold')
ax.text(REV_X+75, REV_Y-15, "Added countersinks & GD&T", fontsize=8)
ax.text(REV_X+250, REV_Y-15, "2026-02-14", fontsize=8)

# ============================================================
# DRAWING NOTES (upper-right of front view area)
# ============================================================
NOTES_X, NOTES_Y = 1060, 900
ax.text(NOTES_X, NOTES_Y, "NOTES:", fontsize=9, weight='bold')
notes = [
    "1. INTERPRET DRAWING PER ASME Y14.5-2018",
    "2. ALL DIMENSIONS IN MILLIMETERS",
    "3. REMOVE ALL BURRS AND SHARP EDGES",
    "4. TOLERANCES UNLESS NOTED:",
    "      X.X  \u00B1 0.5     X.XX  \u00B1 0.10",
    "      ANGLES  \u00B1 0.5\u00B0",
    "5. MATERIAL CERT REQUIRED",
    "6. RoHS COMPLIANT",
]
for i, n in enumerate(notes):
    ax.text(NOTES_X, NOTES_Y-18-i*14, n, fontsize=7.5)

# ============================================================
# SAVE
# ============================================================
plt.savefig("data/complex_bracket.png", dpi=200,
            bbox_inches='tight', facecolor='white')
print("✅ Saved: data/complex_bracket.png")