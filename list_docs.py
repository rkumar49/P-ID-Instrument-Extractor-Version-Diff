import oracledb
from config import ORACLE_USER, ORACLE_PASS, ORACLE_DSN

try:
    oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_7\instantclient_23_26")
except Exception:
    pass

conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=ORACLE_DSN)
cur = conn.cursor()

print("=== All documents ===")
cur.execute("""
    SELECT DOC_ID, MAX(FILENAME), MAX(VERSION_LABEL), COUNT(*)
    FROM CAD_DATA
    GROUP BY DOC_ID
    ORDER BY DOC_ID
""")
for r in cur.fetchall():
    print(r)

conn.close()