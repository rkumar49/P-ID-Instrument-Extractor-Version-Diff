import oracledb
from config import ORACLE_USER, ORACLE_PASS, ORACLE_DSN

try:
    oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_7\instantclient_23_26")
except Exception:
    pass

conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=ORACLE_DSN)
cur = conn.cursor()

# We will inspect QM003-QM01 in docs 1 and 2
for doc_id in [1, 2]:
    print(f"\n========== DOC_ID {doc_id} ==========")

    # Where is QM003-QM01?
    cur.execute("""
        SELECT FUNC, SYSTEM_CODE, COMPONENT_ID, PIPE_SIZES, X, Y
        FROM CAD_DATA
        WHERE DOC_ID = :1 AND COMPONENT_ID LIKE '%QM003-QM01%'
    """, [doc_id])
    saved = cur.fetchall()
    print(f"Saved instrument: {saved}")

    if not saved:
        continue

    cx, cy = saved[0][4], saved[0][5]

    # All pipe labels near it
    print(f"\nPipe labels within 500px of ({cx}, {cy}), sorted by distance:")
    cur.execute("""
        SELECT TEXT_RAW, X, Y,
               (X - :1) * (X - :1) + (Y - :2) * (Y - :2) AS dist_sq
        FROM CAD_DETECTIONS
        WHERE DOC_ID = :3 AND CATEGORY = 'pipe_size'
          AND ABS(X - :1) < 500 AND ABS(Y - :2) < 500
        ORDER BY dist_sq
    """, [cx, cy, doc_id])
    for r in cur.fetchall():
        dist = r[3] ** 0.5
        print(f"  {r[0]:8s}  at ({r[1]}, {r[2]})  dist = {dist:.0f}px")

    # All component_id detections near it
    print(f"\nComponent IDs within 500px:")
    cur.execute("""
        SELECT TEXT_RAW, X, Y,
               (X - :1) * (X - :1) + (Y - :2) * (Y - :2) AS dist_sq
        FROM CAD_DETECTIONS
        WHERE DOC_ID = :3 AND CATEGORY = 'component_id'
          AND ABS(X - :1) < 500 AND ABS(Y - :2) < 500
        ORDER BY dist_sq
    """, [cx, cy, doc_id])
    for r in cur.fetchall():
        dist = r[3] ** 0.5
        print(f"  {r[0]:20s}  at ({r[1]}, {r[2]})  dist = {dist:.0f}px")

conn.close()