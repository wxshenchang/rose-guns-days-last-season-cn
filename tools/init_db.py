"""Build a local SQLite project catalog from the audited script.
No API calls, no game modification, no automatic translation.
"""
import collections
import hashlib
import json
import pathlib
import sqlite3
import sys

BASE=pathlib.Path("D:/ai/rose_localization_workspace")
GAME=next(pathlib.Path("D:/ai").glob("*/rose/*Last Season*"))
SOURCE=GAME/"nscript.dat"
RUN=BASE/"inventory_20261104_180717"
SHA_EXPECTED="4724fc5c37d2daadbde4eca874dc72da481786221238d50764a970e6a8053978"
DB=BASE/"rose_translation.sqlite"
if DB.exists():
    raise SystemExit("Database exists; refusing to overwrite: "+str(DB))
binary=SOURCE.read_bytes()
assert hashlib.sha256(binary).hexdigest()==SHA_EXPECTED
decoded=bytes(v^0x84 for v in binary)
lines=decoded.splitlines(keepends=True)
offsets=[]
pos=0
for raw in lines:
    offsets.append(pos)
    pos+=len(raw)
assert pos==len(decoded)
conn=sqlite3.connect(DB)
conn.execute("PRAGMA foreign_keys=ON")
conn.execute("PRAGMA journal_mode=WAL")
conn.executescript("""
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE segments (
 id TEXT PRIMARY KEY, line_no INTEGER NOT NULL UNIQUE,
 byte_offset INTEGER NOT NULL, raw_length INTEGER NOT NULL,
 original_sha256 TEXT NOT NULL,
 script_label TEXT, speaker_code TEXT, category TEXT NOT NULL,
 confidence TEXT NOT NULL, original_ja TEXT NOT NULL,
 translation_zh TEXT, status TEXT NOT NULL,
 provenance TEXT, notes TEXT,
 CHECK(status IN ('ready','needs_classification','draft','review','approved','blocked'))
);
CREATE INDEX idx_seg_status ON segments(status);
CREATE INDEX idx_seg_category ON segments(category);
CREATE INDEX idx_seg_label ON segments(script_label);
CREATE INDEX idx_seg_speaker ON segments(speaker_code);
CREATE TABLE glossary (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 original TEXT NOT NULL UNIQUE, translation TEXT, context TEXT,
 status TEXT NOT NULL DEFAULT 'proposed',
 source TEXT, reviewed_by TEXT,
 CHECK(status IN ('proposed','approved','rejected'))
);
CREATE TABLE characters (
 code TEXT PRIMARY KEY, name_ja TEXT, name_zh TEXT,
 speaking_style TEXT, status TEXT NOT NULL DEFAULT 'unconfirmed'
);
CREATE TABLE review_events (
 event_id INTEGER PRIMARY KEY AUTOINCREMENT, segment_id TEXT NOT NULL,
 created_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 reviewer TEXT NOT NULL, old_text TEXT, new_text TEXT,
 decision TEXT NOT NULL, reason TEXT,
 FOREIGN KEY(segment_id) REFERENCES segments(id)
);
CREATE TABLE model_runs (
 run_id INTEGER PRIMARY KEY AUTOINCREMENT,
 created_utc TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 model_id TEXT NOT NULL, effort TEXT,
 workflow_stage TEXT NOT NULL, input_count INTEGER DEFAULT 0,
 output_count INTEGER DEFAULT 0, estimated_cost REAL,
 status TEXT NOT NULL, notes TEXT
);
""")
conn.execute("INSERT INTO meta VALUES(?,?)",("source_sha256",SHA_EXPECTED))
conn.execute("INSERT INTO meta VALUES(?,?)",("source_path",str(SOURCE)))
conn.execute("INSERT INTO meta VALUES(?,?)",("inventory",RUN.name))
seen=set()
speakers=collections.Counter()
count=collections.Counter()
insert="INSERT INTO segments (id,line_no,byte_offset,raw_length,original_sha256,script_label,speaker_code,category,confidence,original_ja,status) VALUES (?,?,?,?,?,?,?,?,?,?,?)"
def insert_one(ident,lineno,label,speaker,category,confidence,original,status):
    if lineno in seen:
        raise RuntimeError("Duplicate source line: "+str(lineno))
    if not 1<=lineno<=len(lines):raise ValueError(lineno)
    raw=lines[lineno-1]
    text=raw.rstrip(b"\r\n").decode("cp932")
    if text!=original:raise RuntimeError("Source changed: "+ident)
    conn.execute(insert,(ident,lineno,offsets[lineno-1],len(raw),
        hashlib.sha256(raw).hexdigest(),label,speaker,category,confidence,original,status))
    seen.add(lineno)
    count[status]+=1
    count[category]+=1
    if speaker:speakers[speaker]+=1
with (RUN/"jp_candidates.jsonl").open(encoding="utf-8") as f:
    for s in f:
        r=json.loads(s)
        status="ready" if r["confidence"]=="high" else "needs_classification"
        insert_one(r["id"],r["source_line"],r["label"],r["speaker_code"],r["kind"],r["confidence"],r["source_ja"],status)
with (RUN/"unclassified_grouped.jsonl").open(encoding="utf-8") as f:
    for s in f:
        r=json.loads(s)
        if r["classification"]=="comment_only":continue
        insert_one("L%06d"%r["line"],r["line"],None,None,
            r["classification"],"needs_review",r["text"],"needs_classification")
for speaker,n in speakers.items():
    conn.execute("INSERT INTO characters(code) VALUES (?)",(speaker,))
conn.commit()
integrity=conn.execute("PRAGMA integrity_check").fetchone()[0]
assert integrity=="ok",integrity
expected=len(seen)
actual=conn.execute("SELECT COUNT(*) FROM segments").fetchone()[0]
assert expected==actual
summary={"db":str(DB),"integrity":integrity,"segments":actual,
    "status":{"ready":count["ready"],"needs_classification":count["needs_classification"]},
    "categories":{str(k):v for k,v in count.items() if k not in ("ready","needs_classification")},
    "characters_detected":len(speakers),
    "glossary_entries":0,
    "translation_count":0,
    "source_unchanged":hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SHA_EXPECTED}
(BASE/"db_init_report.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps(summary,ensure_ascii=True))
conn.close()
