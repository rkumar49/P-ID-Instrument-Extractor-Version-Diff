import oracledb
from config import ORACLE_USER, ORACLE_PASS, ORACLE_DSN

try:
    oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_7\instantclient_23_26")
except Exception:
    pass

conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=ORACLE_DSN)
cur = conn.cursor()

print("=== All instruments for BG001-BG02* ===")
cur.execute("""
    SELECT DOC_ID, FUNC, SYSTEM_CODE, COMPONENT_ID, PIPE_SIZES, X, Y
    FROM CAD_DATA
    WHERE COMPONENT_ID LIKE 'BG001-BG02%'
    ORDER BY DOC_ID, X, Y
""")
for r in cur.fetchall():
    print(r)

print("\n=== All pipe_size detections near BG001-BG02 (doc 2, new) ===")
cur.execute("""
    SELECT TEXT_RAW, X, Y
    FROM CAD_DETECTIONS
    WHERE DOC_ID = 2 AND CATEGORY = 'pipe_size'
      AND X BETWEEN 3400 AND 4100 AND Y BETWEEN 1200 AND 1700
    ORDER BY X
""")
for r in cur.fetchall():
    print(r)

print("\n=== All instrument_func detections near BG001-BG02 (doc 2) ===")
cur.execute("""
    SELECT TEXT_RAW, X, Y
    FROM CAD_DETECTIONS
    WHERE DOC_ID = 2 AND CATEGORY = 'instrument_func'
      AND X BETWEEN 3400 AND 4100 AND Y BETWEEN 1200 AND 1700
    ORDER BY X
""")
for r in cur.fetchall():
    print(r)

conn.close()