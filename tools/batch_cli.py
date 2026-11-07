"""Offline translation queue CLI; never sends content to model APIs by itself.

Commands:
  python batch_cli.py status
  python batch_cli.py export --limit 30
  python batch_cli.py import-drafts --file batch_answers.jsonl --model Terra
  python batch_cli.py qa
"""
import argparse
import datetime
import hashlib
import json
import pathlib
import sqlite3
from build_script import get_span,transform

BASE=pathlib.Path("D:/ai/rose_localization_workspace")
DB=BASE/"rose_translation.sqlite"
def conn_open():
 c=sqlite3.connect(DB)
 c.row_factory=sqlite3.Row
 c.execute("PRAGMA foreign_keys=ON")
 return c
def show_status(c):
 print("SEGMENTS",c.execute("SELECT COUNT(*) FROM segments").fetchone()[0])
 print("STATUS",[tuple(r) for r in c.execute("SELECT status,COUNT(*) FROM segments GROUP BY status")])
 print("TRANSLATIONS",c.execute("SELECT COUNT(*) FROM segments WHERE translation_zh IS NOT NULL").fetchone()[0])
 print("GLOSSARY",c.execute("SELECT COUNT(*) FROM glossary").fetchone()[0])
 print("REVIEW_EVENTS",c.execute("SELECT COUNT(*) FROM review_events").fetchone()[0])


def context_before(c, row):
    preceding = c.execute("""SELECT original_ja FROM segments WHERE
        line_no<? AND script_label=? AND category IN ('dialogue','narration')
        ORDER BY line_no DESC LIMIT 3""", (row["line_no"], row["script_label"])).fetchall()
    return [item["original_ja"] for item in reversed(preceding)]


def export_batch(c,limit):
 if limit<1 or limit>100:raise ValueError("Limit must be from 1 to 100")
 selected=c.execute("""SELECT * FROM segments WHERE status='ready'
    AND translation_zh IS NULL ORDER BY line_no LIMIT ?""",(limit,)).fetchall()
 if not selected:
  print("NO_PENDING_SEGMENTS");return
 outdir=BASE/"batches";outdir.mkdir(exist_ok=True)
 stamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
 path=outdir/("terra_pilot_"+stamp+".jsonl")
 exported=[]
 with path.open("x",encoding="utf-8",newline="\n") as f:
  for row in selected:
   span,_=get_span(row["original_ja"])
   prefix,payload,suffix=span
   item={"id":row["id"],"source_sha256":row["original_sha256"],
      "line_no":row["line_no"],"script_label":row["script_label"],
      "speaker_code":row["speaker_code"],"kind":row["category"],
      "source_ja":payload,"context_before_ja":context_before(c,row),
      "locked_prefix":prefix,"locked_suffix":suffix,
      "pagebreak_marker_count":payload.count("@"),
      "translation_zh":None}
   f.write(json.dumps(item,ensure_ascii=False)+"\n")
   exported.append(item["id"])
 print(json.dumps({"batch_file":str(path),"rows":len(exported),"first_id":exported[0],
    "last_id":exported[-1],"model_calls":0,"note":"No request sent; JSONL only."},ensure_ascii=True))


def export_reference(c, limit):
    if not 1 <= limit <= 100:
        raise ValueError("Limit must be from 1 to 100")
    reference = BASE / "baseline_1_5" / "alignment" / "reference.jsonl"
    ready = dict(c.execute("""SELECT id,original_sha256 FROM segments
        WHERE status='ready' AND translation_zh IS NULL"""))
    selected = []
    with reference.open(encoding="utf-8") as source:
        for line in source:
            item = json.loads(line)
            ident = item["id"]
            if item["classification"] != "candidate" or ident not in ready:
                continue
            if item["source_sha256"] != ready[ident]:
                raise ValueError("Reference source hash mismatch: " + ident)
            item["translation_zh"] = item.pop("reference_zh")
            selected.append(item)
            if len(selected) == limit:
                break
    write_queue("reference_1_5", selected)
