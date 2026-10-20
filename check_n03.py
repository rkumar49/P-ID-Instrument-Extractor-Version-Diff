import oracledb
from config import ORACLE_USER, ORACLE_PASS, ORACLE_DSN

try:
    oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_7\instantclient_23_26")
except Exception:
    pass

conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=ORACLE_DSN)
cur = conn.cursor()

for doc_id in [1, 2]:
    print(f"\n=== DOC {doc_id} — N03/XL03/N04/XL04 detections ===")
    cur.execute("""
        SELECT TEXT_RAW, X, Y FROM CAD_DETECTIONS
        WHERE DOC_ID = :d AND TEXT_RAW IN ('N03', 'XL03', 'N04', 'XL04')
        ORDER BY TEXT_RAW, Y
    """, d=doc_id)
    for r in cur.fetchall():
        bucket_x = r[1] // 500
        bucket_y = r[2] // 500
        print(f"  {r[0]:5s}  X={r[1]:5d}  Y={r[2]:5d}  → bucket ({bucket_x}, {bucket_y})")

conn.close()