"""
BASE AGENT WITH RATE LIMITING & RETRY LOGIC
Handles API quota limits gracefully
"""
from abc import ABC, abstractmethod
from typing import Dict, Any
import asyncio
import json
import os
import re
import time

# Safe Import
try:
    import google.generativeai as genai
    HAS_GOOGLE_LIB = True
except ImportError:
    genai = None
    HAS_GOOGLE_LIB = False

class BaseAgent(ABC):
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.current_status = "idle"
        self.model = None
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 4.0  # 4 seconds between requests (15 RPM = ~4s)
        
        # Demo mode fallback
        self.demo_mode = os.getenv("DEMO_MODE", "false").lower() == "true"

        import os
        MY_KEY = os.getenv("GEMINI_API_KEY", "") 

        if MY_KEY and "PASTE" not in MY_KEY:
            clean_key = MY_KEY.strip().replace('\n', '').replace('\r', '')
            if HAS_GOOGLE_LIB:
                try:
                    genai.configure(api_key=clean_key)
                    self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
                    print(f"✅ {agent_id}: AI Connected & Ready.")
                except Exception as e:
                    print(f"❌ {agent_id}: AI Init Failed: {e}")

    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]: pass

    def get_metrics(self) -> Dict[str, Any]:
        return {"id": self.agent_id, "status": self.current_status}

    async def _publish_status(self, task_id, agent_id, status, data=None): pass

    async def _rate_limit(self):
        """Enforce minimum time between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            wait_time = self.min_request_interval - time_since_last
            print(f"⏱️  {self.agent_id}: Rate limiting, waiting {wait_time:.1f}s")
            await asyncio.sleep(wait_time)

    def _extract_retry_delay(self, error_msg: str) -> float:
        """Extract retry delay from error message"""
        match = re.search(r'retry in ([\d.]+)s', error_msg)
        if match:
            return float(match.group(1))
        return 30.0  # Default 30 seconds

    async def generate_response(self, prompt: str) -> str:
        """Generate with rate limiting and retry logic"""
        self.current_status = "processing"
        
        if not self.model:
            return self._error_response("API Key Missing or Invalid")

        # Apply rate limiting BEFORE making request
        await self._rate_limit()

        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Build system instruction based on agent type
                if "frontend" in self.agent_id:
                    system_instruction = f"""
You are an expert React developer. 
{prompt}

Return ONLY a single valid React Functional Component.
- Use Tailwind CSS for styling
- Use 'lucide-react' for icons
- DO NOT use markdown backticks
- Must be 'export default function App()'
"""
                elif "backend" in self.agent_id:
                    system_instruction = f"""
You are an expert FastAPI developer.
{prompt}

Return valid Python FastAPI code with proper endpoints.
DO NOT use markdown backticks.
"""
                elif "database" in self.agent_id:
                    system_instruction = f"""
You are a database architect.
{prompt}

Return valid PostgreSQL CREATE TABLE statements.
DO NOT use markdown backticks.
"""
                elif "ado_parser" in self.agent_id or "parser" in self.agent_id:
                    system_instruction = f"""
{prompt}

Return ONLY valid JSON. No markdown, no explanations.
"""
                else:
                    system_instruction = prompt
                
                # Call AI
                response = await self.model.generate_content_async(system_instruction)
                raw_text = response.text
                
                # Success! Update last request time
                self.last_request_time = time.time()
                
                # Clean output
                clean_code = raw_text.replace("```javascript", "").replace("```jsx", "") \
                                      .replace("```python", "").replace("```sql", "") \
                                      .replace("```json", "").replace("```", "").strip()
                
                self.current_status = "idle"
                
                # Package response
                if "frontend" in self.agent_id:
                    response_obj = {
                        "component_code": clean_code,
                        "dependencies": ["react", "lucide-react", "tailwindcss"]
                    }
                    return f"```json\n{json.dumps(response_obj)}\n```"
                    
                elif "backend" in self.agent_id:
                    response_obj = {
                        "api_code": clean_code,
                        "endpoints": self._extract_endpoints(clean_code)
                    }
                    return f"```json\n{json.dumps(response_obj)}\n```"
                    
                elif "database" in self.agent_id:
                    response_obj = {
                        "schema_sql": clean_code,
                        "tables": self._extract_table_names(clean_code)
                    }
                    return f"```json\n{json.dumps(response_obj)}\n```"
                    
                else:
                    return clean_code

            except Exception as e:
                error_msg = str(e)
                
                # Check if it's a rate limit error
                if "429" in error_msg or "quota" in error_msg.lower() or "rate" in error_msg.lower():
                    wait_time = self._extract_retry_delay(error_msg)
                    
                    if attempt < max_retries - 1:
                        print(f"⏳ {self.agent_id}: Rate limit hit (attempt {attempt+1}/{max_retries}). Waiting {wait_time:.0f}s...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        print(f"❌ {self.agent_id}: Max retries reached. Quota exhausted.")
                        # Fallback to demo mode
                        if self.demo_mode or True:  # Always fallback for now
                            print(f"🎭 {self.agent_id}: Using demo fallback")
                            return self._get_demo_response(prompt)
                        else:
                            return self._error_response(f"API quota exceeded. Please try again in {wait_time:.0f}s or upgrade your plan.")
                else:
                    print(f"❌ {self.agent_id}: Generation error: {error_msg}")
                    return self._error_response(f"Generation failed: {error_msg}")

        # Should never reach here, but just in case
        return self._error_response("Max retries exceeded")

    def _get_demo_response(self, prompt: str) -> str:
        """Fallback demo responses when quota is exceeded"""
        if "frontend" in self.agent_id:
            demo_code = """import React, { useState } from 'react';
