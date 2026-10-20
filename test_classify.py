import utils.classify as m

tests = [
    "=H01GDK01",
    "=Z02RAE30",
    "=Z02NHC20",
    "=Z04QFB10WP014-WP01",
    "=N11-Elektrolysesystem",
    "=A01XXXXXX",
    "=C01XXXXXX",
    "=S01XXXXXX",
    "X01XXXXXX",
    "QM002-QM01",
    "DN50",
    "LIC",
]

for v in tests:
    print(f"{v:30s} -> {m.classify_text(v)}")