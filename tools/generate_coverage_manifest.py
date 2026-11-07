import json
import sqlite3
import collections
import pathlib

BASE_DIR = pathlib.Path("D:/ai/rose_localization_workspace")
DB_PATH = BASE_DIR / "rose_translation.sqlite"
REF_PATH = BASE_DIR / "baseline_1_5/alignment/reference.jsonl"
DELIVERY_DIR = BASE_DIR / "translation_delivery"

def get_season_and_chapter(label, line_no):
    if label is None:
        return ("System / Excluded", "sys_common", "系统/通用脚本（排除项）")
    lbl = str(label)
    if lbl == "*tutorial":
        return ("Season 1", "s01_tutorial", "新手教学 (*tutorial)")
    elif lbl == "*dif_level_chousei":
        return ("Season 4 (Last Season)", "s04_ch05_dif_level", "难度调整 (*dif_level_chousei)")
    
    # Season 1
    if lbl.startswith("*rgd1_") or lbl in ("*map_1", "*map_2", "*map_3", "*mapmode1_end"):
        return ("Season 1", "s01_ch01", "第一季 第1章 (*rgd1_opning, *map_1..3, *mapmode1_end)")
    elif lbl.startswith("*rgd2_") or lbl in ("*map_1_2", "*map_2_2", "*map_3_2", "*map_4_2", "*mapmode2_end"):
        return ("Season 1", "s01_ch02", "第一季 第2章 (*rgd2_opning, *map_*_2, *mapmode2_end)")
    elif lbl in ("*map_1_3", "*map_2_3", "*map_3_3", "*map_4_3", "*mapmode3_end",
                  "*map_1_4", "*map_2_4", "*map_3_4", "*map_4_4", "*mapmode4_end",
                  "*rgd3_opning", "*map_1_5", "*map_2_5", "*map_3_5", "*map_4_5", "*mapmode5_end",
                  "*map_1_6", "*map_2_6", "*map_3_6", "*mapmode6_end",
                  "*map_1_7", "*map_2_7", "*map_3_7", "*mapmode7_end"):
        return ("Season 1", "s01_ch03", "第一季 第3章 (包含 *rgd3_opning 及地图模式 3~7)")
    elif lbl.startswith("*rgd4_") or lbl in ("*map_1_8", "*map_2_8", "*map_3_8", "*map_4_8", "*mapmode8_end",
                                              "*map_1_9", "*map_2_9", "*map_3_9",
                                              "*map_1_10", "*mapmode10_end",
                                              "*map_1_11", "*map_2_11", "*map_3_11", "*map_4_11", "*map_5_11", "*mapmode11_end"):
        return ("Season 1", "s01_ch04", "第一季 第4章 (*rgd4_opning 及地图模式 8~11)")
    elif lbl.startswith("*rgd5_") or lbl in ("*map_1_12", "*map_2_12", "*map_3_12", "*mapmode12_end",
                                              "*map_1_13", "*map_2_13", "*map_3_13", "*mapmode13_end",
                                              "*map_1_14", "*map_2_14", "*map_3_14", "*mapmode14_end"):
        return ("Season 1", "s01_ch05", "第一季 第5章 (*rgd5_opning 及地图模式 12~14)")
    elif lbl.startswith("*rgd6_"):
        return ("Season 1", "s01_ch06", "第一季 第6章 (*rgd6_opning)")
    elif lbl.startswith("*rgd7_") or lbl in ("*map_1_15", "*map_2_15", "*map_3_15",
                                              "*map_1_16", "*map_2_16", "*map_3_16", "*mapmode2_s2_end"):
        return ("Season 1", "s01_ch07", "第一季 第7章 (*rgd7_opning 及地图模式 15~16, *mapmode2_s2_end)")
    
    # Season 2
    elif lbl.startswith("*rgds2_1_") or lbl in ("*map_1_17", "*map_2_17", "*map_3_17", "*mapmode3_s2_end"):
        return ("Season 2", "s02_ch01", "第二季 第1章 (*rgds2_1_opning 及地图模式 17)")
    elif lbl.startswith("*rgds2_2_") or lbl in ("*map_1_18", "*map_2_18", "*map_3_18", "*mapmode4_s2_end"):
        return ("Season 2", "s02_ch02", "第二季 第2章 (*rgds2_2_opning 及地图模式 18)")
    elif lbl.startswith("*rgds2_3_"):
        return ("Season 2", "s02_ch03", "第二季 第3章 (*rgds2_3_opning)")
    elif lbl.startswith("*rgds2_4_"):
        return ("Season 2", "s02_ch04", "第二季 第4章 (*rgds2_4_opning)")
    elif lbl.startswith("*rgds2_5_"):
        return ("Season 2", "s02_ch05", "第二季 第5章 (*rgds2_5_opning)")
    elif lbl.startswith("*rgds2_6_"):
        return ("Season 2", "s02_ch06", "第二季 第6章 (*rgds2_6_opning)")
    elif lbl.startswith("*rgds2_7_"):
        return ("Season 2", "s02_ch07", "第二季 第7章 (*rgds2_7_opning)")
    
    # Season 3
    elif lbl.startswith("*rgds3_1_"):
        return ("Season 3", "s03_ch01", "第三季 第1章 (*rgds3_1_opning)")
    elif lbl.startswith("*rgds3_2_"):
        return ("Season 3", "s03_ch02", "第三季 第2章 (*rgds3_2_opning, *rgds3_2_1_opning)")
    elif lbl.startswith("*rgds3_3_"):
        return ("Season 3", "s03_ch03", "第三季 第3章 (*rgds3_3_opning)")
    elif lbl.startswith("*rgds3_4_") or lbl in ("*map_1_19", "*map_2_19", "*map_3_19", "*map_4_19", "*mapmode19_end"):
        return ("Season 3", "s03_ch04", "第三季 第4章 (*rgds3_4_*, 地图模式 19)")
    elif lbl.startswith("*rgds3_5_"):
        return ("Season 3", "s03_ch05", "第三季 第5章 (*rgds3_5_opning)")
    
    # Season 4
    elif lbl.startswith("*rgds4_1_"):
        return ("Season 4 (Last Season)", "s04_ch01", "第四季 第1章 (*rgds4_1_opning, *rgds4_1_2_opning)")
    elif lbl.startswith("*rgds4_2_"):
        return ("Season 4 (Last Season)", "s04_ch02", "第四季 第2章 (*rgds4_2_opning)")
    elif lbl.startswith("*rgds4_3_"):
        return ("Season 4 (Last Season)", "s04_ch03", "第四季 第3章 (*rgds4_3_opning)")
    elif lbl.startswith("*rgds4_4_") or lbl in ("*map_1_20", "*map_2_20", "*map_3_20", "*map_4_20", "*map_5_20", "*mapmode20_end"):
        return ("Season 4 (Last Season)", "s04_ch04", "第四季 第4章 (*rgds4_4_opning, 地图模式 20)")
    elif lbl.startswith("*rgds4_5_"):
        return ("Season 4 (Last Season)", "s04_ch05", "第四季 第5章 (*rgds4_5_opning)")
    
    return ("Other / Common", "other_" + lbl.replace("*", ""), f"未分类场景 ({lbl})")

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    ref_map = {}
    if REF_PATH.exists():
        with open(REF_PATH, "r", encoding="utf-8") as f:
            for line in f:
                item = json.loads(line)
                ref_map[item["id"]] = item
                
    rows = conn.execute("SELECT id, line_no, script_label, speaker_code, category, confidence, original_ja, original_sha256, status FROM segments ORDER BY line_no").fetchall()
    
    # Check delivered files
    delivered_ids = {}
    for p in DELIVERY_DIR.rglob("*.jsonl"):
        if p.name == "coverage_manifest.jsonl":
            continue
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    delivered_ids[data["id"]] = (p.relative_to(DELIVERY_DIR).as_posix(), data)
                except Exception:
                    pass
                    
    print(f"Total delivered ids found across jsonl: {len(delivered_ids)}")
    
    chapter_stats = collections.defaultdict(lambda: {
        "season": "",
        "chapter_code": "",
        "chapter_title": "",
        "total": 0,
        "dialogue": 0,
        "narration": 0,
        "other": 0,
        "baseline_candidate": 0,
        "baseline_unmatched": 0,
        "delivered": 0,
        "pending": 0,
        "excluded": 0,
        "labels": set(),
        "line_min": 999999,
        "line_max": 0
    })
    
    manifest_records = []
    
    for r in rows:
        seg_id = r["id"]
        line_no = r["line_no"]
        lbl = r["script_label"]
        cat = r["category"]
        conf = r["confidence"]
        status = r["status"]
        
        season, chap_code, chap_title = get_season_and_chapter(lbl, line_no)
        stats = chapter_stats[chap_code]
        stats["season"] = season
        stats["chapter_code"] = chap_code
        stats["chapter_title"] = chap_title
        stats["total"] += 1
        stats["labels"].add(str(lbl))
        if line_no < stats["line_min"]:
            stats["line_min"] = line_no
        if line_no > stats["line_max"]:
            stats["line_max"] = line_no
            
        if cat == "dialogue":
            stats["dialogue"] += 1
        elif cat == "narration":
            stats["narration"] += 1
        else:
            stats["other"] += 1
            
        is_candidate = (seg_id in ref_map and ref_map[seg_id]["classification"] == "candidate")
        if is_candidate:
            stats["baseline_candidate"] += 1
        else:
            stats["baseline_unmatched"] += 1
            
        is_delivered = seg_id in delivered_ids
        is_excluded = (lbl is None or cat in ("needs_command_review", "script_literal_candidate", "possible_script"))
        
        if is_excluded:
            stats["excluded"] += 1
            m_status = "excluded"
        elif is_delivered:
            stats["delivered"] += 1
            m_status = "delivered"
        else:
            stats["pending"] += 1
            m_status = "pending"
            
        delivery_file = delivered_ids[seg_id][0] if is_delivered else None
        
        manifest_records.append({
            "id": seg_id,
            "line_no": line_no,
            "season": season,
            "chapter_code": chap_code,
            "script_label": str(lbl),
            "category": cat,
            "status": m_status,
            "has_1_5_candidate": is_candidate,
            "candidate_text_zh": ref_map[seg_id].get("candidate_text_zh") if is_candidate else None,
            "delivery_file": delivery_file
        })

    # Write coverage_manifest.jsonl
    manifest_jsonl_path = DELIVERY_DIR / "coverage_manifest.jsonl"
    with open(manifest_jsonl_path, "w", encoding="utf-8") as f:
        for rec in manifest_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            
    print(f"Wrote {len(manifest_records)} records to {manifest_jsonl_path}")
    
    # Write coverage_manifest.md
    manifest_md_path = DELIVERY_DIR / "coverage_manifest.md"
    with open(manifest_md_path, "w", encoding="utf-8") as f:
        f.write("# 《ROSE GUNS DAYS》四季全篇汉化覆盖清单\n\n")
        f.write(f"- **总计提取脚本切片**：{len(rows)} 条\n")
        f.write(f"- **当前已交付定稿切片**：{len(delivered_ids)} 条\n")
        f.write("- **交付目录**：`translation_delivery/`\n")
        f.write("- **交付格式**：UTF-8 JSONL，字段包含 `id`、`source_sha256`、`translation_zh`、`review_notes`\n\n")
        f.write("---\n\n")
        
        # Group chapters by season
        by_season = collections.defaultdict(list)
        for chap_code, stats in sorted(chapter_stats.items(), key=lambda x: x[1]["line_min"]):
            by_season[stats["season"]].append(stats)
            
        for season_name, chaps in by_season.items():
            total_season = sum(c["total"] for c in chaps)
            delivered_season = sum(c["delivered"] for c in chaps)
            candidate_season = sum(c["baseline_candidate"] for c in chaps)
            excluded_season = sum(c["excluded"] for c in chaps)
            pending_season = sum(c["pending"] for c in chaps)
            
            f.write(f"## {season_name}\n\n")
            f.write(f"本季切片总量：**{total_season}** 条 | 1.5旧译对照：**{candidate_season}** 条 | 已交付：**{delivered_season}** 条 | 待处理：**{pending_season}** 条 | 排除项：**{excluded_season}** 条\n\n")
            f.write("| 章节代码 | 章节说明 | 对应行号范围 | 总条数 | 对白 | 旁白 | 其他 | 1.5可用候选 | 已交付 | 待处理 | 状态 |\n")
            f.write("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n")
            for c in chaps:
                status_badge = "已完结" if (c["delivered"] > 0 and c["pending"] == 0) else ("进行中" if c["delivered"] > 0 else "待处理")
                if c["excluded"] == c["total"]:
                    status_badge = "程序排除"
                f.write(f"| `{c['chapter_code']}` | {c['chapter_title']} | L{c['line_min']:06d} ~ L{c['line_max']:06d} | {c['total']} | {c['dialogue']} | {c['narration']} | {c['other']} | {c['baseline_candidate']} | {c['delivered']} | {c['pending']} | **{status_badge}** |\n")
            f.write("\n")
            
    print(f"Wrote summary markdown to {manifest_md_path}")

if __name__ == "__main__":
    main()
