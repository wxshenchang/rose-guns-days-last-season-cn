"""Package both Overlay Patch (Package A) and Standalone Game (Package B)."""

import os, sys, shutil, hashlib, zipfile
from pathlib import Path

ROOT = Path("D:/ai/rose_localization_workspace")
CANDIDATE = ROOT / "builds" / "final_review_candidate"
UNLOCKED = ROOT / "builds" / "final_review_unlocked"
DIST = ROOT / "dist"

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

README_PATCH = """========================================================================
《ROSE GUNS DAYS》（玫瑰与枪之日）四季完整汉化补丁 v2.0
========================================================================

【补丁说明】
本补丁为《ROSE GUNS DAYS -Last Season-》四季全主线与支线汉化最终修正版。
涵盖第 1 季、第 2 季、第 3 季、第 4 季及 Extra 额外内容（共计 39,490 句文本）。

【汉化出处与版权致谢】
1. 前期文本出处：本项目前期章节剧情及界面译文，底本来源于原「RGD汉化组」制作发布的《ROSE GUNS DAYS》中文版 Ver1.5。本项目承袭其确立的核心角色译名（雷欧、罗斯、林原树理、珍妮夫人等）与叙事风格。在此向原 RGD汉化组 的开拓性奉献致以崇高敬意！
2. 全季精校与补完：在 1.5 基础上修正错漏，全量补译后续全主线与支线（补译校订 2.7 万余句），并完成现代系统原生新宋体渲染与排版溢出精修。
3. 原作版权：07th Expansion / 竜騎士07。
4. 本补丁仅供视觉小说爱好者交流学习，请支持正版作品。严禁商用。

【安装方法】
1. 确保您已安装《ROSE GUNS DAYS -Last Season-》游戏本体。
2. 将本压缩包内所有文件（00.txt、envdata、extra 文件夹等）解压并复制到游戏安装根目录中。
3. 当系统提示是否覆盖同名文件时，选择「替换目标中的文件」。
4. 双击运行 RoseGunsDays_CN.exe 即可开始游玩。

【快捷全季解锁（可选）】
游戏默认为正统剧情模式（从第一季逐步通关解锁后续各季）。
如需作为审核人员或想直接游玩任意章节：
可将 extra 文件夹内的 00_all_seasons_unlocked.txt 重命名为 00.txt 并覆盖游戏根目录即可。

【常见问题】
Q1: 游戏内字体显示不正确？
A1: 请进入游戏顶部菜单栏 ->「字体」-> 勾选「默认」即可恢复最佳新宋体效果。
Q2: 提示缺字或乱码？
A2: 请确认系统为简体中文编码（GBK），并确保通过 RoseGunsDays_CN.exe 启动。
========================================================================
"""

README_STANDALONE = """========================================================================
《ROSE GUNS DAYS》（玫瑰与枪之日）四季完整中文版 v2.0 绿色解压即玩版
========================================================================

【作品与版本信息】
- 原作版权：07th Expansion / 竜騎士07
- 版本说明：四季全主线与支线完整收录版（含 Last Season 最终季）
- 汉化出处：
  * 前期剧情底本来源于原「RGD汉化组」制作发布的《ROSE GUNS DAYS》中文版 Ver1.5，承袭其经典译名体系与叙事基调。谨向原汉化组全体成员致谢！
  * 本项目在 1.5 基础上全量校订瑕疵，完整补译后续全四季主线与 Extra 支线（累计 39,490 句全量汉化），并完成现代系统底层字体与排版优化。

【运行说明】
1. 本版本为免安装绿色版，解压至任意全英文或无特殊符号路径即可。
2. 双击根目录下的 RoseGunsDays_CN.exe 即可开始游玩。
3. 退出游戏可按 Alt+F4 或右键系统菜单退出。

【操作按键】
- 鼠标左键 / Enter / Space：推进对白、确认选项
- 鼠标滚轮向上 / PageUp：回顾已读文本（Backlog）
- 鼠标滚轮向下 / PageDown：推进文本
- Ctrl：快速快进已读剧情
- 鼠标右键 / Esc：呼出系统存档/读档/设置菜单
- F：切换全屏 / 窗口化

【关于全季解锁】
- 默认设定为正常剧情流程推进模式（从第一季剧情开始体验）。
- 若您是审核人员或希望直接选关体验特定章节，请进入 extra 目录，将 00_all_seasons_unlocked.txt 复制到游戏根目录并重命名为 00.txt 覆盖即可。

【技术与排版优化】
- 引擎字体：优化绑定为经典正方「新宋体 (NSimSun)」，高清晰度渲染且无横向拉扁变形。
- 全量排版：四季全部 39,490 句对白已完成全量边界扫描与排版精修，杜绝对话框底部溢出。

【免责声明】
本整合版仅供视觉小说爱好者交流学习使用，严禁商用。请支持并购买正版游戏。
========================================================================
"""

