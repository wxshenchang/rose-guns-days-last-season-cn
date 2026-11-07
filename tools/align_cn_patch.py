"""Build a local reference index for the recovered RGD 1.5 script."""

import argparse
import collections
import difflib
import json
import pathlib
import re
import sqlite3

from build_script import KNOWN_SHA, ROOT, SRC, get_span, sha, transform

CN_SHA = "df7bc9cd10fb2740d7739b2546247a5088fe46b29a338d1c32879aeafef96f50"
XOR84 = bytes(i ^ 0x84 for i in range(256))
LABEL = re.compile(r"^[ \t]*\*([a-zA-Z0-9_]+)(?:[ \t]*;.*)?[ \t]*$")
KANA = re.compile(r"[\u3041-\u30fa\uff66-\uff9f]")
HAN = re.compile(r"[\u3400-\u9fff]")


def read_script(path, codec, expected_sha):
    data = path.read_bytes()
    if sha(data) != expected_sha:
        raise ValueError(f"Unexpected script SHA-256: {path}")
    return data.translate(XOR84).decode(codec).splitlines()


def labels(lines):
    return [(i, match.group(1)) for i, line in enumerate(lines)
            if (match := LABEL.fullmatch(line))]


def classify_pair(original, reference):
    if original == reference:
        return "exact", None, None
    (prefix, _, suffix), kind = get_span(original)
    try:
        (ref_prefix, body, ref_suffix), ref_kind = get_span(reference)
        if (prefix, suffix, kind) != (ref_prefix, ref_suffix, ref_kind):
            return "boundary_mismatch", None, None
    except ValueError:
        return "boundary_mismatch", None, None
    try:
        transform({}, body, original, "gbk")
    except ValueError as exc:
        return "needs_script_review", body, str(exc)
    if KANA.search(body):
        return "contains_kana", body, None
    if not HAN.search(body):
        return "no_han", body, None
    return "candidate", body, None


def section_bounds(ja, cn):
    ja_labels, cn_labels = labels(ja), labels(cn)
    label_names = [name for _, name in ja_labels]
    if len(label_names) != len(set(label_names)) or label_names != [name for _, name in cn_labels]:
        raise ValueError("Expected the same unique ordered script labels")
    ja_bounds = [0, *(i for i, _ in ja_labels), len(ja)]
    cn_bounds = [0, *(i for i, _ in cn_labels), len(cn)]
    return len(label_names), zip(ja_bounds, ja_bounds[1:], cn_bounds, cn_bounds[1:])


def align(ja, cn, eligible, output):
    matched_labels, sections = section_bounds(ja, cn)
    counts = collections.Counter()
    for ja_start, ja_end, cn_start, cn_end in sections:
        match = difflib.SequenceMatcher(None, ja[ja_start:ja_end], cn[cn_start:cn_end])
        for tag, j1, j2, c1, c2 in match.get_opcodes():
            for ji in range(j1, j2):
                source_line = ja_start + ji
                row = eligible.get(source_line)
                if row is None:
                    continue
                original = ja[source_line]
                if row["original_ja"] != original:
                    raise ValueError("Database source mismatch: " + row["id"])
                if tag not in ("equal", "replace") or j2 - j1 != c2 - c1:
                    counts["unequal_span"] += 1
                    continue
                cn_line = cn_start + c1 + ji - j1
                state, body, issue = classify_pair(original, cn[cn_line])
                counts[state] += 1
                if body is None:
                    continue
                (prefix, source_body, suffix), _ = get_span(original)
                output.write(json.dumps({
                    "id": row["id"], "source_sha256": row["original_sha256"],
                    "source_line": source_line + 1, "patch_line": cn_line + 1,
                    "script_label": row["script_label"], "speaker_code": row["speaker_code"],
                    "source_ja": source_body, "reference_zh": body,
                    "locked_prefix": prefix, "locked_suffix": suffix,
                    "classification": state, "script_issue": issue,
                }, ensure_ascii=False) + "\n")
    if sum(counts.values()) != len(eligible):
        raise ValueError("Alignment did not account for every eligible record")
    return matched_labels, dict(counts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--script", type=pathlib.Path, required=True, help="Recovered RGD 1.5 nscript.dat")
    parser.add_argument("--output", type=pathlib.Path, required=True, help="New output directory")
    args = parser.parse_args()
    ja = read_script(SRC, "cp932", KNOWN_SHA)
    cn = read_script(args.script, "gbk", CN_SHA)
    with sqlite3.connect((ROOT / "rose_translation.sqlite").as_uri() + "?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        eligible = {row["line_no"] - 1: row for row in conn.execute("""
            SELECT id,line_no,original_ja,original_sha256,script_label,speaker_code
            FROM segments WHERE confidence='high' AND category IN ('dialogue','narration')
        """)}
    conn.close()
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "reference.jsonl").open("x", encoding="utf-8", newline="\n") as output:
        count, states = align(ja, cn, eligible, output)
    report = {
        "source_sha256": KNOWN_SHA, "patch_script_sha256": CN_SHA, "matched_labels": count,
        "source_lines": len(ja), "patch_lines": len(cn), "eligible": len(eligible),
        "states": states, "method": "exact line anchors within matching labels, equal-size changed spans",
        "reviewed_translations": 0,
    }
    (args.output / "alignment_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
