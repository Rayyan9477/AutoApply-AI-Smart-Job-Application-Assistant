"""
Database performance monitoring and query optimization.
"""
import time
import logging
from functools import wraps
from typing import Dict, List, Any, Callable
from threading import Lock
from datetime import datetime, timedelta
from sqlalchemy import event
from sqlalchemy.engine import Engine
import csv
import json
from pathlib import Path

# Set up logging
logger = logging.getLogger(__name__)

class QueryPerformanceMonitor:
    """Monitor database query performance."""
    
    def __init__(self):
        self.query_stats: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self.slow_query_threshold = 1.0  # seconds
        
    def record_query(self, query: str, duration: float) -> None:
        """Record query execution statistics."""
        with self._lock:
            if query not in self.query_stats:
                self.query_stats[query] = {
                    "count": 0,
                    "total_time": 0.0,
                    "min_time": float("inf"),
                    "max_time": 0.0,
                    "avg_time": 0.0,
                    "last_executed": None
                }
            
            stats = self.query_stats[query]
            stats["count"] += 1
            stats["total_time"] += duration
            stats["min_time"] = min(stats["min_time"], duration)
            stats["max_time"] = max(stats["max_time"], duration)
            stats["avg_time"] = stats["total_time"] / stats["count"]
            stats["last_executed"] = datetime.utcnow()
            
            if duration > self.slow_query_threshold:
                logger.warning(f"Slow query detected ({duration:.2f}s): {query}")
                
    def get_slow_queries(self, threshold: float = None) -> List[Dict[str, Any]]:
        """Get list of slow queries above threshold."""
        threshold = threshold or self.slow_query_threshold
        slow_queries = []
        
        with self._lock:
            for query, stats in self.query_stats.items():
                if stats["avg_time"] > threshold:
                    slow_queries.append({
                        "query": query,
                        "stats": stats.copy()
                    })
        
        return sorted(slow_queries, key=lambda x: x["stats"]["avg_time"], reverse=True)
        
    def get_most_frequent_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most frequently executed queries."""
        with self._lock:
            frequent_queries = [
                {"query": query, "stats": stats.copy()}
                for query, stats in self.query_stats.items()
            ]
        
        return sorted(frequent_queries, key=lambda x: x["stats"]["count"], reverse=True)[:limit]
        
    def reset_stats(self) -> None:
        """Reset all query statistics."""
        with self._lock:
            self.query_stats.clear()

# Create global monitor instance
query_monitor = QueryPerformanceMonitor()

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query start time."""
    conn.info.setdefault('query_start_time', []).append(time.time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Calculate query execution time and record statistics."""
    total_time = time.time() - conn.info['query_start_time'].pop()
    query_monitor.record_query(statement, total_time)

def log_slow_queries(func: Callable) -> Callable:
    """Decorator to log slow query executions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            return func(*args, **kwargs)
        finally:
            duration = time.time() - start_time
            if duration > query_monitor.slow_query_threshold:
                logger.warning(
                    f"Slow query execution in {func.__name__} ({duration:.2f}s)"
                )
    return wrapper

def get_query_stats() -> Dict[str, Any]:
    """Get current query statistics summary."""
    stats = {
        "total_queries": 0,
        "total_time": 0.0,
        "avg_time": 0.0,
        "slow_queries": 0
    }
    
    with query_monitor._lock:
        for query_stats in query_monitor.query_stats.values():
            stats["total_queries"] += query_stats["count"]
            stats["total_time"] += query_stats["total_time"]
            if query_stats["avg_time"] > query_monitor.slow_query_threshold:
                stats["slow_queries"] += 1
                
        if stats["total_queries"] > 0:
            stats["avg_time"] = stats["total_time"] / stats["total_queries"]
            
    return stats

def analyze_query_patterns() -> Dict[str, Any]:
    """Analyze query patterns and provide optimization recommendations."""
    analysis = {
        "recommendations": [],
        "query_patterns": {},
        "peak_times": {}
    }
    
    with query_monitor._lock:
        # Analyze query patterns
        for query, stats in query_monitor.query_stats.items():
            # Check for frequent queries that might benefit from caching
            if stats["count"] > 100 and stats["avg_time"] > 0.1:
                analysis["recommendations"].append({
                    "type": "caching",
                    "query": query,
                    "message": f"Consider caching results for frequently used query "
                             f"(executed {stats['count']} times, avg time {stats['avg_time']:.2f}s)"
                })
            
            # Check for slow queries that might need optimization
            if stats["avg_time"] > query_monitor.slow_query_threshold:
                analysis["recommendations"].append({
                    "type": "optimization",
                    "query": query,
                    "message": f"Query performing slowly (avg time {stats['avg_time']:.2f}s). "
                             f"Consider adding indexes or optimizing query structure."
                })
                
            # Track query patterns by hour
            if stats["last_executed"]:
                hour = stats["last_executed"].hour
                if hour not in analysis["peak_times"]:
                    analysis["peak_times"][hour] = 0
                analysis["peak_times"][hour] += stats["count"]
    
    return analysis

# Add monitoring service class to existing file
class DatabaseMonitorService:
    """Service for monitoring database health and performance."""
    
    def __init__(self, engine, monitor=query_monitor):
        self.engine = engine
        self.monitor = monitor
        self.alerts = []
        self.last_check = None
        
    async def check_database_health(self) -> Dict[str, Any]:
        """Check database health metrics."""
        try:
            health_check = {
                "status": "healthy",
                "last_check": datetime.utcnow(),
                "connection_pool": {},
                "query_stats": {},
                "alerts": []
            }
            
            # Check connection pool
            pool = self.engine.pool
            health_check["connection_pool"] = {
                "size": pool.size(),
                "checkedin": pool.checkedin(),
                "overflow": pool.overflow(),
                "checkedout": pool.checkedout()
            }
            
            # Get query statistics
            query_stats = get_query_stats()
            health_check["query_stats"] = query_stats
            
            # Check for potential issues
            if query_stats["slow_queries"] > 0:
                health_check["alerts"].append({
                    "level": "warning",
                    "message": f"Found {query_stats['slow_queries']} slow queries"
                })
            
            if pool.checkedout() / pool.size() > 0.8:
                health_check["alerts"].append({
                    "level": "warning",
                    "message": "Connection pool usage above 80%"
                })
            
            # Get query pattern analysis
            pattern_analysis = analyze_query_patterns()
            health_check["query_patterns"] = pattern_analysis
            
            # Add recommendations
            if pattern_analysis["recommendations"]:
                health_check["recommendations"] = pattern_analysis["recommendations"]
            
            self.last_check = health_check["last_check"]
            return health_check
            
        except Exception as e:
            logger.error(f"Error checking database health: {e}")
            return {
                "status": "error",
                "last_check": datetime.utcnow(),
                "error": str(e)
            }
    
    def get_slow_query_report(self, days: int = 1) -> Dict[str, Any]:
        """Generate report of slow queries over the specified period."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        slow_queries = self.monitor.get_slow_queries()
        
        recent_slow_queries = [
            q for q in slow_queries
            if q["stats"]["last_executed"] and q["stats"]["last_executed"] > cutoff
        ]
        
        return {
            "period_days": days,
            "total_slow_queries": len(recent_slow_queries),
            "queries": recent_slow_queries,
            "summary": {
                "total_time": sum(q["stats"]["total_time"] for q in recent_slow_queries),
                "avg_time": sum(q["stats"]["avg_time"] for q in recent_slow_queries) / len(recent_slow_queries)
                if recent_slow_queries else 0
            }
        }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current database performance metrics."""
        stats = get_query_stats()
        
        return {
            "timestamp": datetime.utcnow(),
            "query_stats": stats,
            "pool_stats": {
                "size": self.engine.pool.size(),
                "overflow": self.engine.pool.overflow(),
                "checkedout": self.engine.pool.checkedout()
            },
            "performance_score": self._calculate_performance_score(stats)
        }
    
    def _calculate_performance_score(self, stats: Dict[str, Any]) -> float:
        """Calculate overall performance score (0-100)."""
        score = 100.0
        
        # Penalize for slow queries
        if stats["total_queries"] > 0:
            slow_query_ratio = stats["slow_queries"] / stats["total_queries"]
            score -= slow_query_ratio * 30  # Up to 30 point penalty
        
        # Penalize for high average query time
        if stats["avg_time"] > 1.0:  # More than 1 second average
            score -= min((stats["avg_time"] - 1.0) * 10, 30)  # Up to 30 point penalty
        
        # Penalize for connection pool exhaustion
        pool_usage = self.engine.pool.checkedout() / self.engine.pool.size()
        if pool_usage > 0.8:
            score -= (pool_usage - 0.8) * 100  # Up to 20 point penalty
        
        return max(0, min(score, 100))  # Ensure score is between 0 and 100
    
    def export_metrics(self, format: str = 'csv', output_dir: str = 'metrics') -> str:
        """Export current metrics to file for analysis.
        
        Args:
            format: Output format ('csv' or 'json')
            output_dir: Directory to save metrics files
            
        Returns:
            Path to the exported metrics file
        """
        metrics = self.get_performance_metrics()
        timestamp = metrics["timestamp"].strftime("%Y%m%d-%H%M%S")
        
        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if format == 'csv':
            filepath = output_path / f"db_metrics_{timestamp}.csv"
            self._export_csv(metrics, filepath)
        else:
            filepath = output_path / f"db_metrics_{timestamp}.json"
            self._export_json(metrics, filepath)
            
        return str(filepath)
    
    def _export_csv(self, metrics: dict, filepath: Path) -> None:
        """Export metrics to CSV format."""
        # Flatten metrics for CSV format
        flat_metrics = {
            "timestamp": metrics["timestamp"],
            "performance_score": metrics["performance_score"],
            **metrics["query_stats"],
            **{f"pool_{k}": v for k, v in metrics["pool_stats"].items()}
        }
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=flat_metrics.keys())
            writer.writeheader()
            writer.writerow(flat_metrics)
    
    def _export_json(self, metrics: dict, filepath: Path) -> None:
        """Export metrics to JSON format."""
        # Convert datetime to string for JSON serialization
        metrics_copy = metrics.copy()
        metrics_copy["timestamp"] = metrics_copy["timestamp"].isoformat()
        
        with open(filepath, 'w') as f:
            json.dump(metrics_copy, f, indent=2)
    
    def export_slow_queries_report(self, days: int = 7, format: str = 'csv', 
                                 output_dir: str = 'metrics') -> str:
        """Export slow queries report to file.
        
        Args:
            days: Number of days to include in report
            format: Output format ('csv' or 'json')
            output_dir: Directory to save report files
            
        Returns:
            Path to the exported report file
        """
        report = self.get_slow_query_report(days)
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        
        # Ensure output directory exists
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if format == 'csv':
            filepath = output_path / f"slow_queries_{timestamp}.csv"
            self._export_slow_queries_csv(report, filepath)
        else:
            filepath = output_path / f"slow_queries_{timestamp}.json"
            self._export_slow_queries_json(report, filepath)
            
        return str(filepath)
    
    def _export_slow_queries_csv(self, report: dict, filepath: Path) -> None:
        """Export slow queries report to CSV format."""
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Query", "Average Time (s)", "Executions", 
                "Total Time (s)", "Last Executed"
            ])
            
            for query in report["queries"]:
                writer.writerow([
                    query["query"],
                    query["stats"]["avg_time"],
                    query["stats"]["count"],
                    query["stats"]["total_time"],
                    query["stats"]["last_executed"].isoformat()
                ])
                
            # Write summary
            writer.writerow([])
            writer.writerow(["Summary"])
            writer.writerow(["Total Slow Queries", report["total_slow_queries"]])
            writer.writerow(["Total Time (s)", report["summary"]["total_time"]])
            writer.writerow(["Average Time (s)", report["summary"]["avg_time"]])
    
    def _export_slow_queries_json(self, report: dict, filepath: Path) -> None:
        """Export slow queries report to JSON format."""
        # Convert datetime objects to strings for JSON serialization
        report_copy = report.copy()
        for query in report_copy["queries"]:
            query["stats"] = query["stats"].copy()
            query["stats"]["last_executed"] = query["stats"]["last_executed"].isoformat()
            
        with open(filepath, 'w') as f:
            json.dump(report_copy, f, indent=2)
            
    def get_metrics_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get historical metrics from exported files.
        
        Args:
            days: Number of days of history to retrieve
            
        Returns:
            List of metrics dictionaries
        """
        metrics_dir = Path('metrics')
        if not metrics_dir.exists():
            return []
            
        cutoff = datetime.utcnow() - timedelta(days=days)
        metrics_files = list(metrics_dir.glob('db_metrics_*.json'))
        
        metrics_history = []
        for file in metrics_files:
            # Extract timestamp from filename
            try:
                timestamp = datetime.strptime(
                    file.stem.replace('db_metrics_', ''),
                    "%Y%m%d-%H%M%S"
                )
                if timestamp >= cutoff:
                    with open(file) as f:
                        metrics = json.load(f)
                        metrics["timestamp"] = datetime.fromisoformat(metrics["timestamp"])
                        metrics_history.append(metrics)
            except (ValueError, json.JSONDecodeError):
                continue
                
        return sorted(metrics_history, key=lambda x: x["timestamp"])