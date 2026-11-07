import json
import sqlite3
import pathlib
import sys

sys.path.append("tools")
from build_script import transform, get_span

conn = sqlite3.connect("rose_translation.sqlite")
conn.row_factory = sqlite3.Row

delivery_dir = pathlib.Path("translation_delivery")

jsonl_files = sorted(list(delivery_dir.rglob("*.jsonl")))
jsonl_files = [p for p in jsonl_files if p.name != "coverage_manifest.jsonl"]

print(f"Found {len(jsonl_files)} delivery JSONL files.")

total_delivered = 0
all_delivered_ids = set()
errors = []

for p in jsonl_files:
    count_in_file = 0
    with open(p, "r", encoding="utf-8") as f:
        for line_idx, line in enumerate(f, 1):
            count_in_file += 1
            total_delivered += 1
            data = json.loads(line)
            sid = data["id"]
            if sid in all_delivered_ids:
                errors.append(f"Duplicate id {sid} in {p}")
            all_delivered_ids.add(sid)
            
            # Check DB
            db_row = conn.execute("SELECT * FROM segments WHERE id=?", (sid,)).fetchone()
            if not db_row:
                errors.append(f"ID {sid} not in DB (file {p})")
                continue
                
            orig_ja = db_row["original_ja"]
            orig_sha = db_row["original_sha256"]
            
            if data["source_sha256"] != orig_sha:
                errors.append(f"SHA mismatch for {sid} in {p}")
                
            zh = data["translation_zh"]
            if orig_ja.count("@") != zh.count("@"):
                errors.append(f"@ count mismatch for {sid} in {p}")
                
            try:
                zh.encode("gbk")
            except Exception as e:
                errors.append(f"GBK encode error for {sid} in {p}: {e}")
                
    print(f"  {p.relative_to(delivery_dir).as_posix()}: {count_in_file} lines")

print("-" * 60)
print(f"Total delivered records audited: {total_delivered}")
print(f"Total unique IDs audited: {len(all_delivered_ids)}")
print(f"Total audit errors: {len(errors)}")

if errors:
    print("Top 10 errors:")
    for err in errors[:10]:
        print(" ", err)
    sys.exit(1)
else:
    print("ALL DELIVERED CHAPTERS PASSED 100% INDEPENDENT AUDIT!")
