"""
SQLite database for storing extracted instrument records across versions.

Schema v2 adds:
    - w, h (bounding box size)
    - page_width, page_height (for normalized coordinates)
    - source (pdf_text | ocr)
"""

import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd


DB_PATH = Path(__file__).resolve().parent.parent / "output" / "instruments.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


def _conn():
    return sqlite3.connect(DB_PATH)


def init_db():
    """Create tables (v2 schema) if they don't exist."""
    with _conn() as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                filename          TEXT NOT NULL,
                version_label     TEXT,
                page_num          INTEGER,
                page_width        INTEGER,
                page_height       INTEGER,
                extracted_at      TIMESTAMP,
                instrument_count  INTEGER,
                source            TEXT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS instruments (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                document_id  INTEGER NOT NULL,
                func         TEXT,
                system_code  TEXT,
                component_id TEXT,
                pipe_sizes   TEXT,
                confidence   REAL,
                x            INTEGER,
                y            INTEGER,
                w            INTEGER,
                h            INTEGER,
                FOREIGN KEY(document_id) REFERENCES documents(id)
            )
        """)
        c.commit()


def _ensure_columns():
    """Add columns to older DBs that don't have them (idempotent migration)."""
    with _conn() as c:
        # Inspect existing columns
        cols_docs = [r[1] for r in c.execute("PRAGMA table_info(documents)").fetchall()]
        for col, typ in [("page_width", "INTEGER"), ("page_height", "INTEGER"), ("source", "TEXT")]:
            if col not in cols_docs:
                c.execute(f"ALTER TABLE documents ADD COLUMN {col} {typ}")

        cols_inst = [r[1] for r in c.execute("PRAGMA table_info(instruments)").fetchall()]
        for col, typ in [("w", "INTEGER"), ("h", "INTEGER")]:
            if col not in cols_inst:
                c.execute(f"ALTER TABLE instruments ADD COLUMN {col} {typ}")

        c.commit()


def save_document(filename, version_label, page_num, instruments,
                  page_width=None, page_height=None, source="ocr"):
    """
    Save one document's instrument list.

    Returns:
        new document_id
    """
    init_db()
    _ensure_columns()

    with _conn() as c:
        cur = c.cursor()
        cur.execute(
            "INSERT INTO documents "
            "(filename, version_label, page_num, page_width, page_height, "
            " extracted_at, instrument_count, source) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                filename,
                version_label,
                page_num,
                int(page_width) if page_width else None,
                int(page_height) if page_height else None,
                datetime.utcnow(),
                len(instruments),
                source,
            ),
        )
        doc_id = cur.lastrowid

        rows = []
        for r in instruments:
            rows.append((
                doc_id,
                r.get("func", "") or "",
                r.get("system_code") or "",
                r.get("component_id") or "",
                ", ".join(r.get("pipe_sizes", []) or []),
                float(r.get("confidence", 0.0)),
                int(r.get("x", 0)),
                int(r.get("y", 0)),
                int(r.get("w", 0)),
                int(r.get("h", 0)),
            ))

        cur.executemany(
            "INSERT INTO instruments "
            "(document_id, func, system_code, component_id, pipe_sizes, "
            " confidence, x, y, w, h) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        c.commit()
    return doc_id


def list_documents():
    init_db()
    _ensure_columns()
    with _conn() as c:
        df = pd.read_sql_query(
            "SELECT id, filename, version_label, page_num, "
            "       page_width, page_height, "
            "       extracted_at, instrument_count, source "
            "FROM documents ORDER BY extracted_at DESC",
            c,
        )
    return df


def get_document_meta(document_id):
    """Return a dict with metadata for one document."""
    init_db()
    with _conn() as c:
        df = pd.read_sql_query(
            "SELECT * FROM documents WHERE id = ?",
            c, params=(document_id,),
        )
    return df.iloc[0].to_dict() if not df.empty else None


def get_instruments(document_id):
    init_db()
    _ensure_columns()
    with _conn() as c:
        df = pd.read_sql_query(
            "SELECT func, system_code, component_id, pipe_sizes, "
            "       confidence, x, y, w, h "
            "FROM instruments WHERE document_id = ? "
            "ORDER BY y, x",
            c, params=(document_id,),
        )
    return df


def delete_document(document_id):
    with _conn() as c:
        c.execute("DELETE FROM instruments WHERE document_id = ?", (document_id,))
        c.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        c.commit()


def clear_all():
    with _conn() as c:
        c.execute("DELETE FROM instruments")
        c.execute("DELETE FROM documents")
        c.commit()