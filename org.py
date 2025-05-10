import os
import hashlib
import shutil
import json
import time
from datetime import datetime

WATCHED_FOLDER = "/sdcard/"
HASH_DB_FILE = "file_hashes.json"
UNDO_LOG_FILE = "undo_log.json"
SKIP_DIRS = ["Android", "obb", "Android/data", "WhatsApp/Media/.Statuses", ".thumbnails"]
JUNK_EXTENSIONS = [".nomedia", ".tmp", ".log", ".bak"]

EXTENSION_MAP = {
    ".jpg": "Images", ".jpeg": "Images", ".png": "Images", ".gif": "Images", ".webp": "Images",
    ".mp4": "Videos", ".avi": "Videos", ".mov": "Videos",
    ".pdf": "Docs", ".docx": "Docs", ".txt": "Docs", ".xlsx": "Excel_Files",
    ".mp3": "Music", ".wav": "Music",
    ".zip": "ZIP_Files", ".rar": "RAR_Files",
    ".apk": "APK_Files", ".exe": "EXE_Files",
    ".arw": "ARW_Files", ".cr2": "CR2_Files"
}

def get_file_hash(file_path):
    hash_func = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except Exception:
        return None

def should_skip(path):
    return any(skip.lower() in path.lower() for skip in SKIP_DIRS)

def is_screenshot(file):
    return "screenshot" in file.lower()

def load_json(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return {}

def save_json(data, file):
    with open(file, "w") as f:
        json.dump(data, f, indent=4)

def organize_files(folder):
    undo_log = {}
    for root, _, files in os.walk(folder):
        if should_skip(root):
            continue
        for file in files:
            full_path = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower()
            if is_screenshot(file):
                continue
            if ext in JUNK_EXTENSIONS or should_skip(full_path):
                try:
                    os.remove(full_path)
                    undo_log[full_path] = {"action": "delete"}
                    print(f"Deleted junk: {full_path}")
                except Exception as e:
                    print(f"Failed to delete {file}: {e}")
                continue
            category = EXTENSION_MAP.get(ext)
            if category:
                target_dir = os.path.join(WATCHED_FOLDER, category)
                os.makedirs(target_dir, exist_ok=True)
                target_path = os.path.join(target_dir, file)
                try:
                    shutil.move(full_path, target_path)
                    undo_log[target_path] = {"action": "move", "from": full_path}
                    print(f"Moved: {file} to {category}")
                except Exception as e:
                    print(f"Error moving {file}: {e}")
    save_json(undo_log, UNDO_LOG_FILE)

def check_integrity(folder):
    current_hashes = {}
    for root, _, files in os.walk(folder):
        if should_skip(root):
            continue
        for file in files:
            full_path = os.path.join(root, file)
            file_hash = get_file_hash(full_path)
            if file_hash:
                current_hashes[full_path] = file_hash

    saved_hashes = load_json(HASH_DB_FILE)

    print("\n--- Integrity Report ---")
    for path, old_hash in saved_hashes.items():
        if path not in current_hashes:
            print(f"Deleted: {path}")
        elif current_hashes[path] != old_hash:
            print(f"Modified: {path}")

    for path in current_hashes:
        if path not in saved_hashes:
            print(f"New File: {path}")

    save_json(current_hashes, HASH_DB_FILE)
    print("--- End of Report ---\n")

def undo_last_action():
    undo_log = load_json(UNDO_LOG_FILE)
    if not undo_log:
        print("Nothing to undo.")
        return

    for path, info in undo_log.items():
        if info["action"] == "move" and os.path.exists(path):
            try:
                shutil.move(path, info["from"])
                print(f"Moved back: {path} -> {info['from']}")
            except Exception as e:
                print(f"Failed to undo move: {e}")
        elif info["action"] == "delete":
            print(f"Cannot restore deleted file: {path}")
    os.remove(UNDO_LOG_FILE)

def show_menu():
    while True:
        print("\n--- File Organizer Pro by Choying ---")
        print("1. Organize & Clean")
        print("2. Check Integrity")
        print("3. Undo Last Actions")
        print("4. Exit")
        choice = input("Enter choice: ")

        if choice == "1":
            organize_files(WATCHED_FOLDER)
        elif choice == "2":
            check_integrity(WATCHED_FOLDER)
        elif choice == "3":
            undo_last_action()
        elif choice == "4":
            print("Exiting...")
            break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    show_menu()
