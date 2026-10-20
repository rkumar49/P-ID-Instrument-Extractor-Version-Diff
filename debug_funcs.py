import oracledb
from config import ORACLE_USER, ORACLE_PASS, ORACLE_DSN

try:
    oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_7\instantclient_23_26")
except Exception:
    pass

conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=ORACLE_DSN)
cur = conn.cursor()

# Look at CAD_DATA for the entire document, sorted by Y
for doc_id in [1, 2]:
    print(f"\n=== DOC {doc_id} — ALL rows sorted by Y ===")
    cur.execute(
        "SELECT FUNC, COMPONENT_ID, X, Y FROM CAD_DATA "
        "WHERE DOC_ID = :d ORDER BY Y",
        d=doc_id,
    )
    for r in cur.fetchall():
        print(f"  Y={r[3]:5d}  X={r[2]:5d}  FUNC={str(r[0]):5s}  COMP={r[1]}")

conn.close()