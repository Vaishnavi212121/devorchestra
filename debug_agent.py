import asyncio
import os
import sys

# Ensure we can find the agents folder
sys.path.insert(0, os.path.abspath('.'))

from agents.backend_agent import BackendAgent

# 1. Force Set the API Key
os.environ["GOOGLE_API_KEY"] = "AIzaSyDPRACWaV3QRqD7T0l--l0FoqBc-u32GWU"

async def debug_run():
    print("🤖 Initializing Backend Agent...")
    try:
        agent = BackendAgent()
        
        if not agent.model:
            print("❌ Error: Agent model is None. API Key might be invalid.")
            return

        print(f"✅ Agent initialized with model: {agent.model._model_name}")
        
        print("\n🚀 Sending test prompt to Google Gemini...")
        result = await agent.execute_task({
            "task_id": "debug-test",
            "requirements": "Create a simple Python Hello World API using FastAPI"
        })
        
        print("\n🔍 RAW AGENT RESULT:")
        print(result)
        
        if result.get("status") == "failed":
            print(f"\n❌ FAILURE CAUSE: {result.get('error')}")
        else:
            print("\n✅ SUCCESS! The agent is working.")
            
    except Exception as e:
        print(f"\n❌ CRITICAL CRASH: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_run())
