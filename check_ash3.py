import oracledb
from config import ORACLE_USER, ORACLE_PASS, ORACLE_DSN

try:
    oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_7\instantclient_23_26")
except Exception:
    pass

conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=ORACLE_DSN)
cur = conn.cursor()

for doc_id in [1, 2]:
    print(f"\n=== DOC {doc_id} — all ASH raw detections ===")
    cur.execute(
        "SELECT TEXT_RAW, CATEGORY, CONFIDENCE, X, Y FROM CAD_DETECTIONS "
        "WHERE DOC_ID = :d AND TEXT_RAW = 'ASH' ORDER BY Y",
        d=doc_id,
    )
    for r in cur.fetchall():
        print(f"  {r[0]:5s}  cat={r[1]:15s}  conf={r[2]}  at ({r[3]}, {r[4]})")

    print(f"\n=== DOC {doc_id} — all ASH in CAD_DATA ===")
    cur.execute(
        "SELECT FUNC, COMPONENT_ID, X, Y FROM CAD_DATA "
        "WHERE DOC_ID = :d AND FUNC = 'ASH' ORDER BY Y",
        d=doc_id,
    )
    for r in cur.fetchall():
        print(f"  FUNC={r[0]}  COMP={r[1]}  at ({r[2]}, {r[3]})")

conn.close()