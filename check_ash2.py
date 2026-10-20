import oracledb
from config import ORACLE_USER, ORACLE_PASS, ORACLE_DSN

try:
    oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_7\instantclient_23_26")
except Exception:
    pass

conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=ORACLE_DSN)
cur = conn.cursor()

# What components are near ASH at (3019, 3180)?
for doc_id in [1, 2]:
    print(f"\n=== DOC {doc_id} — components within 300px of ASH (3019, 3180) ===")
    cur.execute(
        "SELECT FUNC, COMPONENT_ID, X, Y FROM CAD_DATA "
        "WHERE DOC_ID = :d "
        "  AND X BETWEEN 2719 AND 3319 "
        "  AND Y BETWEEN 2880 AND 3480 "
        "ORDER BY Y, X",
        d=doc_id,
    )
    for r in cur.fetchall():
        print(f"  FUNC={r[0]}  COMP={r[1]}  at ({r[2]}, {r[3]})")

    print(f"\n=== DOC {doc_id} — raw component detections near (3019, 3180) ===")
    cur.execute(
        "SELECT TEXT_RAW, CATEGORY, X, Y FROM CAD_DETECTIONS "
        "WHERE DOC_ID = :d "
        "  AND X BETWEEN 2719 AND 3319 "
        "  AND Y BETWEEN 2880 AND 3480 "
        "ORDER BY Y, X",
        d=doc_id,
    )
    for r in cur.fetchall():
        print(f"  {r[0]:25s}  cat={r[1]:20s}  at ({r[2]}, {r[3]})")

conn.close()