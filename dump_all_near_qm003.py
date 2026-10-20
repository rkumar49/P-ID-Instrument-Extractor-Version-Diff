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
        print("QM003-QM01 not found")
        continue
    cx, cy = row

    print(f"\nQM003-QM01 at ({cx}, {cy})")
    print(f"\nALL detections within 250px (any category):")

    cur.execute(
        "SELECT TEXT_RAW, CATEGORY, X, Y FROM CAD_DETECTIONS "
        "WHERE DOC_ID = :d "
        "  AND X BETWEEN :x1 AND :x2 AND Y BETWEEN :y1 AND :y2 "
        "ORDER BY Y, X",
        d=doc_id, x1=cx - 250, x2=cx + 250, y1=cy - 250, y2=cy + 250,
    )
    for r in cur.fetchall():
        dist = ((r[2] - cx) ** 2 + (r[3] - cy) ** 2) ** 0.5
        print(f"  {r[1]:20s} {r[0]:25s}  at ({r[2]:5d},{r[3]:5d})  dist={dist:6.0f}")

conn.close()