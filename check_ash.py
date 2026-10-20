import oracledb
from config import ORACLE_USER, ORACLE_PASS, ORACLE_DSN

try:
    oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_7\instantclient_23_26")
except Exception:
    pass

conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=ORACLE_DSN)
cur = conn.cursor()

for doc_id in [1, 2]:
    print(f"\n=== DOC_ID {doc_id} ===")
    # Any row with ASH in func or component_id
    cur.execute(
        "SELECT FUNC, SYSTEM_CODE, COMPONENT_ID, PIPE_SIZES, X, Y "
        "FROM CAD_DATA "
        "WHERE DOC_ID = :d "
        "  AND (UPPER(FUNC) LIKE '%ASH%' OR UPPER(COMPONENT_ID) LIKE '%ASH%')",
        d=doc_id,
    )
    rows = cur.fetchall()
    if not rows:
        print("  No rows with ASH found in CAD_DATA")
    for r in rows:
        print(f"  FUNC={r[0]}  SYS={r[1]}  COMP={r[2]}  PIPE={r[3]}  at ({r[4]}, {r[5]})")

    # ASH in raw detections
    cur.execute(
        "SELECT TEXT_RAW, CATEGORY, X, Y "
        "FROM CAD_DETECTIONS "
        "WHERE DOC_ID = :d AND UPPER(TEXT_RAW) LIKE '%ASH%'",
        d=doc_id,
    )
    dets = cur.fetchall()
    print(f"  ASH raw detections: {len(dets)}")
    for r in dets:
        print(f"    {r[0]}  cat={r[1]}  at ({r[2]}, {r[3]})")

conn.close()