def import_drafts(c,file,model):
 model=model.strip()
 if not model:raise ValueError("Model name required")
 lines=file.read_text(encoding="utf-8").splitlines()
 if not lines:raise ValueError("Input empty")
 payloads=[json.loads(x) for x in lines]
 if len(payloads)>100:raise ValueError("Batch too large")
 seen=set()
 c.execute("BEGIN IMMEDIATE")
 try:
  for obj in payloads:
   ident=obj["id"]
   if ident in seen:raise ValueError("Duplicate ID: "+ident)
   seen.add(ident)
   row=c.execute("SELECT * FROM segments WHERE id=?",(ident,)).fetchone()
   if not row or row["status"]!="ready" or row["translation_zh"] is not None:
    raise ValueError("Not ready or already drafted: "+ident)
   if obj.get("source_sha256")!=row["original_sha256"]:
    raise ValueError("Source hash mismatch: "+ident)
   text=obj["translation_zh"]
   transform(dict(row),text,row["original_ja"],"utf-8")
   note=obj.get("review_notes")
   if note is not None and not isinstance(note,str):
    raise ValueError("review_notes must be a string: "+ident)
   c.execute("""UPDATE segments SET translation_zh=?,status='draft',provenance=?
      WHERE id=?""",(text,model,ident))
   c.execute("""INSERT INTO review_events(segment_id,reviewer,old_text,
      new_text,decision,reason) VALUES (?,?,NULL,?,'draft',?)""",
      (ident,model,text,(note or "").strip() or "Draft imported for independent review"))
  c.commit()
 except Exception:
  c.rollback()
  raise
 print("IMPORTED_DRAFTS",len(payloads),"MODEL",model)

