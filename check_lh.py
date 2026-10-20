import oracledb
from config import ORACLE_USER, ORACLE_PASS, ORACLE_DSN

try:
    oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_7\instantclient_23_26")
except Exception:
    pass

conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=ORACLE_DSN)
cur = conn.cursor()

print("=== All L and H detections ===")
cur.execute("""
    SELECT DOC_ID, TEXT_RAW, CATEGORY, X, Y
    FROM CAD_DETECTIONS
    WHERE UPPER(TEXT_RAW) IN ('L', 'H')
    ORDER BY DOC_ID, Y
""")
for r in cur.fetchall():
    print(f"  DOC={r[0]}  TEXT={r[1]!r}  CATEGORY={r[2]}  X={r[3]}  Y={r[4]}")

print()
print("=== All *_BG02L or *_BG02H style detections ===")
cur.execute("""
    SELECT DOC_ID, TEXT_RAW, CATEGORY, X, Y
    FROM CAD_DETECTIONS
    WHERE UPPER(TEXT_RAW) LIKE '%BG02L%'
       OR UPPER(TEXT_RAW) LIKE '%BG02H%'
    ORDER BY DOC_ID, Y
""")
for r in cur.fetchall():
    print(f"  DOC={r[0]}  TEXT={r[1]!r}  CATEGORY={r[2]}  X={r[3]}  Y={r[4]}")

conn.close()