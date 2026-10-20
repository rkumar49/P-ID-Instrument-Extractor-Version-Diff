import oracledb
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from config import ORACLE_USER, ORACLE_PASS, ORACLE_DSN

try:
    oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_7\instantclient_23_26")
except Exception:
    pass

conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=ORACLE_DSN)
cur = conn.cursor()

# Focus on a small region around QM003-QM01 in old doc (doc 3)
print("=== Components in region around QM003-QM01 (doc 3) ===")
cur.execute("""
    SELECT FUNC, SYSTEM_CODE, COMPONENT_ID, PIPE_SIZES, X, Y
    FROM CAD_DATA
    WHERE DOC_ID = 3
      AND X BETWEEN 2000 AND 3500
      AND Y BETWEEN 2000 AND 3000
    ORDER BY X, Y
""")
for r in cur.fetchall():
    print(r)

print("\n=== All pipe_size detections in same region (doc 3) ===")
cur.execute("""
    SELECT TEXT_RAW, X, Y
    FROM CAD_DETECTIONS
    WHERE DOC_ID = 3 AND CATEGORY = 'pipe_size'
      AND X BETWEEN 2000 AND 3500
      AND Y BETWEEN 2000 AND 3000
    ORDER BY X, Y
""")
for r in cur.fetchall():
    print(r)

print("\n=== All component_id detections in same region (doc 3) ===")
cur.execute("""
    SELECT TEXT_RAW, X, Y
    FROM CAD_DETECTIONS
    WHERE DOC_ID = 3 AND CATEGORY = 'component_id'
      AND X BETWEEN 2000 AND 3500
      AND Y BETWEEN 2000 AND 3000
    ORDER BY X, Y
""")
for r in cur.fetchall():
    print(r)

conn.close()