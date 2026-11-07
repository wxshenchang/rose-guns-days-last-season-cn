# 《ROSE GUNS DAYS》（玫瑰与枪之日）四季完整汉化补丁

[![Release](https://img.shields.io/github/v/release/wxshenchang/rose-guns-days-last-season-cn?color=brightgreen&label=Release)](https://github.com/wxshenchang/rose-guns-days-last-season-cn/releases)
[![Language](https://img.shields.io/badge/Language-Simplified%20Chinese-blue)](https://github.com/wxshenchang/rose-guns-days-last-season-cn)
[![Platform](https://img.shields.io/badge/Platform-Windows%20PC-orange)](https://github.com/wxshenchang/rose-guns-days-last-season-cn)

本项目为 07th Expansion（竜騎士07）作品 **《ROSE GUNS DAYS -Last Season-》（玫瑰与枪之日 最终季）** 的四季全量中文本地化与现代运行环境适配补丁。

涵盖第 1 季、第 2 季、第 3 季、第 4 季及 Extra 额外内容，共计 **39,490 句剧情对白与系统界面** 的全量精校与构建。

---

## 🌟 核心特性与优化

| 优化模块 | 说明 |
| :--- | :--- |
| **全四季完整剧情** | 完整覆盖 Season 1 ~ Season 4 及 Extra 支线剧情（39,490 句文本全量精校）。 |
| **汉化底本承袭与补完** | 前期剧情承袭自原 **RGD汉化组 1.5 汉化版** 奠定的译名体系与文风，全量校订瑕疵并补译后续全章节与支线。 |
| **原生新宋体高精渲染** | 彻底修复原版日文 Gothic 回退导致的粗细混排，以及微软黑体被引擎横向拉扁（140% 矮胖）的问题；采用 Windows 原生 **新宋体（`NSimSun`）**，1:1 方正挺拔，字迹锐利清晰。 |
| **四季排版边界清零** | 针对全量文本进行逐句边界扫描，彻底消除长句对白框底部溢出（`overflow_3lines: 0`），并修正多重引号开闭语法闭合。 |
| **全季解锁随选** | 默认提供正统剧情推进体验；附带 `extra` 解锁补丁，方便直接跳选四季任意章节。 |

---

## 📥 安装使用

1. 前往 [Releases](../../releases) 页面下载 `RoseGunsDays_Patch_v2.0.zip`。
2. 解压并将压缩包内的所有文件（`00.txt`、`envdata`、`extra` 文件夹等）复制并覆盖到《ROSE GUNS DAYS -Last Season-》游戏根目录下。
3. 运行游戏即可开始游玩。

> **提示（快捷全季解锁）**：游戏默认按通关顺序解锁各季。如需直接体验全四季内容，将 `extra` 文件夹内的 `00_all_seasons_unlocked.txt` 复制到游戏根目录并重命名为 `00.txt` 覆盖即可。

---

## 🎮 常用快捷键

- **鼠标左键 / Enter / 空格**：推进对白、确认选项
- **鼠标滚轮向上 / PageUp**：呼出已读文本回顾（Backlog）
- **Ctrl**：高速快进已读剧情
- **鼠标右键 / Esc**：呼出系统存档 / 读档 / 设置菜单
- **F 键**：切换窗口化 / 全屏显示

---

## ❓ 常见问题 (FAQ)

**Q: 进游戏后字体显示不是宋体，或者字体异常？**  
A: 请在游戏顶部菜单栏选择 **「字体」-> 勾选「默认」** 即可恢复最佳新宋体渲染。

**Q: 是否需要额外安装字体文件？**  
A: 不需要。新宋体为 Windows 系统原生自带字体，开箱即用。

---

## 📜 汉化来源、致谢与版权声明

### 1. 汉化文本出处与沿革
- **前期译文出处与风格承袭**：
  - 本项目前期章节剧情及界面译文，底本来源于原 **「RGD汉化组」** 制作发布的 **《ROSE GUNS DAYS》中文版 Ver1.5**。
  - 本项目完全继承并沿用了原 1.5 汉化版所确立的核心角色译名（雷欧、罗斯、林原树理、珍妮夫人等）、势力组织术语与战后黑帮叙事风格基调。
  - 在此向当年为本作中文本地化做出开拓性贡献的原 **RGD汉化组** 全体成员致以崇高的敬意与由衷的谢意！
- **全季精校补完与现代适配**：
  - **纠错与润色**：在原 1.5 译本基础上，系统性校订了旧译中遗留的少量错漏、人名异写、断行溢出及语法控制符问题；
  - **全量补译**：补译了原 1.5 尚未涵盖的后续全四季主线与 Extra 支线（累计补完 2.7 万余句，实现全篇 39,490 句 100% 完整汉化）；
  - **底层渲染修复**：攻克了 NScripter 引擎在现代 Windows 环境下的 GDI 字体拉伸与日文字库缺字问题，适配原生新宋体 1:1 清晰呈现。

### 2. 原作版权
- 本作原作剧本、角色、音乐与美术素材版权均归属于 **07th Expansion** 与 **竜騎士07** 老师。

### 3. 免责声明与分发规范
- 本汉化补丁及相关项目文件仅供视觉小说爱好者与 07th Expansion 玩家交流学习使用。
- 严禁将本汉化补丁或整合版本用于任何形式的商业营利行为（包括但不限于付费下载、刻盘倒卖、直播打赏绑定等）。
- 欢迎各位玩家通过官方渠道支持并购买正版游戏。
