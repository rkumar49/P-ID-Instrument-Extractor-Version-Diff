import oracledb
from config import ORACLE_USER, ORACLE_PASS, ORACLE_DSN

try:
    oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_7\instantclient_23_26")
except Exception:
    pass

conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=ORACLE_DSN)
cur = conn.cursor()

print("=== Documents in DB ===")
cur.execute("""
    SELECT DOC_ID, FILENAME, VERSION_LABEL, COUNT(*)
    FROM CAD_DATA
    GROUP BY DOC_ID, FILENAME, VERSION_LABEL
    ORDER BY DOC_ID
""")
for r in cur.fetchall():
    print(r)

print("\n=== All rows for QM002-QM01 (any doc) ===")
cur.execute("""
    SELECT DOC_ID, FUNC, SYSTEM_CODE, COMPONENT_ID, PIPE_SIZES, X, Y
    FROM CAD_DATA
    WHERE COMPONENT_ID LIKE '%QM002%'
    ORDER BY DOC_ID
""")
for r in cur.fetchall():
    print(r)

print("\n=== All rows for QM004-QM01 (any doc) ===")
cur.execute("""
    SELECT DOC_ID, FUNC, SYSTEM_CODE, COMPONENT_ID, PIPE_SIZES, X, Y
    FROM CAD_DATA
    WHERE COMPONENT_ID LIKE '%QM004%'
    ORDER BY DOC_ID
""")
for r in cur.fetchall():
    print(r)

print("\n=== Count of instruments per document ===")
cur.execute("""
    SELECT DOC_ID, COUNT(*)
    FROM CAD_DATA
    GROUP BY DOC_ID
    ORDER BY DOC_ID
""")
for r in cur.fetchall():
    print(r)

print("\n=== Sample component_ids in each doc (first 20) ===")
for doc_id in [1, 2, 3, 4]:
    cur.execute("""
        SELECT COMPONENT_ID FROM CAD_DATA
        WHERE DOC_ID = :1 AND COMPONENT_ID IS NOT NULL
        ORDER BY COMPONENT_ID
    """, [doc_id])
    rows = [r[0] for r in cur.fetchall()]
    print(f"\nDoc {doc_id} ({len(rows)} components):")
    print(rows[:30])

conn.close()