"""
Metrics Collector - Real-time performance tracking
Collects: Execution times, quality scores, speedup metrics, success rates
"""
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json
import statistics

class MetricsCollector:
    def __init__(self, db_path="metrics.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_tables()
    
    def _create_tables(self):
        """Create metrics tables."""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS execution_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                agent_name TEXT,
                execution_time REAL,
                success BOOLEAN,
                quality_score INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS quality_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                agent_type TEXT,
                language TEXT,
                quality_score INTEGER,
                passed_threshold BOOLEAN,
                linting_results TEXT,
                sonarqube_metrics TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS speedup_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT,
                total_execution_time REAL,
                manual_estimate_hours REAL,
                speedup_factor REAL,
                agents_used INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS agent_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT,
                avg_execution_time REAL,
                success_rate REAL,
                total_tasks INTEGER,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_task_timestamp ON execution_metrics(timestamp);
            CREATE INDEX IF NOT EXISTS idx_agent_name ON execution_metrics(agent_name);
        """)
        self.conn.commit()
    
    def log_execution(self, task_id: str, agent_name: str, execution_time: float, 
                     success: bool, quality_score: int = None):
        """Log agent execution metrics."""
        self.conn.execute("""
            INSERT INTO execution_metrics (task_id, agent_name, execution_time, success, quality_score)
            VALUES (?, ?, ?, ?, ?)
        """, (task_id, agent_name, execution_time, success, quality_score))
        self.conn.commit()
    
    def log_quality(self, task_id: str, agent_type: str, language: str, 
                   quality_score: int, passed_threshold: bool, 
                   linting_results: Dict, sonarqube_metrics: Dict):
        """Log code quality metrics."""
        self.conn.execute("""
            INSERT INTO quality_metrics 
            (task_id, agent_type, language, quality_score, passed_threshold, linting_results, sonarqube_metrics)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            task_id, agent_type, language, quality_score, passed_threshold,
            json.dumps(linting_results), json.dumps(sonarqube_metrics)
        ))
        self.conn.commit()
    
    def log_speedup(self, task_id: str, total_execution_time: float, 
                   manual_estimate_hours: float, agents_used: int):
        """Log speedup metrics."""
        speedup_factor = (manual_estimate_hours * 3600) / total_execution_time if total_execution_time > 0 else 0
        
        self.conn.execute("""
            INSERT INTO speedup_metrics 
            (task_id, total_execution_time, manual_estimate_hours, speedup_factor, agents_used)
            VALUES (?, ?, ?, ?, ?)
        """, (task_id, total_execution_time, manual_estimate_hours, speedup_factor, agents_used))
        self.conn.commit()
    
    def get_performance_summary(self, days: int = 7) -> Dict[str, Any]:
        """Get performance summary for the last N days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Overall metrics
        cursor = self.conn.execute("""
            SELECT 
                COUNT(*) as total_tasks,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_tasks,
                AVG(execution_time) as avg_execution_time,
                MIN(execution_time) as min_execution_time,
                MAX(execution_time) as max_execution_time
            FROM execution_metrics
            WHERE timestamp > ?
        """, (cutoff_date,))
        
        row = cursor.fetchone()
        total, successful, avg_time, min_time, max_time = row if row else (0, 0, 0, 0, 0)
        
        success_rate = (successful / total * 100) if total > 0 else 0
        
        # Speedup metrics
        cursor = self.conn.execute("""
            SELECT 
                AVG(speedup_factor) as avg_speedup,
                MIN(speedup_factor) as min_speedup,
                MAX(speedup_factor) as max_speedup,
                AVG(total_execution_time) as avg_total_time
            FROM speedup_metrics
            WHERE timestamp > ?
        """, (cutoff_date,))
        
        speedup_row = cursor.fetchone()
        avg_speedup, min_speedup, max_speedup, avg_total_time = speedup_row if speedup_row else (0, 0, 0, 0)
        
        # Quality metrics
        cursor = self.conn.execute("""
            SELECT 
                AVG(quality_score) as avg_quality,
                SUM(CASE WHEN passed_threshold = 1 THEN 1 ELSE 0 END) as passed_count,
                COUNT(*) as total_quality_checks
            FROM quality_metrics
            WHERE timestamp > ?
        """, (cutoff_date,))
        
        quality_row = cursor.fetchone()
        avg_quality, passed_count, total_checks = quality_row if quality_row else (0, 0, 0)
        
        quality_pass_rate = (passed_count / total_checks * 100) if total_checks > 0 else 0
        
        return {
            "period_days": days,
            "overall": {
                "total_tasks": total or 0,
                "successful_tasks": successful or 0,
                "success_rate_percentage": round(success_rate, 2),
                "avg_execution_time_seconds": round(avg_time, 2) if avg_time else 0,
                "min_execution_time_seconds": round(min_time, 2) if min_time else 0,
                "max_execution_time_seconds": round(max_time, 2) if max_time else 0
            },
            "speedup": {
                "avg_speedup_factor": round(avg_speedup, 2) if avg_speedup else 0,
                "min_speedup_factor": round(min_speedup, 2) if min_speedup else 0,
                "max_speedup_factor": round(max_speedup, 2) if max_speedup else 0,
                "avg_total_execution_seconds": round(avg_total_time, 2) if avg_total_time else 0,
                "comparison": f"{round(avg_speedup, 1)}x faster than manual (4 hours)" if avg_speedup else "N/A"
            },
            "quality": {
                "avg_quality_score": round(avg_quality, 2) if avg_quality else 0,
                "quality_pass_rate_percentage": round(quality_pass_rate, 2),
                "total_quality_checks": total_checks or 0,
                "passed_checks": passed_count or 0
            }
        }
    
    def get_agent_performance(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get performance metrics per agent."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor = self.conn.execute("""
            SELECT 
                agent_name,
                COUNT(*) as total_tasks,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_tasks,
                AVG(execution_time) as avg_execution_time,
                AVG(quality_score) as avg_quality_score
            FROM execution_metrics
            WHERE timestamp > ?
            GROUP BY agent_name
            ORDER BY total_tasks DESC
        """, (cutoff_date,))
        
        agents = []
        for row in cursor.fetchall():
            agent_name, total, successful, avg_time, avg_quality = row
            success_rate = (successful / total * 100) if total > 0 else 0
            
            agents.append({
                "agent_name": agent_name,
                "total_tasks": total,
                "successful_tasks": successful,
                "success_rate_percentage": round(success_rate, 2),
                "avg_execution_time_seconds": round(avg_time, 2) if avg_time else 0,
                "avg_quality_score": round(avg_quality, 2) if avg_quality else 0
            })
        
        return agents
    
    def get_quality_trends(self, days: int = 7) -> Dict[str, List]:
        """Get quality score trends over time."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        cursor = self.conn.execute("""
            SELECT 
                DATE(timestamp) as date,
                agent_type,
                AVG(quality_score) as avg_score
            FROM quality_metrics
            WHERE timestamp > ?
            GROUP BY DATE(timestamp), agent_type
            ORDER BY date DESC, agent_type
        """, (cutoff_date,))
        
        trends = {}
        for row in cursor.fetchall():
            date, agent_type, avg_score = row
            if agent_type not in trends:
                trends[agent_type] = []
            trends[agent_type].append({
                "date": date,
                "avg_quality_score": round(avg_score, 2)
            })
        
        return trends
    
    def get_speedup_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent speedup history."""
        cursor = self.conn.execute("""
            SELECT 
                task_id,
                total_execution_time,
                manual_estimate_hours,
                speedup_factor,
                agents_used,
                timestamp
            FROM speedup_metrics
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        history = []
        for row in cursor.fetchall():
            task_id, exec_time, manual_hours, speedup, agents, timestamp = row
            history.append({
                "task_id": task_id,
                "execution_time_seconds": round(exec_time, 2),
                "manual_estimate_hours": manual_hours,
                "speedup_factor": round(speedup, 2),
                "agents_used": agents,
                "timestamp": timestamp,
                "time_saved_hours": round(manual_hours - (exec_time / 3600), 2)
            })
        
        return history
    
    def get_comparison_report(self) -> Dict[str, Any]:
        """Generate comprehensive comparison report for demo/presentation."""
        summary = self.get_performance_summary(days=30)
        agent_perf = self.get_agent_performance(days=30)
        speedup_history = self.get_speedup_history(limit=10)
        
        # Calculate aggregates
        if speedup_history:
            speedups = [h['speedup_factor'] for h in speedup_history]
            time_saved = [h['time_saved_hours'] for h in speedup_history]
            
            avg_speedup = statistics.mean(speedups)
            median_speedup = statistics.median(speedups)
            total_time_saved = sum(time_saved)
        else:
            avg_speedup = 0
            median_speedup = 0
            total_time_saved = 0
        
        return {
            "report_date": datetime.now().isoformat(),
            "summary": summary,
            "highlights": {
                "avg_speedup": f"{round(avg_speedup, 1)}x",
                "median_speedup": f"{round(median_speedup, 1)}x",
                "total_time_saved_hours": round(total_time_saved, 2),
                "total_time_saved_days": round(total_time_saved / 24, 2),
                "best_performing_agent": max(agent_perf, key=lambda x: x['success_rate_percentage'])['agent_name'] if agent_perf else "N/A",
                "avg_quality_score": summary['quality']['avg_quality_score']
            },
            "agent_performance": agent_perf,
            "recent_speedups": speedup_history[:5]  # Top 5
        }
    
    def export_to_json(self, filename: str = None):
        """Export all metrics to JSON for external analysis."""
        if not filename:
            filename = f"metrics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            "export_date": datetime.now().isoformat(),
            "performance_summary": self.get_performance_summary(days=30),
            "agent_performance": self.get_agent_performance(days=30),
            "quality_trends": self.get_quality_trends(days=30),
            "speedup_history": self.get_speedup_history(limit=50),
            "comparison_report": self.get_comparison_report()
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        return filename

# Singleton instance
_metrics_collector = None

def get_metrics_collector():
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector