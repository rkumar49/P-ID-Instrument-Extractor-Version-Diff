import oracledb
from config import ORACLE_USER, ORACLE_PASS, ORACLE_DSN

try:
    oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_7\instantclient_23_26")
except Exception:
    pass

conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=ORACLE_DSN)
cur = conn.cursor()

for doc_id in [1, 2]:
    print(f"\n========== DOC {doc_id} ==========")

    cur.execute(
        "SELECT X, Y FROM CAD_DATA WHERE DOC_ID = :d AND COMPONENT_ID = 'QM003-QM01'",
        d=doc_id,
    )
    row = cur.fetchone()
    if not row:
        continue
    cx, cy = row

    print(f"\nPipe labels near QM003-QM01 at ({cx}, {cy}):")
    cur.execute(
        "SELECT TEXT_RAW, X, Y, W, H FROM CAD_DETECTIONS "
        "WHERE DOC_ID = :d AND CATEGORY = 'pipe_size' "
        "  AND X BETWEEN :x1 AND :x2 AND Y BETWEEN :y1 AND :y2 "
        "ORDER BY X",
        d=doc_id, x1=cx - 400, x2=cx + 400, y1=cy - 400, y2=cy + 400,
    )
    for r in cur.fetchall():
        text, x, y, w, h = r
        dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
        orientation = "TALL (vertical text)" if h > w * 1.5 else \
                      "WIDE (horizontal text)" if w > h * 1.5 else \
                      "SQUARE-ish"
        print(f"  {text:8s} at ({x:5d},{y:5d})  W={w:3d} H={h:3d}  dist={dist:6.0f}  {orientation}")

conn.close()