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

    # What was saved for QM003-QM01?
    cur.execute(
        "SELECT COMPONENT_ID, PIPE_SIZES, X, Y FROM CAD_DATA "
        "WHERE DOC_ID = :d AND COMPONENT_ID = 'QM003-QM01'",
        d=doc_id,
    )
    print(f"Saved: {cur.fetchone()}")

    # Other nearby components
    print("Nearby components:")
    cur.execute(
        "SELECT COMPONENT_ID, PIPE_SIZES, X, Y FROM CAD_DATA "
        "WHERE DOC_ID = :d AND X BETWEEN 2000 AND 3500 AND Y BETWEEN 2000 AND 3000 "
        "ORDER BY X",
        d=doc_id,
    )
    for r in cur.fetchall():
        print(f"  {r[0]:20s}  pipe={str(r[1]):12s}  at ({r[2]}, {r[3]})")

    # All pipe labels in the region
    print("All pipe labels in region:")
    cur.execute(
        "SELECT TEXT_RAW, X, Y FROM CAD_DETECTIONS "
        "WHERE DOC_ID = :d AND CATEGORY = 'pipe_size' "
        "  AND X BETWEEN 2000 AND 3500 AND Y BETWEEN 2000 AND 3000",
        d=doc_id,
    )
    for r in cur.fetchall():
        print(f"  {r[0]:8s}  at ({r[1]}, {r[2]})")

conn.close()