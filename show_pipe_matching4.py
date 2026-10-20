import oracledb
from config import ORACLE_USER, ORACLE_PASS, ORACLE_DSN

try:
    oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_7\instantclient_23_26")
except Exception:
    pass

conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=ORACLE_DSN)
cur = conn.cursor()

for doc_id in [1, 2]:
    print(f"\n========== DOC_ID {doc_id} ==========")

    # Where is QM003-QM01?
    cur.execute(
        "SELECT FUNC, SYSTEM_CODE, COMPONENT_ID, PIPE_SIZES, X, Y "
        "FROM CAD_DATA WHERE DOC_ID = :d AND COMPONENT_ID LIKE '%QM003-QM01%'",
        d=doc_id,
    )
    saved = cur.fetchall()
    print(f"Saved instrument: {saved}")
    if not saved:
        continue

    cx, cy = saved[0][4], saved[0][5]

    # Pipe labels near it — sort by distance in Python to avoid bind issues
    print(f"\nPipe labels within 500px of ({cx}, {cy}):")
    cur.execute(
        "SELECT TEXT_RAW, X, Y FROM CAD_DETECTIONS "
        "WHERE DOC_ID = :d AND CATEGORY = 'pipe_size' "
        "  AND X BETWEEN :x1 AND :x2 AND Y BETWEEN :y1 AND :y2",
        d=doc_id, x1=cx - 500, x2=cx + 500, y1=cy - 500, y2=cy + 500,
    )
    pipes = cur.fetchall()
    pipes_sorted = sorted(pipes, key=lambda r: (r[1] - cx) ** 2 + (r[2] - cy) ** 2)
    for r in pipes_sorted:
        dist = ((r[1] - cx) ** 2 + (r[2] - cy) ** 2) ** 0.5
        print(f"  {r[0]:10s}  at ({r[1]}, {r[2]})   dist = {dist:.0f}px")

    # Component IDs near it
    print(f"\nComponent IDs within 500px:")
    cur.execute(
        "SELECT TEXT_RAW, X, Y FROM CAD_DETECTIONS "
        "WHERE DOC_ID = :d AND CATEGORY = 'component_id' "
        "  AND X BETWEEN :x1 AND :x2 AND Y BETWEEN :y1 AND :y2",
        d=doc_id, x1=cx - 500, x2=cx + 500, y1=cy - 500, y2=cy + 500,
    )
    comps = cur.fetchall()
    comps_sorted = sorted(comps, key=lambda r: (r[1] - cx) ** 2 + (r[2] - cy) ** 2)
    for r in comps_sorted:
        dist = ((r[1] - cx) ** 2 + (r[2] - cy) ** 2) ** 0.5
        print(f"  {r[0]:20s}  at ({r[1]}, {r[2]})   dist = {dist:.0f}px")

conn.close()