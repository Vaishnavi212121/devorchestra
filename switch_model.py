import os

# This model is often more stable for free tier
TARGET_MODEL = "gemini-flash-latest"

FILES = [
    "agents/base_agent.py",
    "agents/backend_agent.py", 
    "agents/frontend_agent.py",
    "agents/database_agent.py",
    "agents/orchestrator.py"
]

print(f"🔄 Switching all agents to {TARGET_MODEL}...")

for file_path in FILES:
    if os.path.exists(file_path):
        with open(file_path, "r") as f:
            content = f.read()

        # Replace old models
        new_content = content.replace("gemini-pro", TARGET_MODEL)
        new_content = new_content.replace("gemini-pro", TARGET_MODEL)

        with open(file_path, "w") as f:
            f.write(new_content)
        print(f"✅ Updated {file_path}")

print("🎉 Switch complete! Try running api/main.py now.")
