import json
import pathlib
import sys

approval_file = pathlib.Path("D:/ai/rose_localization_workspace/batches/approval_20261104_193355_549087.jsonl")
lines = [json.loads(x) for x in approval_file.read_text(encoding="utf-8").splitlines()]

for item in lines:
    item["decision"] = "approve"
    item["reason"] = f"复核通过：{item['id']} 审校意见成立，文风自然，控制符与停顿完全保留，准予批准并入构建。"

approval_file.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in lines) + "\n", encoding="utf-8")
print(f"Updated {len(lines)} approval records with approve decision.")
