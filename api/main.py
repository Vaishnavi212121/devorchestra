from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os, sys, json
from datetime import datetime
from dotenv import load_dotenv
from typing import Optional
import logging

# Setup paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(CURRENT_DIR)
sys.path.insert(0, ROOT_DIR)

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Imports
from agents.orchestrator import OrchestratorAgent
from database import get_db_manager
from core.redis_manager import get_redis_bus

# Initialize
app = FastAPI(title="DevOrchestra v2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = OrchestratorAgent()
db = get_db_manager()
redis_bus = get_redis_bus()

class UserStoryRequest(BaseModel):
    user_story: str
    project_name: str = "demo"

# --- DASHBOARD HTML ---
@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    with open(os.path.join(os.path.dirname(__file__), 'index.html'), 'r') as f:
        return f.read()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("🔌 WebSocket connected")
    
    try:
        while True:
            data = await websocket.receive_json()
            user_story = data.get("user_story") or data.get("message", "")
            
            if not user_story:
                await websocket.send_json({"type": "error", "message": "No user story provided"})
                continue
            
            logger.info(f"📝 Received: {user_story[:50]}...")
            
            # Set websocket for orchestrator
            orchestrator.set_websocket(websocket)
            
            # Initial progress
            await websocket.send_json({
                "type": "progress",
                "progress": 5,
                "message": "🚀 Starting orchestration...",
                "agent": "orchestrator"
            })
            
            try:
                # RUN ORCHESTRATOR
                result = await orchestrator.execute_task({
                    "user_story": user_story
                })
                
                logger.info(f"✅ Orchestration complete in {result.get('execution_time_seconds', 0):.1f}s")
                
            except Exception as e:
                logger.error(f"❌ Orchestration error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
    
    except WebSocketDisconnect:
        logger.info("🔌 WebSocket disconnected")

@app.get("/agents/status")
async def get_status():
    """Get all agent statuses"""
    metrics_data = orchestrator.get_all_metrics()
    metrics_data["system"] = {
        "timestamp": datetime.now().isoformat(),
        "redis_connected": redis_bus.health_check() if redis_bus else False
    }
    return metrics_data

@app.get("/metrics/performance")
async def get_performance_metrics():
    """Get performance metrics from database"""
    try:
        cursor = db.conn.execute("""
            SELECT 
                COUNT(*) as total_tasks,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
                AVG(CASE WHEN status = 'completed' THEN 
                    (julianday('now') - julianday(timestamp)) * 86400 
                END) as avg_time_seconds
            FROM tasks
            WHERE timestamp > datetime('now', '-7 days')
        """)
        row = cursor.fetchone()
        
        if row:
            total, successful, avg_time = row
            success_rate = (successful / total * 100) if total > 0 else 0
            speedup = (4 * 3600 / avg_time) if avg_time and avg_time > 0 else 0
            
            return {
                "total_tasks_7d": total or 0,
                "success_rate": f"{success_rate:.1f}%",
                "avg_execution_time": f"{avg_time:.1f}s" if avg_time else "N/A",
                "estimated_speedup": f"{speedup:.1f}x" if speedup > 0 else "N/A"
            }
    except Exception as e:
        logger.error(f"Metrics error: {e}")
    
    return {
        "total_tasks_7d": 0,
        "success_rate": "0%",
        "avg_execution_time": "N/A",
        "estimated_speedup": "N/A"
    }

@app.get("/task/latest")
async def get_latest_task():
    """Get most recent task with proper code extraction"""
    try:
        cursor = db.conn.execute(
            "SELECT id, status, result, timestamp FROM tasks ORDER BY timestamp DESC LIMIT 1"
        )
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="No tasks found")
        
        task_id, status, result_json, timestamp = row
        
        # Default empty results
        results = {
            "frontend": "// No frontend code generated yet",
            "backend": "# No backend code generated yet",
            "database": "-- No database schema generated yet"
        }
        
        if result_json:
            try:
                parsed = json.loads(result_json)
                gen_code = parsed.get("generated_code", {})
                
                # ✅ FIXED: Proper extraction logic
                if "frontend" in gen_code:
                    frontend_data = gen_code["frontend"]
                    if isinstance(frontend_data, dict):
                        result_obj = frontend_data.get("result", {})
                        code = result_obj.get("component_code", "")
                        if code:
                            results["frontend"] = code
                
                if "backend" in gen_code:
                    backend_data = gen_code["backend"]
                    if isinstance(backend_data, dict):
                        result_obj = backend_data.get("result", {})
                        code = result_obj.get("api_code", "")
                        if code:
                            results["backend"] = code
                
                if "database" in gen_code:
                    database_data = gen_code["database"]
                    if isinstance(database_data, dict):
                        result_obj = database_data.get("result", {})
                        code = result_obj.get("schema_sql", "")
                        if code:
                            results["database"] = code
                
                logger.info(f"✅ Extracted code lengths: F={len(results['frontend'])}, B={len(results['backend'])}, D={len(results['database'])}")
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON parse error: {e}")
                results["frontend"] = f"// Error parsing results: {e}"
        
        return {
            "id": task_id,
            "status": status,
            "timestamp": timestamp,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching latest task: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "redis": redis_bus.health_check() if redis_bus else False,
        "database": "connected" if db.conn else "disconnected",
        "model": "gemini-2.0-flash-exp",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting DevOrchestra v2.0")
    logger.info("📊 Dashboard: http://localhost:8000")
    logger.info("📡 WebSocket: ws://localhost:8000/ws")
    logger.info("🤖 Model: gemini-2.0-flash-exp")
    PORT = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=PORT)