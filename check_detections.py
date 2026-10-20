import oracledb
from config import ORACLE_USER, ORACLE_PASS, ORACLE_DSN

try:
    oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_7\instantclient_23_26")
except Exception:
    pass

conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=ORACLE_DSN)
cur = conn.cursor()

cx, cy = 2463, 2523   # QM003-QM01 in DOC 1

print(f"=== All detections in DOC 1 within 300px of ({cx}, {cy}) ===")
cur.execute(
    "SELECT TEXT_RAW, CATEGORY, X, Y FROM CAD_DETECTIONS "
    "WHERE DOC_ID = 1 "
    "  AND X BETWEEN :x1 AND :x2 AND Y BETWEEN :y1 AND :y2",
    x1=cx - 300, x2=cx + 300, y1=cy - 300, y2=cy + 300,
)
results = cur.fetchall()
# Sort by distance
results_sorted = sorted(results, key=lambda r: (r[2] - cx) ** 2 + (r[3] - cy) ** 2)
for r in results_sorted:
    dist = ((r[2] - cx) ** 2 + (r[3] - cy) ** 2) ** 0.5
    print(f"  {r[1]:20s} {r[0]:25s}  at ({r[2]}, {r[3]})   dist = {dist:.0f}px")

conn.close()