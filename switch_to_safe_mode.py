import os

def fix_files():
    # We are switching FROM the broken model TO the safe model
    BROKEN_MODEL = "gemini-pro"
    SAFE_MODEL = "gemini-pro"
    
    print(f"🔧 Switching all agents from '{BROKEN_MODEL}' to '{SAFE_MODEL}'...")
    count = 0
    
    for root, dirs, files in os.walk("."):
        if "venv" in root or "__pycache__" in root:
            continue
            
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    if BROKEN_MODEL in content:
                        new_content = content.replace(BROKEN_MODEL, SAFE_MODEL)
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        print(f"✅ Fixed: {file}")
                        count += 1
                except Exception as e:
                    print(f"⚠️ Could not read {path}")

    print(f"🎉 Done! Updated {count} files to Safe Mode.")

if __name__ == "__main__":
    fix_files()