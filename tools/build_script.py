"""Reproducible, non-destructive script build prototype.
IMPORTANT: CP932 builds are not Chinese-capable. Chinese output requires
a separately validated Chinese-capable engine and a tested encoding profile.
"""
import argparse
import datetime
import hashlib
import json
import pathlib
import re

ROOT=pathlib.Path("D:/ai/rose_localization_workspace")
GAME=next(pathlib.Path("D:/ai").glob("*/rose/*Last Season*"))
SRC=GAME/"nscript.dat"
KNOWN_SHA="4724fc5c37d2daadbde4eca874dc72da481786221238d50764a970e6a8053978"
RUN=ROOT/"inventory_20261104_180717"
DIALOGUE=re.compile(r"^(\s*[a-zA-Z][a-zA-Z0-9_]{0,24}[\u300c\u300e\u3008\uff08])(.*)([\u300d\u300f\u3009\uff09][\\/@]?(?:;.*)?)$")
SPLIT_DIALOGUE=re.compile(r"^(\s*[a-zA-Z][a-zA-Z0-9_]{0,24}[\u300c\u300e\u3008\uff08])(.*)(/)$")
SPLIT_TAIL=re.compile(r"^([ \t\u3000]*)(.*)([\u300d\u300f\u3009\uff09][\\/]?(?:;.*)?)$")
INLINE_COMMAND_NARRATIVE=re.compile(r"^(\s*(?:(?:if|notif|inc|dec|mov)\b.*?:\s*)+)(.*)([\\/@](?:;.*)?)$")
NARRATIVE=re.compile(r"^([ \t\u3000]*)(.*)([\\/@](?:;.*)?)$")
TOKENS=re.compile(r"(?:[%$][a-zA-Z0-9_]+|@[a-zA-Z0-9_]+)")

def sha(data):return hashlib.sha256(data).hexdigest()

def get_span(line):
    m=DIALOGUE.fullmatch(line)
    if m:return m.groups(),"dialogue"
    m=SPLIT_DIALOGUE.fullmatch(line)
    if m:return m.groups(),"dialogue"
    m=SPLIT_TAIL.fullmatch(line)
    if m:
        c=m.group(2).lstrip("@ \t\u3000")
        if c and not c[0].isascii():
            return m.groups(),"dialogue_tail"
    m=INLINE_COMMAND_NARRATIVE.fullmatch(line)
    if m and m.group(2):
        c=m.group(2).lstrip("@ \t\u3000")
        if c and not c[0].isascii():
            return m.groups(),"narration"
    m=NARRATIVE.fullmatch(line)
    if m and m.group(2):
        c=m.group(2).lstrip("@ \t\u3000")
        if c and not c[0].isascii():
            return m.groups(),"narration"
    raise ValueError("Line has no validated dialogue/narrative syntax")

def transform(row,new_text,original,codec):
    parts,kind=get_span(original)
    prefix,body,suffix=parts
    if not isinstance(new_text,str) or not new_text.strip():
        raise ValueError("Translation must be a nonempty string")
    if any(x in new_text for x in ("\r","\n","\\","/",";","\"")):
        raise ValueError("Text cannot contain raw linebreaks, terminators, comments or quote delimiters")
    if body.count("@")!=new_text.count("@"):
        raise ValueError("Page-break @ marker count mismatch")
    if TOKENS.findall(body)!=TOKENS.findall(new_text):
        raise ValueError("Dynamic placeholder sequence mismatch")
    if prefix.endswith("\u300c") and "\u300d" in new_text:
        raise ValueError("Closing dialogue bracket in translated payload")
    if prefix.endswith("\u300e") and "\u300f" in new_text:
        raise ValueError("Closing dialogue bracket in translated payload")
    if prefix.endswith("\u3008") and "\u3009" in new_text:
        raise ValueError("Closing dialogue bracket in translated payload")
    if prefix.endswith("\uff08") and "\uff09" in new_text:
        raise ValueError("Closing dialogue bracket in translated payload")
    result=prefix+new_text+suffix
    result.encode(codec)
    return result,kind

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--manifest",type=pathlib.Path)
    parser.add_argument("--codec",choices=["cp932"],default="cp932")
    args=parser.parse_args()
    raw=SRC.read_bytes()
    if sha(raw)!=KNOWN_SHA:raise RuntimeError("Original source changed - aborting")
    decoded=bytes(x^0x84 for x in raw)
    # CP932 has non-bijective mappings. Never reencode unchanged text:
    # preserve all original line bytes and replace only validated lines.
    global_cp932_roundtrip_is_exact = decoded.decode("cp932").encode("cp932")==decoded
    lines=decoded.splitlines(keepends=True)
    index={}
    for x in (RUN/"jp_candidates.jsonl").open(encoding="utf-8"):
        row=json.loads(x);index[row["id"]]=row
    changes={}
    if args.manifest:
        for item in map(json.loads,args.manifest.read_text(encoding="utf-8").splitlines()):
            ident=item["id"]
            if ident in changes or ident not in index:raise ValueError("Duplicate/unknown id: "+ident)
            if item.get("source_sha256")!=index[ident]["original_line_sha256"]:
                raise ValueError("Source hash missing or mismatched: "+ident)
            changes[ident]=item["text_zh"]
    detail=[]
    for ident,translated in changes.items():
        record=index[ident];i=record["source_line"]-1
        before=lines[i]
        if sha(before)!=record["original_line_sha256"]:raise RuntimeError("Changed source line: "+ident)
        clean=before.rstrip(b"\r\n")
        newline=before[len(clean):]
        original=clean.decode("cp932")
        updated,kind=transform(record,translated,original,args.codec)
        lines[i]=updated.encode(args.codec)+newline
        detail.append({"id":ident,"kind":kind,"before_bytes":len(before),"after_bytes":len(lines[i])})
    result=bytes(v^0x84 for v in b"".join(lines))
    if not changes and result!=raw:raise AssertionError("No-op roundtrip changed bytes")
    if args.codec=="cp932":
        check=bytes(v^0x84 for v in result).decode("cp932")
        if len(check.splitlines())!=len(decoded.decode("cp932").splitlines()):
            raise AssertionError("Line structure changed")
    destination=ROOT/"builds"/("build_"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
    destination.mkdir(parents=True,exist_ok=False)
    output=destination/"nscript.dat"
    output.write_bytes(result)
    report={"source_sha256":sha(raw),"result_sha256":sha(result),"no_op_identical":result==raw,"global_cp932_roundtrip_exact":global_cp932_roundtrip_is_exact,"codec":args.codec,"engine_compatibility_verified":False,"changes":detail,"output":str(output)}
    (destination/"build_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=True))

if __name__=="__main__":main()