def make_patch_bundle():
    print("\n=== Building Package A: Overlay Patch Bundle ===")
    patch_dir = DIST / "RoseGunsDays_Patch_v2.0"
    if patch_dir.exists():
        shutil.rmtree(patch_dir)
    patch_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. Copy core files
    shutil.copyfile(CANDIDATE / "00.txt", patch_dir / "00.txt")
    shutil.copyfile(CANDIDATE / "envdata", patch_dir / "envdata")
    
    # 2. Add extra unlocked script
    extra_dir = patch_dir / "extra"
    extra_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(UNLOCKED / "00.txt", extra_dir / "00_all_seasons_unlocked.txt")
    
    # 3. Add README
    (patch_dir / "README_补丁使用说明.txt").write_text(README_PATCH, encoding="gbk")
    
    # 4. Generate SHA256SUMS
    lines = []
    for p in sorted(patch_dir.rglob("*")):
        if p.is_file():
            rel = p.relative_to(patch_dir)
            lines.append(f"{sha256_file(p)}  {rel}")
    (patch_dir / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    
    # 5. Pack zip
    zip_path = DIST / "RoseGunsDays_Patch_v2.0.zip"
    if zip_path.exists():
        zip_path.unlink()
    print(f"Creating zip: {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in patch_dir.rglob("*"):
            if p.is_file():
                arcname = p.relative_to(DIST)
                zf.write(p, arcname)
    print(f"Done Package A: {zip_path} ({zip_path.stat().st_size / (1024*1024):.2f} MB)")

def make_standalone_bundle():
    print("\n=== Building Package B: Standalone Release Bundle ===")
    standalone_dir = DIST / "RoseGunsDays_CN_v2.0_Standalone"
    if standalone_dir.exists():
        shutil.rmtree(standalone_dir)
    standalone_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy from candidate, skipping backups and reports
    skip_files = {"00.txt.bak", "envdata.bak", "build_report.json"}
    for item in CANDIDATE.iterdir():
        if item.name in skip_files:
            continue
        dest = standalone_dir / item.name
        if item.is_dir():
            print(f"Copying directory: {item.name}...")
            shutil.copytree(item, dest)
        else:
            print(f"Copying file: {item.name} ({item.stat().st_size / (1024*1024):.2f} MB)...")
            shutil.copyfile(item, dest)
            
    # Add extra unlocked script
    extra_dir = standalone_dir / "extra"
    extra_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(UNLOCKED / "00.txt", extra_dir / "00_all_seasons_unlocked.txt")
    
    # Add README
    (standalone_dir / "README_游戏运行说明.txt").write_text(README_STANDALONE, encoding="gbk")
    
    # Generate SHA256SUMS for root files
    print("Generating SHA256SUMS...")
    lines = []
    for p in sorted(standalone_dir.iterdir()):
        if p.is_file() and p.name != "SHA256SUMS.txt":
            lines.append(f"{sha256_file(p)}  {p.name}")
    (standalone_dir / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    
    # Pack zip with ZIP64
    zip_path = DIST / "RoseGunsDays_CN_v2.0_Standalone.zip"
    if zip_path.exists():
        zip_path.unlink()
    print(f"Creating standalone archive: {zip_path.name} (this will take ~1-2 minutes for 1.8GB)...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_STORED, allowZip64=True) as zf:
        for root, dirs, files in os.walk(standalone_dir):
            for file in files:
                full_p = Path(root) / file
                arcname = full_p.relative_to(DIST)
                zf.write(full_p, arcname)
    print(f"Done Package B: {zip_path} ({zip_path.stat().st_size / (1024*1024):.2f} MB)")

if __name__ == "__main__":
    DIST.mkdir(exist_ok=True)
    make_patch_bundle()
    make_standalone_bundle()
    print("\nAll packaging finished successfully!")
