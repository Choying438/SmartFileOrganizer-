import os
import hashlib
import shutil
import json

WATCHED_FOLDER = "/sdcard/"  # Change if needed
HASH_DB_FILE = "file_hashes.json"
SKIP_DIRS = ["Android", "obb", "Android/data"]

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
    for skip in SKIP_DIRS:
        if skip.lower() in path.lower():
            return True
    return False

def organize_files(folder):
    for root, _, files in os.walk(folder):
        if should_skip(root):
            continue
        for file in files:
            full_path = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower()
            category = EXTENSION_MAP.get(ext, None)
            if category:
                target_dir = os.path.join(WATCHED_FOLDER, category)
                os.makedirs(target_dir, exist_ok=True)
                try:
                    shutil.move(full_path, os.path.join(target_dir, file))
                    print(f"Moved: {file} to {category}")
                except Exception as e:
                    print(f"Error moving {file}: {e}")

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

    if os.path.exists(HASH_DB_FILE):
        with open(HASH_DB_FILE, "r") as f:
            saved_hashes = json.load(f)
    else:
        saved_hashes = {}

    print("\n--- Integrity Report ---")
    for path, old_hash in saved_hashes.items():
        if path not in current_hashes:
            print(f"Deleted: {path}")
        elif current_hashes[path] != old_hash:
            print(f"Modified: {path}")

    for path in current_hashes:
        if path not in saved_hashes:
            print(f"New File: {path}")

    with open(HASH_DB_FILE, "w") as f:
        json.dump(current_hashes, f, indent=4)
    print("--- End of Report ---\n")

# Run the process
print("Organizing files...")
organize_files(WATCHED_FOLDER)

print("Checking file integrity...")
check_integrity(WATCHED_FOLDER)
