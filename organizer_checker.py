#!/data/data/com.termux/files/usr/bin/env python3
import os
import shutil
import json
from pathlib import Path
from datetime import datetime

# === Configuration ===
HOME_DIR = "/storage/emulated/0"
LOG_PATH = os.path.join(Path.home(), ".file_organizer_restore_log.json")
SKIP_DIRS = ["Android", ".thumbnails", "WhatsApp", "DCIM/.thumbnails", "Android/data", "Android/obb"]
EXT_CATS = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".arw", ".cr2"],
    "Videos": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv"],
    "Documents": [".pdf", ".docx", ".doc", ".xlsx", ".xls", ".pptx", ".txt", ".rtf"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Audio": [".mp3", ".wav", ".ogg", ".m4a"],
    "Executables": [".exe", ".apk", ".deb"]
}

# === ANSI Color Helper ===
def color(text, r, g, b):
    return f"\033[38;2;{r};{g};{b}m{text}\033[0m"

# === Banner ===
def display_title():
    border = "="*50
    print(color(border, 96, 200, 255))
    print(color(f"{'Smart File Organizer Pro':^50}", 255, 220, 100))
    print(color("-"*50, 200, 100, 255))
    print(color(f"{'By Choying':^50}", 100, 255, 150))
    print(color(f"{'Enhanced Preview v2.0':^50}", 200, 255, 200))
    print(color(border, 96, 200, 255))

# === Scan and Prepare Moves ===
def scan_files():
    moves = []
    for root, dirs, files in os.walk(HOME_DIR):
        if any(skip in root for skip in SKIP_DIRS): continue
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            for cat, exts in EXT_CATS.items():
                if ext in exts:
                    src = os.path.join(root, f)
                    year = datetime.fromtimestamp(os.path.getmtime(src)).strftime("%Y")
                    dst = os.path.join(HOME_DIR, f"{year}-{cat}", f)
                    moves.append((src, dst))
                    break
    return moves

# === Enhanced Preview File Counts ===
def preview_summary(moves):
    counts = {}
    size_stats = {}
    date_stats = {"oldest": datetime.now(), "newest": datetime.fromtimestamp(0)}
    extensions = {}
    
    for src, dst in moves:
        # Get file category from destination path
        cat = dst.split("-",1)[1].split(os.sep)[0]
        ext = os.path.splitext(src)[1].lower()
        
        # Count files per category
        counts[cat] = counts.get(cat, 0) + 1
        
        # Track extensions
        extensions[ext] = extensions.get(ext, 0) + 1
        
        # Calculate size statistics
        try:
            file_size = os.path.getsize(src) / (1024*1024)  # Size in MB
            if cat not in size_stats:
                size_stats[cat] = {"total": 0, "largest": 0, "count": 0}
            size_stats[cat]["total"] += file_size
            size_stats[cat]["count"] += 1
            if file_size > size_stats[cat]["largest"]:
                size_stats[cat]["largest"] = file_size
        except:
            pass
        
        # Get file modification time
        try:
            mod_time = datetime.fromtimestamp(os.path.getmtime(src))
            if mod_time < date_stats["oldest"]:
                date_stats["oldest"] = mod_time
            if mod_time > date_stats["newest"]:
                date_stats["newest"] = mod_time
        except:
            pass
    
    # Print colorful summary
    print(color("\n📊 [Enhanced File Statistics Preview]\n", 180, 255, 180))
    
    # 1. Category Breakdown
    print(color("📂 Category Breakdown:", 255, 220, 100))
    max_count = max(counts.values()) if counts else 1
    for cat, cnt in sorted(counts.items()):
        bar = "█" * int(30 * cnt / max_count)
        print(color(f"  {cat:<12} {cnt:>4} files ", 200, 200, 255) + 
              color(f"{bar}", 100, 255, 150))
    
    # 2. Size Information
    print(color("\n💾 Size Statistics:", 255, 220, 100))
    for cat, stats in size_stats.items():
        avg = stats["total"] / stats["count"] if stats["count"] > 0 else 0
        print(color(f"  {cat:<12} ", 200, 200, 255) +
              color(f"Total: {stats['total']:.1f}MB ", 100, 255, 200) +
              color(f"Avg: {avg:.1f}MB ", 200, 255, 100) +
              color(f"Largest: {stats['largest']:.1f}MB", 255, 150, 100))
    
    # 3. Date Range
    print(color("\n📅 Date Range:", 255, 220, 100))
    print(color(f"  Oldest file:  {date_stats['oldest'].strftime('%Y-%m-%d')}", 200, 200, 255))
    print(color(f"  Newest file:  {date_stats['newest'].strftime('%Y-%m-%d')}", 200, 200, 255))
    print(color(f"  Time span:    {(date_stats['newest'] - date_stats['oldest']).days} days", 200, 200, 255))
    
    # 4. Extension Distribution
    print(color("\n🔤 Extension Distribution:", 255, 220, 100))
    top_ext = sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:5]
    for ext, cnt in top_ext:
        print(color(f"  {ext:<8} {cnt:>4} files", 200, 255, 200))
    
    # 5. Total Summary
    total_files = sum(counts.values())
    total_size = sum(stats["total"] for stats in size_stats.values())
    print(color("\n🔢 Totals:", 255, 220, 100))
    print(color(f"  {total_files} files", 255, 200, 100))
    print(color(f"  {total_size:.1f}MB", 255, 200, 100))
    print()

