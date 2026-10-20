import oracledb
from config import ORACLE_USER, ORACLE_PASS, ORACLE_DSN

try:
    oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_7\instantclient_23_26")
except Exception:
    pass

conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=ORACLE_DSN)
cur = conn.cursor()

# All component_ids sorted by X (left to right)
print("=== ALL component IDs, sorted by X (left → right) for DOC 1 ===")
cur.execute("""
    SELECT TEXT_RAW, X, Y
    FROM CAD_DETECTIONS
    WHERE DOC_ID = 1 AND CATEGORY = 'component_id'
    ORDER BY X
""")
for r in cur.fetchall():
    print(r)

print("\n=== ALL component IDs, sorted by Y (top → bottom) ===")
cur.execute("""
    SELECT TEXT_RAW, X, Y
    FROM CAD_DETECTIONS
    WHERE DOC_ID = 1 AND CATEGORY = 'component_id'
    ORDER BY Y
""")
for r in cur.fetchall():
    print(r)

print("\n=== Search for QM009 specifically ===")
cur.execute("""
    SELECT TEXT_RAW, CATEGORY, X, Y
    FROM CAD_DETECTIONS
    WHERE DOC_ID = 1 AND TEXT_RAW LIKE '%009%'
""")
for r in cur.fetchall():
    print(r)

print("\n=== All raw texts sorted by category (unique values per category) ===")
cur.execute("""
    SELECT CATEGORY, TEXT_RAW, COUNT(*)
    FROM CAD_DETECTIONS
    WHERE DOC_ID = 1
    GROUP BY CATEGORY, TEXT_RAW
    ORDER BY CATEGORY, TEXT_RAW
""")
prev_cat = None
for r in cur.fetchall():
    if r[0] != prev_cat:
        print(f"\n--- {r[0]} ---")
        prev_cat = r[0]
    print(f"  {r[1]!r} (x{r[2]})")

conn.close()