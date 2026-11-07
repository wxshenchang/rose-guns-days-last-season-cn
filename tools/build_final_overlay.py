"""Assemble the reviewed story and UI into one isolated GBK script."""
import json
from pathlib import Path

from build_gbk import BASELINE, CN_SHA, KNOWN_SHA, ROOT, SRC, USABLE_STATES, classify_pair, decoded_lines, sha
from align_cn_patch import labels
from build_script import transform

FINAL = ROOT / 'translation_final'
DESTINATION = ROOT / 'builds' / 'final_review_candidate'
SUPPLEMENT_TARGETS = {'L170886': 170864, 'L206349': 206327, 'L207472': 207450}


def read_jsonl(path):
    with path.open(encoding='utf-8') as stream:
        return [json.loads(line) for line in stream]


def build():
    source_raw, source = decoded_lines(SRC, KNOWN_SHA, 'cp932')
    base_raw, base = decoded_lines(BASELINE, CN_SHA, 'gbk')
    story = {r['id']:r for path in FINAL.glob('season*/*.jsonl') for r in read_jsonl(path)}
    assert len(story) == 39487
    for ident, row in story.items():
        assert row['source_sha256'] == sha(source_raw[int(ident[1:])-1]), ident
    patches = {}
    covered = set()

    def patch(start, end, rendered):
        assert 1 <= start <= end <= len(base) and start not in patches
        assert all('\r' not in line and '\n' not in line for line in rendered)
        patches[start] = (end, rendered)

    def cover(ids):
        for ident in ids:
            assert ident not in covered, ident
            covered.add(ident)

    for filename in ('integration_comment_anchors.jsonl','integration_reconciled.jsonl'):
        for row in read_jsonl(FINAL/filename):
            ident, target = row['id'], row['baseline_line']
            assert story[ident]['source_sha256'] == row['source_sha256']
            assert row['baseline_sha256'] == sha(base_raw[target-1])
            patch(target, target, [row['script_zh']])
            cover([ident])
    for row in read_jsonl(FINAL/'integration_spans.jsonl'):
        targets = row['baseline_lines']
        assert targets == list(range(targets[0],targets[-1]+1))
        assert [sha(base_raw[p-1]) for p in targets] == row['baseline_sha256']
        assert [story[ident]['source_sha256'] for ident in row['ids']] == row['source_sha256']
        patch(targets[0], targets[-1], row['script_zh'])
        cover(row['ids'])
    for line in (ROOT/'scratch/integration_alignment.tsv').read_text(encoding='utf-8').splitlines():
        number, target, state = line.split('\t')
        ident = f'L{int(number):06}'
        if ident in covered:
            continue
        assert state in USABLE_STATES and target, ident
        j,p = int(number)-1,int(target)-1
        assert classify_pair(source[j],base[p])[0] == state
        rendered,_ = transform(story[ident],story[ident]['translation_zh'],base[p],'gbk')
        patch(p+1,p+1,[rendered])
        cover([ident])
    assert covered == set(story)

    for row in read_jsonl(FINAL/'supplemental.jsonl'):
        ident = row['id']
        n,target = int(ident[1:]),SUPPLEMENT_TARGETS[ident]
        before = row['locked_prefix']+row['source_ja']+row['locked_suffix']
        assert source[n-1] == base[target-1] == before
        assert row['source_sha256'] == sha(source_raw[n-1])
        patch(target,target,[row['locked_prefix']+row['translation_zh']+row['locked_suffix']])
        cover([ident])
    assert len(covered) == 39490

    ui = read_jsonl(FINAL/'ui_review.jsonl') + read_jsonl(FINAL/'ui_review_followup.jsonl')
    for row in ui:
        n,target = int(row['id'][1:]),row['baseline_line']
        assert row['source_sha256'] == sha(source_raw[n-1])
        assert row['baseline_sha256'] == sha(base_raw[target-1])
        patch(target,target,[row['script_zh']])
        cover([row['id']])

    assert base[44] == 'defaultfont "ＭＳ ゴシック"'
    patch(45,45,['defaultfont "NSimSun"'])

    cursor = 1
    chunks = []
    for start,(end,rendered) in sorted(patches.items()):
        assert start >= cursor, f'Overlapping replacement at baseline line {start}'
        chunks.extend(base_raw[cursor-1:start-1])
        line_end = base_raw[start-1][len(base_raw[start-1].rstrip(b'\r\n')):]
        if start == 45:
            # Match the font line shipped in the manually verified candidate.
            line_end = b'\r\n'
        assert line_end in (b'\r\n',b'\n')
        chunks.extend(line.encode('gbk')+line_end for line in rendered)
        cursor = end+1
    chunks.extend(base_raw[cursor-1:])
    result = b''.join(chunks)
    assert [name for _,name in labels(result.decode('gbk').splitlines())] == [name for _,name in labels(base)]
    assert len(result.splitlines())==len(base)+sum(len(text)-(end-start+1) for start,(end,text) in patches.items())
    return result, dict(story_rows=39490,ui_rows=len(ui),encoding='GBK',default_font='NSimSun',sha256=sha(result),
                        source_sha256=KNOWN_SHA,baseline_sha256=CN_SHA,validation='static_only')


if __name__ == '__main__':
    payload, report = build()
    DESTINATION.mkdir(exist_ok=True)
    (DESTINATION/'00.txt').write_bytes(payload)
    (DESTINATION/'build_report.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))
