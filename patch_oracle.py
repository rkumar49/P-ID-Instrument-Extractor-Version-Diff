import pathlib

p = pathlib.Path("utils/oracle.py")
s = p.read_text(encoding="utf-8")

new_func = '''def load_documents():
    """Return summary of all saved documents."""
    init_table()
    with _conn() as conn:
        return pd.read_sql(
            """
            SELECT DOC_ID, FILENAME, VERSION_LABEL, UPLOADED_AT, N_INSTRUMENTS
            FROM (
                SELECT DOC_ID,
                       MAX(FILENAME)      AS FILENAME,
                       MAX(VERSION_LABEL) AS VERSION_LABEL,
                       MAX(UPLOADED_AT)   AS UPLOADED_AT,
                       COUNT(*)           AS N_INSTRUMENTS
                FROM   CAD_DATA
                GROUP  BY DOC_ID
            )
            ORDER BY UPLOADED_AT DESC
            """,
            conn,
        )


'''

start = s.find("def load_documents")
end = s.find("def load_instruments")

if start == -1 or end == -1:
    print("ERROR: markers not found. start=", start, "end=", end)
else:
    s2 = s[:start] + new_func + s[end:]
    p.write_text(s2, encoding="utf-8")
    print("Patched. New length:", len(s2))