# === Preview Move List ===
def preview_moves(moves):
    print(color("[Preview - Files to be moved]\n", 255, 200, 100))
    for i, (src, dst) in enumerate(moves[:15], 1):  # Show first 15 files
        print(color(f"{i}. {os.path.basename(src):<30}", 200, 255, 200) + 
              color(f"from: {os.path.dirname(src)}", 150, 200, 255))
        print(color(f"   → {dst}", 100, 255, 100))
    if len(moves) > 15:
        print(color(f"\n... and {len(moves)-15} more files", 200, 200, 200))
    print()

# === Execute Moves & Log ===
def execute_moves(moves):
    log = {}
    moved_count = 0
    total_size = 0
    
    for src, dst in moves:
        try:
            file_size = os.path.getsize(src) / (1024*1024)  # MB
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(src, dst)
            log[dst] = src
            moved_count += 1
            total_size += file_size
        except Exception as e:
            print(color(f"Error moving {src}: {str(e)}", 255, 100, 100))
    
    with open(LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)
    
    print(color(f"\n✅ Successfully moved {moved_count}/{len(moves)} files ({total_size:.1f}MB)", 100, 255, 100))
    print(color(f"Log saved to: {LOG_PATH}", 200, 200, 255))

# === Undo Last Move ===
def undo_moves():
    if not os.path.exists(LOG_PATH):
        print(color("No log found to undo!", 255, 100, 100))
        return
    
    with open(LOG_PATH) as f:
        log = json.load(f)
    
    restored_count = 0
    for dst, src in log.items():
        if os.path.exists(dst):
            os.makedirs(os.path.dirname(src), exist_ok=True)
            try:
                shutil.move(dst, src)
                restored_count += 1
            except Exception as e:
                print(color(f"Error restoring {dst}: {str(e)}", 255, 100, 100))
    
    os.remove(LOG_PATH)
    print(color(f"\n↩️ Restored {restored_count}/{len(log)} files", 100, 255, 100))

# === Show Restore Log ===
def show_log():
    if not os.path.exists(LOG_PATH):
        print(color("No restore log available.", 255, 100, 100))
        return
    
    with open(LOG_PATH) as f:
        log = json.load(f)
    
    print(color("\n📋 [Restore Log Summary]\n", 255, 255, 180))
    
    # Count files by category in the log
    log_counts = {}
    for dst in log.keys():
        cat = dst.split("-",1)[1].split(os.sep)[0]
        log_counts[cat] = log_counts.get(cat, 0) + 1
    
    # Print summary
    for cat, count in log_counts.items():
        print(color(f"  {cat:<12} {count:>4} files", 200, 255, 200))
    
    # Show sample entries
    print(color("\nLast 5 operations:", 255, 220, 100))
    for dst, src in list(log.items())[-5:]:
        print(color(f"  {os.path.basename(src)}", 200, 255, 200) + 
              color(" from ", 200, 200, 200) +
              color(f"{os.path.dirname(src)}", 150, 200, 255))
    print()

# === Main Menu ===
def main():
    display_title()
    moves = scan_files()
    
    while True:
        print(color("\nSelect an option:", 255, 200, 100))
        print(color("[1] Preview & Move Files", 200, 255, 100))
        print(color("[2] Undo Last Move", 255, 150, 100))
        print(color("[3] Cancel", 255, 100, 100))
        print(color("[4] Show Restore Log", 100, 255, 255))
        print(color("[6] Detailed File Preview", 200, 255, 200))
        print(color("[7] Category Statistics", 255, 255, 180))
        print(color("[8] Quick Summary", 180, 255, 180))
        print(color("[9] Full Analysis Report", 100, 200, 255))
        print(color("[0] Exit\n", 255, 100, 100))

        choice = input(color("Enter choice: ", 255, 255, 255)).strip()
        
        if choice == "1":
            preview_summary(moves)
            preview_moves(moves)
            if input(color("Proceed with moving? (y/n): ", 255, 255, 0)).lower() == 'y':
                execute_moves(moves)
        elif choice == "2":
            undo_moves()
        elif choice == "3":
            print(color("\nOperation canceled.", 255, 100, 100))
            break
        elif choice == "4":
            show_log()
        elif choice == "6":
            preview_moves(moves)
        elif choice == "7":
            preview_summary(moves)
        elif choice == "8":
            total_files = len(moves)
            total_size = sum(os.path.getsize(src) for src, _ in moves) / (1024*1024)
            print(color("\n📝 Quick Summary:", 180, 255, 180))
            print(color(f"  Files to organize: {total_files}", 200, 255, 200))
            print(color(f"  Estimated size: {total_size:.1f}MB", 200, 255, 200))
        elif choice == "9":
            preview_summary(moves)
            preview_moves(moves)
        elif choice == "0":
            print(color("\nExiting Smart File Organizer Pro. Goodbye!", 100, 255, 100))
            break
        else:
            print(color("\nInvalid option. Please try again.", 255, 100, 100))

if __name__ == "__main__":
    main()
