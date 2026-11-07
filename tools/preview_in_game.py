"""Preview any text ID in Rose Guns Days engine, capture screenshots, or make save slot 1."""

import os, sys, subprocess, time, ctypes, argparse, json
from ctypes import wintypes
from pathlib import Path
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path("D:/ai/rose_localization_workspace")
sys.path.append(str(ROOT / "tools"))

from build_final_overlay import SUPPLEMENT_TARGETS, read_jsonl

unlocked_dir = ROOT / "builds" / "final_review_unlocked"
cand_dir = ROOT / "builds" / "final_review_candidate"
txt_path = unlocked_dir / "00.txt"
bak_path = unlocked_dir / "00.txt.bak"

# 1. Map ID to baseline line
def get_id_line_map():
    final_dir = ROOT / "translation_final"
    align_file = ROOT / "scratch" / "integration_alignment.tsv"
    mapped = {}
    for filename in ('integration_comment_anchors.jsonl', 'integration_reconciled.jsonl'):
        for row in read_jsonl(final_dir / filename):
            mapped[row['id']] = row['baseline_line']
    for row in read_jsonl(final_dir / 'integration_spans.jsonl'):
        targets = row['baseline_lines']
        for ident in row['ids']:
            mapped[ident] = targets[0]
    for line in align_file.read_text(encoding='utf-8').splitlines():
        number, target, state = line.split('\t')
        ident = f'L{int(number):06}'
        if ident not in mapped:
            mapped[ident] = int(target)
    for row in read_jsonl(final_dir / 'supplemental.jsonl'):
        ident = row['id']
        mapped[ident] = SUPPLEMENT_TARGETS[ident]
    return mapped

def preview(target_id, keep_open=False):
    target_id = target_id.upper()
    if not target_id.startswith("L"):
        target_id = f"L{int(target_id):06}"
    
    id_map = get_id_line_map()
    base_line = id_map.get(target_id)
    if not base_line:
        print(f"Error: Could not find mapping for ID {target_id}")
        return
    
    print(f"Target ID: {target_id} -> Baseline Line: {base_line}")
    
    # Read candidate 00.txt to get the exact rendered lines and context
    with open(cand_dir / "00.txt", "rb") as f:
        cand_lines = f.readlines()
    
    # Look back for background and window commands
    idx = base_line - 1
    # Find preceding bg or window if needed
    win_cmd = b"window 2\r\n"
    bg_cmd = b"bg public_113,0\r\n"
    for j in range(max(0, idx - 15), idx):
        if cand_lines[j].strip().startswith(b"window "):
            win_cmd = cand_lines[j]
        elif cand_lines[j].strip().startswith(b"bg ") and not cand_lines[j].strip().startswith(b"bg black"):
            parts = cand_lines[j].strip().split()[1].split(b",")
            bg_cmd = b"bg " + parts[0] + b",0\r\n"
    
    # Extract 1 preceding line for context if dialogue
    context_lines = []
    if idx > 0 and (b"\xa1\xb8" in cand_lines[idx-1] or b"window" not in cand_lines[idx-1]):
        context_lines.append(cand_lines[idx-1])
    context_lines.append(cand_lines[idx])
    
    # Target line + next line
    if idx + 1 < len(cand_lines):
        context_lines.append(cand_lines[idx+1])
    
    test_block = (
        b"mov %RGDEND,41 : goto *preview_target_scene\r\n"
        b"*preview_target_scene\r\n"
        + bg_cmd +
        b"print 1\r\n"
        + win_cmd +
        b"".join(context_lines)
        + b"\\\r\nend\r\n"
    )
    
    # Modify unlocked 00.txt
    with open(bak_path, "rb") as f_bak:
        script_lines = f_bak.readlines()
    
    script_lines[44] = b'defaultfont "NSimSun"\r\n'
    script_lines[7452] = test_block
    
    with open(txt_path, "wb") as f_out:
        f_out.writelines(script_lines)
    
    # Launch game
    p = subprocess.Popen([str(unlocked_dir / "RoseGunsDays_CN.exe")], cwd=str(unlocked_dir))
    time.sleep(5)
    
    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    
    hwnd = None
    def enum_cb(h, _):
        nonlocal hwnd
        buf = ctypes.create_unicode_buffer(100)
        user32.GetWindowTextW(h, buf, 100)
        if "rose" in buf.value.lower() or "guns" in buf.value.lower():
            hwnd = h
            return False
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    
    user32.SetForegroundWindow(hwnd)
    time.sleep(0.3)
    
    rect = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    w, h = rect.right - rect.left, rect.bottom - rect.top
    hwnd_dc = user32.GetDC(hwnd)
    mem_dc = gdi32.CreateCompatibleDC(hwnd_dc)
    bitmap = gdi32.CreateCompatibleBitmap(hwnd_dc, w, h)
    gdi32.SelectObject(mem_dc, bitmap)
    
    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ('biSize', wintypes.DWORD), ('biWidth', wintypes.LONG), ('biHeight', wintypes.LONG),
            ('biPlanes', wintypes.WORD), ('biBitCount', wintypes.WORD), ('biCompression', wintypes.DWORD),
            ('biSizeImage', wintypes.DWORD), ('biXPelsPerMeter', wintypes.LONG), ('biYPelsPerMeter', wintypes.LONG),
            ('biClrUsed', wintypes.DWORD), ('biClrImportant', wintypes.DWORD)
        ]
    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    buf = ctypes.create_string_buffer(w * h * 4)
    
    # Click once if there was context line before target
    if len(context_lines) > 1:
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        user32.SetCursorPos((rect.left + rect.right) // 2, (rect.top + rect.bottom) // 2)
        time.sleep(0.1)
        user32.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.08)
        user32.mouse_event(0x0004, 0, 0, 0, 0)
        time.sleep(2.5)
    
    user32.PrintWindow(hwnd, mem_dc, 2)
    gdi32.GetDIBits(mem_dc, bitmap, 0, h, buf, ctypes.byref(bmi), 0)
    im = Image.frombuffer('RGBA', (w, h), buf, 'raw', 'BGRA', 0, 1).convert('RGB')
    
    out_scene = ROOT / "scratch" / f"preview_{target_id}_scene.png"
    out_crop = ROOT / "scratch" / f"preview_{target_id}_crop_3x.png"
    
    im.save(str(out_scene))
    crop = im.crop((45, 340, 600, 475))
    crop_3x = crop.resize((crop.width * 3, crop.height * 3), Image.NEAREST)
    crop_3x.save(str(out_crop))
    
    gdi32.DeleteObject(bitmap)
    gdi32.DeleteDC(mem_dc)
    user32.ReleaseDC(hwnd, hwnd_dc)
    
    if not keep_open:
        p.terminate()
        p.wait()
        # Restore clean 00.txt
        with open(bak_path, "rb") as f_bak:
            clean_lines = f_bak.readlines()
        clean_lines[44] = b'defaultfont "NSimSun"\r\n'
        with open(txt_path, "wb") as f_out:
            f_out.writelines(clean_lines)
    else:
        print(f"Game kept open for inspection (HWND: {hwnd})!")
    
    print(f"\n[SUCCESS] Preview captured for {target_id}:")
    print(f"  Full Scene: {out_scene}")
    print(f"  3x TextBox: {out_crop}")
    return out_scene, out_crop

if __name__ == "__main__":
    if len(sys.argv) > 1:
        preview(sys.argv[1])
    else:
        print("Usage: python preview_in_game.py <TEXT_ID>")