import { Sparkles, Info } from 'lucide-react';

export default function App() {
    const [count, setCount] = useState(0);
    
    return (
        <div className='min-h-screen bg-gradient-to-br from-purple-900 via-slate-900 to-blue-900 text-white p-8'>
            <div className='max-w-4xl mx-auto'>
                <div className='bg-yellow-500/10 border border-yellow-500 rounded-xl p-4 mb-6 flex items-start gap-3'>
                    <Info className='text-yellow-400 flex-shrink-0' size={24} />
                    <div className='text-sm'>
                        <p className='font-bold text-yellow-400 mb-1'>Demo Mode Active</p>
                        <p className='text-yellow-200'>API quota reached. This is a fallback demo component. Upgrade your API plan for full functionality.</p>
                    </div>
                </div>
                
                <div className='bg-white/5 backdrop-blur rounded-xl p-8 border border-white/10'>
                    <div className='flex items-center gap-3 mb-6'>
                        <Sparkles className='text-purple-400' size={32} />
                        <h1 className='text-3xl font-bold'>Demo Component</h1>
                    </div>
                    
                    <p className='text-slate-300 mb-6'>
                        This is a placeholder component. In production, this would be your custom React app.
                    </p>
                    
                    <div className='bg-purple-500/20 rounded-lg p-6 border border-purple-500/30'>
                        <p className='text-sm text-purple-300 mb-2'>Interactive Demo:</p>
                        <button 
                            onClick={() => setCount(count + 1)}
                            className='bg-purple-600 hover:bg-purple-700 px-6 py-2 rounded-lg font-semibold transition-colors'
                        >
                            Clicked {count} times
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}"""
            return f"```json\n{json.dumps({'component_code': demo_code, 'dependencies': ['react', 'lucide-react']})}\n```"
        
        elif "backend" in self.agent_id:
            demo_code = """from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Demo API - Quota Fallback")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class Item(BaseModel):
    name: str
    description: str = None

@app.get("/")
async def root():
    return {
        "message": "Demo API - API quota reached",
        "status": "fallback_mode",
        "note": "Upgrade your Gemini API plan for custom endpoints"
    }

@app.get("/items")
async def get_items():
    return {"items": [{"id": 1, "name": "Demo Item"}]}

@app.post("/items")
async def create_item(item: Item):
    return {"message": "Created", "item": item}"""
            return f"```json\n{json.dumps({'api_code': demo_code, 'endpoints': ['GET /', 'GET /items', 'POST /items']})}\n```"
        
        elif "database" in self.agent_id:
            demo_sql = """-- Demo Database Schema (Fallback Mode)
-- API quota reached. Upgrade for custom schemas.

CREATE TABLE IF NOT EXISTS demo_items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_demo_items_name ON demo_items(name);

-- This is a placeholder schema
-- Real implementation would match your specific requirements"""
            return f"```json\n{json.dumps({'schema_sql': demo_sql, 'tables': ['demo_items']})}\n```"
        
        else:
            return json.dumps({"message": "Demo fallback response", "status": "quota_exceeded"})

    def _extract_endpoints(self, code: str) -> list:
        """Extract API endpoints from FastAPI code"""
        endpoints = []
        patterns = [
            r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']',
            r'@router\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']'
        ]
        for pattern in patterns:
            matches = re.findall(pattern, code)
            for method, path in matches:
                endpoints.append(f"{method.upper()} {path}")
        return endpoints if endpoints else ["GET /", "POST /data"]

    def _extract_table_names(self, sql: str) -> list:
        """Extract table names from SQL"""
        pattern = r'CREATE TABLE (?:IF NOT EXISTS )?([a-zA-Z_][a-zA-Z0-9_]*)'
        tables = re.findall(pattern, sql, re.IGNORECASE)
        return tables if tables else ["main_table"]

    def _error_response(self, msg):
        """Graceful error UI"""
        if "frontend" in self.agent_id:
            err_code = f"""import React from 'react';
import {{ AlertCircle }} from 'lucide-react';

export default function ErrorComponent() {{
    return (
        <div className='min-h-screen bg-slate-900 flex items-center justify-center p-4'>
            <div className='max-w-md w-full bg-red-900/20 border border-red-500 rounded-xl p-6'>
                <div className='flex items-center gap-3 mb-4'>
                    <AlertCircle className='text-red-500' size={{32}} />
                    <h2 className='text-xl font-bold text-red-400'>System Error</h2>
                </div>
                <p className='text-red-300'>{msg}</p>
                <div className='mt-4 text-xs text-red-400'>
                    <p>Try:</p>
                    <ul className='list-disc ml-4 mt-2 space-y-1'>
                        <li>Wait a few minutes and retry</li>
                        <li>Upgrade your API plan</li>
                        <li>Enable demo mode</li>
                    </ul>
                </div>
            </div>
        </div>
    );
}}"""
            return f"```json\n{json.dumps({'component_code': err_code, 'dependencies': ['react', 'lucide-react']})}\n```"
        else:
            return f"```json\n{json.dumps({'error': msg, 'code': f'# Error: {msg}'})}\n```"