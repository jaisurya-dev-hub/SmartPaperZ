import sqlite3
from flask import g, current_app

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
  pw_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'user' CHECK(role IN('user','admin')),
  active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS colleges(id INTEGER PRIMARY KEY, name TEXT NOT NULL, norm TEXT NOT NULL, state TEXT NOT NULL,
  city TEXT, university TEXT, status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN('pending','approved','rejected')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP, UNIQUE(norm,state));
CREATE TABLE IF NOT EXISTS exams(id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE, category TEXT NOT NULL, body TEXT);
CREATE TABLE IF NOT EXISTS papers(id INTEGER PRIMARY KEY, title TEXT NOT NULL, category TEXT NOT NULL,
  college_id INTEGER REFERENCES colleges(id) ON DELETE SET NULL, exam_id INTEGER REFERENCES exams(id) ON DELETE SET NULL,
  course TEXT, subject TEXT, year INTEGER, semester TEXT, language TEXT, stage TEXT, description TEXT,
  stored_name TEXT, sha256 TEXT UNIQUE, source_url TEXT,
  status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN('pending','approved','rejected','removed')),
  featured INTEGER NOT NULL DEFAULT 0, downloads INTEGER NOT NULL DEFAULT 0,
  uploader_id INTEGER REFERENCES users(id) ON DELETE SET NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE INDEX IF NOT EXISTS ix_papers_status_year ON papers(status,year);
CREATE INDEX IF NOT EXISTS ix_papers_college ON papers(college_id);
CREATE INDEX IF NOT EXISTS ix_papers_exam ON papers(exam_id);
CREATE TABLE IF NOT EXISTS bookmarks(user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
  paper_id INTEGER REFERENCES papers(id) ON DELETE CASCADE, PRIMARY KEY(user_id,paper_id));
CREATE TABLE IF NOT EXISTS reports(id INTEGER PRIMARY KEY, paper_id INTEGER NOT NULL REFERENCES papers(id) ON DELETE CASCADE,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, reason TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'open', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS admin_log(id INTEGER PRIMARY KEY, admin_id INTEGER, action TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
"""

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db

def q(sql, *a): return get_db().execute(sql, a).fetchall()
def one(sql, *a): return get_db().execute(sql, a).fetchone()
def run(sql, *a):
    d = get_db(); c = d.execute(sql, a); d.commit(); return c.lastrowid

def init_app(app):
    @app.teardown_appcontext
    def close(_):
        d = g.pop("db", None)
        if d: d.close()

def init_db():
    get_db().executescript(SCHEMA)
