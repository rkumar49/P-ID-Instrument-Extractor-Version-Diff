import oracledb
from config import ORACLE_USER, ORACLE_PASS, ORACLE_DSN
from utils.classify import group_instruments

try:
    oracledb.init_oracle_client(lib_dir=r"C:\Oracle\instantclient_23_7\instantclient_23_26")
except Exception:
    pass

conn = oracledb.connect(user=ORACLE_USER, password=ORACLE_PASS, dsn=ORACLE_DSN)
cur = conn.cursor()

# Pull raw detections for DOC 1
cur.execute(
    "SELECT TEXT_RAW, CATEGORY, CONFIDENCE, X, Y, W, H FROM CAD_DETECTIONS "
    "WHERE DOC_ID = 1 ORDER BY Y, X"
)
rows = cur.fetchall()
conn.close()

# Rebuild the detections list the way the app does
detections = []
for text, cat, conf, x, y, w, h in rows:
    detections.append({
        "text": text, "category": cat, "confidence": conf,
        "x": x, "y": y, "w": w, "h": h,
        "bbox": None,
    })

print(f"\nTotal raw detections: {len(detections)}")
print(f"ASH detections in input: {sum(1 for d in detections if d['text'] == 'ASH')}")

# Run grouping
instruments, unassigned = group_instruments(detections)

print(f"\nTotal instruments: {len(instruments)}")
print(f"ASH rows in output: {sum(1 for r in instruments if r.get('func') == 'ASH')}")
print("\nAll ASH instruments:")
for r in instruments:
    if r.get("func") == "ASH":
        print(f"  func={r['func']}  comp={r.get('component_id')}  at ({r['x']}, {r['y']})")