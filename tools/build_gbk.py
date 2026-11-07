"""Build a GBK 00.txt overlay from approved translations for the RGD 1.5 engine."""

import argparse
import difflib
import json
import pathlib
from contextlib import closing

import batch_cli
from align_cn_patch import CN_SHA, XOR84, classify_pair, section_bounds
from build_script import KNOWN_SHA, ROOT, SRC, sha, transform

BASELINE = ROOT / "baseline_1_5" / "recovered" / "nscript.dat"
USABLE_STATES = {"exact", "candidate", "contains_kana", "no_han"}


def decoded_lines(path, digest, codec):
    encoded = path.read_bytes()
    if sha(encoded) != digest:
        raise ValueError(f"Unexpected script SHA-256: {path}")
    raw = encoded.translate(XOR84).splitlines(keepends=True)
    return raw, [line.rstrip(b"\r\n").decode(codec) for line in raw]


def paired_lines(ja, cn, wanted):
    _, sections = section_bounds(ja, cn)
    remaining = iter(sorted(wanted))
    source = next(remaining, None)
    for j_start, j_end, c_start, c_end in sections:
        if source is None:
            break
        if source >= j_end:
            continue
        jp_section = ja[j_start:j_end]
        cn_section = cn[c_start:c_end]
        opcodes = difflib.SequenceMatcher(None, jp_section, cn_section).get_opcodes()
        while source is not None and source < j_end:
            original = ja[source]
            comment = ";" + original
            target = None
            method = None
            if jp_section.count(original) == 1 and cn_section.count(comment) == 1:
                after = c_start + cn_section.index(comment) + 1
                if after < c_end and classify_pair(original, cn[after])[0] in USABLE_STATES:
                    target, method = after, "original_comment"
            if target is None:
                for tag, j1, j2, c1, c2 in opcodes:
                    if j1 <= source - j_start < j2 and tag in ("equal", "replace") and j2 - j1 == c2 - c1:
                        possible = c_start + c1 + source - j_start - j1
                        if classify_pair(original, cn[possible])[0] in USABLE_STATES:
                            target, method = possible, "matched_span"
                        break
            if target is None:
                raise ValueError(f"No structurally compatible 1.5 line for original line {source + 1}")
            yield source, target, method
            source = next(remaining, None)
    if source is not None:
        raise ValueError(f"Original line out of range: {source + 1}")


def build(rows):
    original_raw, ja = decoded_lines(SRC, KNOWN_SHA, "cp932")
    cn_raw, cn = decoded_lines(BASELINE, CN_SHA, "gbk")
    wanted = {row["line_no"] - 1: row for row in rows}
    for source, row in wanted.items():
        if (not 0 <= source < len(ja) or ja[source] != row["original_ja"]
                or sha(original_raw[source]) != row["original_sha256"]):
            raise ValueError("Approved row does not match the original script: " + row["id"])
        transform(row, row["translation_zh"], ja[source], "gbk")
    details = []
    used = set()
    for source, target, method in paired_lines(ja, cn, wanted):
        row = wanted[source]
        if target in used:
            raise ValueError(f"Multiple original lines point to 1.5 line {target + 1}")
        used.add(target)
        updated, _ = transform(row, row["translation_zh"], cn[target], "gbk")
        raw = cn_raw[target]
        newline = raw[len(raw.rstrip(b"\r\n")):]
        cn_raw[target] = updated.encode("gbk") + newline
        details.append({"id": row["id"], "source_line": source + 1, "patch_line": target + 1,
                        "approval_event_id": row["event_id"], "alignment": method})
    result = b"".join(cn_raw)
    return result, {"original_sha256": KNOWN_SHA, "baseline_sha256": CN_SHA,
                    "sha256": sha(result), "encoding": "gbk", "changes": details}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=pathlib.Path, required=True, help="New build directory")
    args = parser.parse_args()
    with closing(batch_cli.conn_open()) as conn:
        rows = batch_cli.approved_rows(conn)
    result, report = build(rows)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "00.txt").write_bytes(result)
    (args.output / "build_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output / "00.txt"), "sha256": report["sha256"],
                      "approved_rows": len(report["changes"])}))


if __name__ == "__main__":
    main()