def text_sha256(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def latest_event(c, ident):
    return c.execute("""SELECT * FROM review_events WHERE segment_id=?
        ORDER BY event_id DESC LIMIT 1""", (ident,)).fetchone()


def write_queue(stage, records):
    if not records:
        print("NO_PENDING_SEGMENTS")
        return
    outdir = BASE / "batches"
    outdir.mkdir(exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = outdir / f"{stage}_{stamp}.jsonl"
    with path.open("x", encoding="utf-8", newline="\n") as output:
        for record in records:
            output.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(json.dumps({"batch_file": str(path), "rows": len(records), "model_calls": 0}))


def export_review_queue(c, stage, limit):
    if not 1 <= limit <= 100:
        raise ValueError("Limit must be from 1 to 100")
    expected_status = "draft" if stage == "review" else "review"
    c.execute("BEGIN")
    rows = c.execute("""SELECT * FROM segments WHERE status=?
        ORDER BY line_no LIMIT ?""", (expected_status, limit)).fetchall()
    records = []
    for row in rows:
        event = latest_event(c, row["id"])
        expected_decisions = ("draft", "reject") if stage == "review" else ("pass", "revise")
        if not event or event["decision"] not in expected_decisions or event["new_text"] != row["translation_zh"]:
            raise ValueError("Translation and review history disagree: " + row["id"])
        (prefix, body, suffix), _ = get_span(row["original_ja"])
        records.append({
            "id": row["id"], "source_sha256": row["original_sha256"],
            "text_sha256": text_sha256(row["translation_zh"]), "event_id": event["event_id"],
            "line_no": row["line_no"], "script_label": row["script_label"],
            "speaker_code": row["speaker_code"], "kind": row["category"],
            "source_ja": body, "context_before_ja": context_before(c, row),
            "locked_prefix": prefix, "locked_suffix": suffix, "current_zh": row["translation_zh"],
            "previous_decision": event["decision"], "previous_reason": event["reason"],
            "decision": None, "reason": None,
        })
    c.commit()
    write_queue(stage, records)


def import_decisions(c, file, actor, stage):
    actor = actor.strip()
    if not actor:
        raise ValueError("Reviewer or approver name required")
    payloads = [json.loads(line) for line in file.read_text(encoding="utf-8").splitlines()]
    if not 1 <= len(payloads) <= 100:
        raise ValueError("Batch must contain 1 to 100 records")
    expected_status = "draft" if stage == "review" else "review"
    decisions = {"pass": "review", "revise": "review", "reject": "draft"} if stage == "review" else {"approve": "approved"}
    seen = set()
    with c:
        c.execute("BEGIN IMMEDIATE")
        for item in payloads:
            ident = item["id"]
            if ident in seen:
                raise ValueError("Duplicate ID: " + ident)
            seen.add(ident)
            row = c.execute("SELECT * FROM segments WHERE id=?", (ident,)).fetchone()
            if not row or row["status"] != expected_status or row["translation_zh"] is None:
                raise ValueError(f"Segment is not awaiting {stage}: {ident}")
            if actor.casefold() == (row["provenance"] or "").strip().casefold():
                raise ValueError("Draft author cannot review or approve: " + ident)
            current = row["translation_zh"]
            event = latest_event(c, ident)
            expected_decisions = ("draft", "reject") if stage == "review" else ("pass", "revise")
            if (item.get("source_sha256") != row["original_sha256"]
                or item.get("text_sha256") != text_sha256(current)
                or not event or event["decision"] not in expected_decisions
                or item.get("event_id") != event["event_id"] or event["new_text"] != current):
                raise ValueError("Stale source, translation, or review event: " + ident)
            decision = item.get("decision")
            reason = item.get("reason")
            if decision not in decisions or not isinstance(reason, str) or not reason.strip():
                raise ValueError("Valid decision and reason required: " + ident)
            if decision == "revise":
                new_text = item.get("translation_zh")
                if new_text == current:
                    raise ValueError("Use pass if the draft requires no edits: " + ident)
            else:
                if "translation_zh" in item:
                    raise ValueError("Only revise may supply replacement text: " + ident)
                new_text = current
            if decision != "reject":
                transform(dict(row), new_text, row["original_ja"], "utf-8")
            c.execute("UPDATE segments SET translation_zh=?,status=? WHERE id=?",
                      (new_text, decisions[decision], ident))
            c.execute("""INSERT INTO review_events(segment_id,reviewer,old_text,new_text,decision,reason)
                VALUES (?,?,?,?,?,?)""", (ident, actor, current, new_text, decision, reason.strip()))
    print(json.dumps({"stage": stage, "imported": len(payloads), "actor": actor}))


def approved_rows(c):
    rows = c.execute("""WITH latest AS (
            SELECT segment_id,MAX(event_id) AS event_id FROM review_events GROUP BY segment_id
        )
        SELECT s.id,s.line_no,s.original_sha256,s.translation_zh,s.original_ja,
        e.event_id,e.decision,e.new_text
        FROM segments s LEFT JOIN latest l ON l.segment_id=s.id
        LEFT JOIN review_events e ON e.event_id=l.event_id
        WHERE s.status='approved' ORDER BY s.line_no""").fetchall()
    if not rows:
        raise ValueError("No approved segments")
    for row in rows:
        if row["decision"] != "approve" or row["new_text"] != row["translation_zh"]:
            raise ValueError("Approval and translation disagree: " + row["id"])
        transform(dict(row), row["translation_zh"], row["original_ja"], "utf-8")
    return rows


def export_approved(c, path):
    rows = approved_rows(c)
    with path.open("x", encoding="utf-8", newline="\n") as output:
        for row in rows:
            output.write(json.dumps({"id": row["id"], "source_sha256": row["original_sha256"],
                                     "text_zh": row["translation_zh"], "approval_event_id": row["event_id"]},
                                    ensure_ascii=False) + "\n")
    print(json.dumps({"approved_file": str(path), "rows": len(rows)}))


def qa(c):
 rows=c.execute("""SELECT id,original_ja,translation_zh,status FROM segments
   WHERE translation_zh IS NOT NULL""").fetchall()
 fails=[]
 for r in rows:
  try:transform(dict(r),r["translation_zh"],r["original_ja"],"utf-8")
  except Exception as e:fails.append({"id":r["id"],"error":str(e)})
 print(json.dumps({"translations":len(rows),"structural_failures":len(fails),
   "failures":fails[:20],"approved":c.execute("SELECT COUNT(*) FROM segments WHERE status='approved'").fetchone()[0]},
   ensure_ascii=True))
def main():
 p=argparse.ArgumentParser()
 s=p.add_subparsers(dest="command",required=True)
 s.add_parser("status")
 q=s.add_parser("export");q.add_argument("--limit",type=int,default=30)
 reference=s.add_parser("export-reference")
 reference.add_argument("--limit",type=int,default=30)
 m=s.add_parser("import-drafts");m.add_argument("--file",type=pathlib.Path,required=True);m.add_argument("--model",required=True)
 for command, stage in (("export-review", "review"), ("export-approval", "approval")):
  queue=s.add_parser(command)
  queue.add_argument("--limit",type=int,default=30)
  queue.set_defaults(handler=lambda c,args,stage=stage:export_review_queue(c,stage,args.limit))
 for command, stage, flag in (("import-reviews", "review", "--reviewer"), ("approve", "approval", "--approver")):
  action=s.add_parser(command)
  action.add_argument("--file",type=pathlib.Path,required=True)
  action.add_argument(flag,dest="actor",required=True)
  action.set_defaults(handler=lambda c,args,stage=stage:import_decisions(c,args.file,args.actor,stage))
 approved=s.add_parser("export-approved")
 approved.add_argument("--file",type=pathlib.Path,required=True)
 s.add_parser("qa")
 args=p.parse_args()
 c=conn_open()
 try:
  if args.command=="status":show_status(c)
  elif args.command=="export":export_batch(c,args.limit)
  elif args.command=="export-reference":export_reference(c,args.limit)
  elif args.command=="import-drafts":import_drafts(c,args.file,args.model)
  elif args.command=="export-approved":export_approved(c,args.file)
  elif args.command=="qa":qa(c)
  else:args.handler(c,args)
 finally:c.close()
if __name__=="__main__":main()
