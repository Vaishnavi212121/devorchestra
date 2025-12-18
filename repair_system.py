import os

# The ONLY model we know works for you
TARGET_MODEL = "gemini-pro"

# Models to find and destroy
BAD_MODELS = [
    "gemini-pro", 
    "gemini-flash-latest", 
    "gemini-pro",
    "gemini-pro"
]

AGENTS_DIR = "agents"

print(f"🚀 Starting Repair: Enforcing {TARGET_MODEL} across all agents...")

count = 0
for root, dirs, files in os.walk(AGENTS_DIR):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r") as f:
                content = f.read()
            
            new_content = content
            changed = False
            
            for bad in BAD_MODELS:
                if bad in new_content:
                    new_content = new_content.replace(bad, TARGET_MODEL)
                    changed = True
            
            if changed:
                with open(path, "w") as f:
                    f.write(new_content)
                print(f"✅ FIXED: {file}")
                count += 1

print(f"\n🎉 Repair Complete! Updated {count} files.")
