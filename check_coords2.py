import oracledb
from config import ORACLE_USER, ORACLE_PASS, ORACLE_DSN

try:
    oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_7\instantclient_23_26")
except Exception:
    pass

conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=ORACLE_DSN)
cur = conn.cursor()

for doc_id in [1, 2]:
    print(f"\n=== DOC {doc_id} ===")
    # X, Y ranges
    cur.execute("""
        SELECT MIN(X), MAX(X), MIN(Y), MAX(Y), COUNT(*),
               MIN(PAGE_WIDTH), MAX(PAGE_WIDTH),
               MIN(PAGE_HEIGHT), MAX(PAGE_HEIGHT)
        FROM CAD_DATA WHERE DOC_ID = :d
    """, d=doc_id)
    r = cur.fetchone()
    print(f"  X: {r[0]} to {r[1]}")
    print(f"  Y: {r[2]} to {r[3]}")
    print(f"  Rows: {r[4]}")
    print(f"  PAGE_WIDTH: {r[5]} to {r[6]}")
    print(f"  PAGE_HEIGHT: {r[7]} to {r[8]}")

    # Sample rows with high Y
    cur.execute("""
        SELECT COMPONENT_ID, X, Y FROM CAD_DATA
        WHERE DOC_ID = :d AND Y > 4238
        ORDER BY Y DESC FETCH FIRST 5 ROWS ONLY
    """, d=doc_id)
    print(f"  Rows with Y > 4238:")
    for r in cur.fetchall():
        print(f"    {r[0]}: X={r[1]}, Y={r[2]}")

conn.close()