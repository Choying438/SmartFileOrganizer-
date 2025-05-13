import os
import hashlib
import shutil
import json

WATCHED_FOLDER = "/sdcard/"
HASH_DB_FILE = "file_hashes.json"
UNDO_LOG_FILE = "undo_log.json"
SKIP_DIRS = ["Android", "obb", "Android/data", ".thumbnails", ".cache", "DCIM/.thumbnails"]

# Organized by categories
FILE_CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".webp", ".raw", ".arw", ".cr2"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".xlsx", ".csv", ".xml"],
    "Videos": [".mp4", ".avi", ".mov", ".mkv", ".flv"],
    "Music": [".mp3", ".wav", ".ogg", ".flac"],
    "Archives": [".zip", ".rar", ".7z", ".tar"],
    "APKs": [".apk"],
    "Executables": [".exe", ".msi"],
    "Others": []  # For any other types
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

def delete_unwanted_thumbnails(folder):
    deleted = []
    for root, _, files in os.walk(folder):
        if should_skip(root):
            continue
        for file in files:
            if file.lower().endswith(".jpg") and file[:-4].isdigit():
                try:
                    os.remove(os.path.join(root, file))
                    deleted.append(os.path.join(root, file))
                    print(f"Deleted unwanted thumbnail: {file}")
                except Exception as e:
                    print(f"Failed to delete {file}: {e}")
    return deleted

def show_category_menu():
    print("\n=== Select File Types to Organize ===")
    for i, (category, extensions) in enumerate(FILE_CATEGORIES.items(), 1):
        print(f"{i}. {category} ({', '.join(extensions)})")
    print(f"{len(FILE_CATEGORIES)+1}. All File Types")
    print(f"{len(FILE_CATEGORIES)+2}. Back to Main Menu")
    
    choices = input("Enter your choices (comma separated): ").strip().split(',')
    selected_categories = []
    
    for choice in choices:
        try:
            choice_num = int(choice.strip())
            if 1 <= choice_num <= len(FILE_CATEGORIES):
                selected_categories.append(list(FILE_CATEGORIES.keys())[choice_num-1])
            elif choice_num == len(FILE_CATEGORIES)+1:  # All files
                return list(FILE_CATEGORIES.keys())
            elif choice_num == len(FILE_CATEGORIES)+2:  # Back
                return None
        except ValueError:
            pass
    
    return selected_categories if selected_categories else None

def organize_files(folder, categories):
    move_log = []
    extension_map = {}
    
    # Build extension map for selected categories
    for category in categories:
        for ext in FILE_CATEGORIES[category]:
            extension_map[ext] = category
    
    for root, _, files in os.walk(folder):
        if should_skip(root):
            continue
        for file in files:
            full_path = os.path.join(root, file)
            ext = os.path.splitext(file)[1].lower()
            category = extension_map.get(ext, None)
            
            if category:
                target_dir = os.path.join(WATCHED_FOLDER, category)
                os.makedirs(target_dir, exist_ok=True)
                dest_path = os.path.join(target_dir, file)
                try:
                    shutil.move(full_path, dest_path)
                    move_log.append({"from": full_path, "to": dest_path})
                    print(f"Moved: {file} to {category}")
                except Exception as e:
                    print(f"Error moving {file}: {e}")
    
    if move_log:
        with open(UNDO_LOG_FILE, "w") as f:
            json.dump(move_log, f, indent=4)

def undo_organization():
    if not os.path.exists(UNDO_LOG_FILE):
        print("Nothing to undo.")
        return

    with open(UNDO_LOG_FILE, "r") as f:
        move_log = json.load(f)

    for move in reversed(move_log):
        try:
            os.makedirs(os.path.dirname(move["from"]), exist_ok=True)
            shutil.move(move["to"], move["from"])
            print(f"Restored: {os.path.basename(move['to'])}")
        except Exception as e:
            print(f"Failed to restore {move['to']}: {e}")

    os.remove(UNDO_LOG_FILE)
    print("Undo complete.")

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

def main_menu():
    while True:
        print("\n=== File Organizer Pro by Choying ===")
        print("1. Organize Files (Choose Types)")
        print("2. Clean Junk Files")
        print("3. Undo Last Organize")
        print("4. Check File Integrity")
        print("5. Exit")

        choice = input("Choose an option (1-5): ").strip()
        
        if choice == "1":
            selected_categories = show_category_menu()
            if selected_categories:
                print(f"\nOrganizing: {', '.join(selected_categories)}")
                organize_files(WATCHED_FOLDER, selected_categories)
                check_integrity(WATCHED_FOLDER)
        
        elif choice == "2":
            print("\nCleaning junk files...")
            delete_unwanted_thumbnails(WATCHED_FOLDER)
        
        elif choice == "3":
            print("\nUndoing last organization...")
            undo_organization()
        
        elif choice == "4":
            print("\nChecking file integrity...")
            check_integrity(WATCHED_FOLDER)
        
        elif choice == "5":
            print("\nGoodbye!")
            exit()
        
        else:
            print("\nInvalid option. Please try again.")

if __name__ == "__main__":
    main_menu()
