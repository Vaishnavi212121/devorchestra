import os

# The model we WANT
NEW_MODEL = "gemini-pro"

# The models we want to REMOVE
BAD_MODELS = [
    "gemini-pro",
    "gemini-pro",
    "gemini-pro",
    "gemini-pro"  # Optional: standardizing everything to flash
]

def fix_files():
    print("🔍 Scanning for bad model names...")
    count = 0
    
    # Walk through all files in the current directory
    for root, dirs, files in os.walk("."):
        # Skip hidden folders and environments
        if "venv" in root or "__pycache__" in root or ".git" in root:
            continue
            
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    new_content = content
                    for bad in BAD_MODELS:
                        if bad in new_content:
                            print(f"🛠️ Fixing {bad} in {path}")
                            new_content = new_content.replace(bad, NEW_MODEL)
                    
                    if new_content != content:
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        count += 1
                except Exception as e:
                    print(f"⚠️ Could not read {path}: {e}")

    print(f"✅ Finished! Fixed {count} files.")

if __name__ == "__main__":
    fix_files()