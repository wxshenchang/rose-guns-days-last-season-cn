import json
import pathlib
import sys

sys.path.insert(0, "D:/ai/rose_localization_workspace/tools")

review_file = pathlib.Path("D:/ai/rose_localization_workspace/batches/review_20261104_193259_279317.jsonl")
lines = [json.loads(x) for x in review_file.read_text(encoding="utf-8").splitlines()]

# Decisions from reviewer Sol
reasons = [
    "准确传递原文含义，英文名大写规范，标点正确。",
    "旧译口吻自然，略作凝练贴合原文，表意准确流畅。",
    "保留 @ 停顿与轻快口吻，存档术语规范统一。",
    "成功补全 1.5 遗漏的「ノベルパートで（文字剧情部分）」，解决关键漏译。",
    "纠正 1.5 方位与按钮误译（原版明确为一番右上），存档术语统一。",
    "统一术语为存档模式，表意准确自然。",
    "修正 1.5 错误生造词「凸槽」，恢复「存档位」规范中文表达。",
    "保留 @ 停顿与全角空格排版，梅丽尔语气鲜活生动，修正标点空隙。",
    "旧译准确自然，符合复用原则，准予通过。",
    "修正 1.5 严重语气偏离（误将何とっ译为不知道为什么），准确还原推介核心玩法的雀跃口吻。",
    "消除旧译残留日文汉字「戦闘」，规范为简体中文「战斗」。",
    "人名敬称「敬礼寺先生」统一规范，旧译复用自然。",
    "敬礼寺粗犷老兵口吻贴切，@ 停顿准确完整。",
    "日文惯用句意译准确，逻辑比 1.5 显著提升，还原自己拍除祸患的含义。",
    "黑帮斗殴场景张力良好，对白节奏紧凑。",
    "消除旧译残留日文汉字「攻撃」，规范为简体中文「攻击」，@ 分页准确。",
    "人称与硬派语气契合敬礼寺江湖老手身份。",
    "系统教学用语清晰明确，打击标记定位准确。",
    "机制说明自然通顺，修正生硬语序。",
    "纠正 1.5 脑补的奇怪词汇，操作指令清晰准确。",
    "生动还原用鼠标挥击拍打的动作感与防御机制。",
    "剔除日式生造词「限制時間」「相应回数」，改为自然规范中文。",
    "UI 指示精准自然，消除日制汉语痕迹。",
    "纠正 1.5 将攻击次数误判为游戏回合数的逻辑错误。",
    "拟声表达生动，防守动作要领说明清晰。",
    "标点标准化，省略号规范为中文双三连点「……」。",
    "复用旧译优秀口语，保留停顿节奏与操作趣味。",
    "口吻地道传神，富有老派黑帮军官气势。",
    "呼喊声节奏感良好，标点合规完整。",
    "补足 1.5 漏译的「裏技（隐藏秘技）」，斯特拉神秘调侃的声线呈现到位。"
]

for item, reason in zip(lines, reasons):
    item["decision"] = "pass"
    item["reason"] = reason

review_file.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in lines) + "\n", encoding="utf-8")
print(f"Updated {len(lines)} review records with Sol pass decisions.")
