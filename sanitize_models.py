import os
import re

def sanitize_files():
    # This regex finds any GenerativeModel call and forces it to 1.5-flash
    # It catches: 'gemini-2.0-flash', 'gemini-pro', 'models/gemini-pro', etc.
    pattern = r"genai\.GenerativeModel\(['\"][\w\-\/]+['\"]\)"
    replacement = "genai.GenerativeModel('gemini-pro')"
    
    count = 0
    print("🧹 Sanitizing model names in all files...")

    for root, dirs, files in os.walk("."):
        if "venv" in root or "__pycache__" in root:
            continue
            
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    
                    # Force replace any model definition
                    new_content = re.sub(pattern, replacement, content)
                    
                    # Specific fix for the "exp" suffix bug if it exists elsewhere
                    new_content = new_content.replace("gemini-pro", "gemini-pro")
                    
                    if new_content != content:
                        print(f"✅ Fixed {file}")
                        with open(path, "w", encoding="utf-8") as f:
                            f.write(new_content)
                        count += 1
                except Exception as e:
                    print(f"⚠️ Could not process {path}: {e}")

    print(f"🎉 Done! Sanitized {count} files.")

if __name__ == "__main__":
    sanitize_files()
    