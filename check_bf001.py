import oracledb
from config import ORACLE_USER, ORACLE_PASS, ORACLE_DSN

try:
    oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_7\instantclient_23_26")
except Exception:
    pass

conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=ORACLE_DSN)
cur = conn.cursor()

print("=== BF001-BF01 in CAD_DETECTIONS ===")
cur.execute("""
    SELECT DOC_ID, TEXT_RAW, CATEGORY, X, Y
    FROM CAD_DETECTIONS
    WHERE UPPER(TEXT_RAW) LIKE '%BF001%'
    ORDER BY DOC_ID
""")
rows = cur.fetchall()
if not rows:
    print("  ❌ NOT FOUND in CAD_DETECTIONS")
else:
    for r in rows:
        print(f"  DOC={r[0]}  TEXT={r[1]!r}  CATEGORY={r[2]}  X={r[3]}  Y={r[4]}")

print()
print("=== BF001-BF01 in CAD_DATA (instruments) ===")
cur.execute("""
    SELECT DOC_ID, FUNC, SYSTEM_CODE, COMPONENT_ID, X, Y
    FROM CAD_DATA
    WHERE UPPER(COMPONENT_ID) LIKE '%BF001%'
    ORDER BY DOC_ID
""")
rows = cur.fetchall()
if not rows:
    print("  ❌ NOT FOUND in CAD_DATA")
else:
    for r in rows:
        print(f"  DOC={r[0]}  FUNC={r[1]!r}  SYS={r[2]!r}  COMP={r[3]!r}  X={r[4]}  Y={r[5]}")

print()
print("=== All func bubbles in DOC 2 within 500px of BF001-BF01 ===")
cur.execute("""
    SELECT DOC_ID, TEXT_RAW, CATEGORY, X, Y
    FROM CAD_DETECTIONS
    WHERE DOC_ID = 2
      AND CATEGORY = 'instrument_func'
      AND X BETWEEN 1600 AND 2600
      AND Y BETWEEN 3100 AND 4100
    ORDER BY Y
""")
for r in cur.fetchall():
    print(f"  DOC={r[0]}  TEXT={r[1]!r}  X={r[3]}  Y={r[4]}")

conn.close()