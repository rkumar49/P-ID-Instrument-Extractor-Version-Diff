import oracledb
from config import ORACLE_USER, ORACLE_PASS, ORACLE_DSN
import pathlib

try:
    oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_7\instantclient_23_26")
except Exception:
    pass

conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=ORACLE_DSN)
cur = conn.cursor()

print("=== Documents and render files ===")
cur.execute("""
    SELECT DISTINCT DOC_ID, FILENAME, VERSION_LABEL
    FROM CAD_DATA
    ORDER BY DOC_ID
""")

for r in cur.fetchall():
    doc_id, filename, label = r
    render = pathlib.Path(f"output/renders/doc_{doc_id}.png")
    if render.exists():
        size_mb = render.stat().st_size / (1024 * 1024)
        print(f"  DOC {doc_id}  {label}  → render EXISTS  {size_mb:.2f} MB")
    else:
        print(f"  DOC {doc_id}  {label}  → render MISSING ❌")

conn.close()