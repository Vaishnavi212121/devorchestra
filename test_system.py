"""
Automated Test Runner for DevOrchestra
Tests all components with sample user stories
"""
import asyncio
import sys
import os

# 👇 FORCE SET THE API KEY HERE
os.environ["GOOGLE_API_KEY"] = "AIzaSyDPRACWaV3QRqD7T0l--l0FoqBc-u32GWU"

sys.path.insert(0, os.path.abspath('.'))

from agents.orchestrator import OrchestratorAgent
from core.redis_manager import get_redis_bus
from database import get_db_manager
import json
from datetime import datetime

# Sample User Stories for Testing
TEST_STORIES = [
    {
        "id": "test_1",
        "name": "Simple Login Page",
        "story": """As a user, I want a login page with email and password fields, 
        so that I can securely access my account. The page should validate email format 
        and show error messages for invalid inputs."""
    },
    {
        "id": "test_2",
        "name": "User Dashboard",
        "story": """As a logged-in user, I want to see a dashboard displaying my profile 
        information, recent activities, and quick action buttons, so that I can quickly 
        access important features."""
    },
    {
        "id": "test_3",
        "name": "Todo List Manager",
        "story": """As a user, I want to create, edit, and delete todo items with due dates, 
        so that I can manage my tasks effectively. The system should store todos in a database 
        and allow filtering by status."""
    }
]

class SystemTester:
    def __init__(self):
        self.orchestrator = OrchestratorAgent()
        self.redis = get_redis_bus()
        self.db = get_db_manager()
        self.results = []
    
    async def test_redis_connection(self):
        """Test 1: Redis Connection"""
        print("\n" + "="*60)
        print("TEST 1: Redis Connection")
        print("="*60)
        
        is_healthy = self.redis.health_check()
        
        if is_healthy:
            print("✅ Redis is connected and healthy")
            
            # Test pub/sub
            test_messages = []
            def callback(msg):
                test_messages.append(msg)
            
            # Run in background to prevent freezing
            asyncio.create_task(self.redis.subscribe("test:channel", callback))
            await asyncio.sleep(0.5)
            
            # Now publish
            await self.redis.publish_task_status("test_task", "test_agent", "testing", {"test": True})
            await asyncio.sleep(1)
            
            if test_messages:
                print("✅ Pub/Sub is working")
            else:
                print("⚠️  Pub/Sub may have issues (check Redis listener thread)")
        else:
            print("❌ Redis connection failed - running in mock mode")
            print("   Run: redis-server")
        
        return is_healthy
    
    async def test_database_connection(self):
        """Test 2: Database Connection"""
        print("\n" + "="*60)
        print("TEST 2: Database Connection")
        print("="*60)
        
        try:
            cursor = self.db.conn.execute("SELECT COUNT(*) FROM tasks")
            count = cursor.fetchone()[0]
            print(f"✅ Database connected - {count} tasks in history")
            return True
        except Exception as e:
            print(f"❌ Database error: {e}")
            return False
    
    async def test_agents_initialization(self):
        """Test 3: All Agents Initialization"""
        print("\n" + "="*60)
        print("TEST 3: Agent Initialization")
        print("="*60)
        
        agents = [
            "orchestrator", "frontend_agent", "backend_agent", "database_agent",
            "testing_agent", "ado_parser", "legacy_agent", "prompt_refiner", "integration_agent"
        ]
        
        all_ok = True
        for agent_name in agents:
            if hasattr(self.orchestrator, agent_name):
                print(f"✅ {agent_name} initialized")
            elif agent_name == "orchestrator":
                print(f"✅ {agent_name} initialized")
            else:
                print(f"❌ {agent_name} not found")
                all_ok = False
        
        return all_ok
    
    async def test_code_generation(self, test_case):
        """Test 4: Full Code Generation Pipeline"""
        print("\n" + "="*60)
        print(f"TEST 4: Code Generation - {test_case['name']}")
        print("="*60)
        print(f"User Story: {test_case['story'][:100]}...")
        
        start_time = datetime.now()
        
        try:
            # FORCE RE-INIT Orchestrator model just in case
            if not self.orchestrator.model:
                 print("⚠️ Orchestrator model was None, attempting re-init...")
                 import google.generativeai as genai
                 genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
                 self.orchestrator.model = genai.GenerativeModel('gemini-pro')

            result = await self.orchestrator.execute_task({
                "user_story": test_case['story']
            })
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Validate result structure
            checks = {
                "Has task_id": "task_id" in result,
                "Has requirements": "requirements" in result or ("generated_code" in result),
                "Has generated_code": "generated_code" in result,
                "Has frontend code": self._check_code(result, "frontend", "component_code"),
                "Has backend code": self._check_code(result, "backend", "api_code"),
                "Has database schema": self._check_code(result, "database", "schema_sql"),
                "Status is completed": result.get("status") == "completed"
            }
            
            passed = sum(checks.values())
            total = len(checks)
            
            print(f"\n📊 Validation Results: {passed}/{total} passed")
            for check, status in checks.items():
                icon = "✅" if status else "❌"
                print(f"  {icon} {check}")
            
            print(f"\n⏱️  Execution Time: {execution_time:.2f} seconds")
            
            # Store result
            self.results.append({
                "test_id": test_case['id'],
                "test_name": test_case['name'],
                "execution_time": execution_time,
                "passed_checks": passed,
                "total_checks": total
            })
            
            return passed == total
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _check_code(self, result, agent_type, code_key):
        """Helper to check if code was generated"""
        try:
            code = result.get("generated_code", {}).get(agent_type, {}).get("result", {}).get(code_key, "")
            return len(str(code)) > 20
        except:
            return False
    
    async def test_parallel_execution(self):
        """Test 5: Parallel Execution Speed"""
        print("\n" + "="*60)
        print("TEST 5: Parallel Execution Performance")
        print("="*60)
        
        story = "Create a simple contact form"
        print("Testing parallel agent execution...")
        start = datetime.now()
        
        await self.orchestrator.execute_task({"user_story": story})
        
        parallel_time = (datetime.now() - start).total_seconds()
        print(f"✅ Parallel execution completed in {parallel_time:.2f}s")

    def generate_report(self):
        print("\n" + "="*60)
        print("FINAL TEST REPORT")
        print("="*60)
        for r in self.results:
            status = "✅ PASS" if r['passed_checks'] == r['total_checks'] else "❌ FAIL"
            print(f"\n  {status} {r['test_name']}")
            print(f"    - Execution: {r['execution_time']:.2f}s")
            print(f"    - Checks: {r['passed_checks']}/{r['total_checks']}")

async def main():
    print("="*60)
    print("DevOrchestra System Test Suite")
    print("Testing all components and generating metrics")
    print("="*60)
    
    tester = SystemTester()
    await tester.test_redis_connection()
    await tester.test_database_connection()
    await tester.test_agents_initialization()
    
    print("\n" + "="*60)
    print("Starting Code Generation Tests")
    print("="*60)
    
    for i, test_case in enumerate(TEST_STORIES, 1):
        print(f"\n[Test {i}/{len(TEST_STORIES)}]")
        await tester.test_code_generation(test_case)
        if i < len(TEST_STORIES):
            print("\nWaiting 3 seconds...")
            await asyncio.sleep(3)
    
    await tester.test_parallel_execution()
    tester.generate_report()
    print("\n" + "="*60)
    print("All tests completed!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())