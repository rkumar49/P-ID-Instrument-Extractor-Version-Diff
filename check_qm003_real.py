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

    # Where is QM003-QM01?
    cur.execute(
        "SELECT FUNC, SYSTEM_CODE, COMPONENT_ID, PIPE_SIZES, X, Y FROM CAD_DATA "
        "WHERE DOC_ID = :d AND COMPONENT_ID = 'QM003-QM01'",
        d=doc_id,
    )
    saved = cur.fetchall()
    print(f"Saved: {saved}")
    if not saved:
        continue

    cx, cy = saved[0][4], saved[0][5]

    # All pipe labels within 400px
    print(f"\nPipe labels within 400px of ({cx}, {cy}):")
    cur.execute(
        "SELECT TEXT_RAW, X, Y FROM CAD_DETECTIONS "
        "WHERE DOC_ID = :d AND CATEGORY = 'pipe_size' "
        "  AND X BETWEEN :x1 AND :x2 AND Y BETWEEN :y1 AND :y2",
        d=doc_id, x1=cx - 400, x2=cx + 400, y1=cy - 400, y2=cy + 400,
    )
    pipes = cur.fetchall()
    sorted_pipes = sorted(pipes, key=lambda r: (r[1] - cx) ** 2 + (r[2] - cy) ** 2)
    for r in sorted_pipes:
        dist = ((r[1] - cx) ** 2 + (r[2] - cy) ** 2) ** 0.5
        dx = r[1] - cx
        dy = r[2] - cy
        axis = ""
        if abs(dx) < 40:
            axis = " [same X — vertical pipe]"
        elif abs(dy) < 40:
            axis = " [same Y — horizontal pipe]"
        print(f"  {r[0]:8s} at ({r[1]:5d}, {r[2]:5d})  dist={dist:6.0f}  Δ=({dx:+5d},{dy:+5d}){axis}")

    # Other nearby components
    print(f"\nOther component_ids within 400px:")
    cur.execute(
        "SELECT TEXT_RAW, X, Y FROM CAD_DETECTIONS "
        "WHERE DOC_ID = :d AND CATEGORY = 'component_id' "
        "  AND X BETWEEN :x1 AND :x2 AND Y BETWEEN :y1 AND :y2 "
        "  AND TEXT_RAW != 'QM003-QM01'",
        d=doc_id, x1=cx - 400, x2=cx + 400, y1=cy - 400, y2=cy + 400,
    )
    for r in cur.fetchall():
        dist = ((r[1] - cx) ** 2 + (r[2] - cy) ** 2) ** 0.5
        print(f"  {r[0]:20s} at ({r[1]:5d}, {r[2]:5d})  dist={dist:6.0f}")

conn.close()