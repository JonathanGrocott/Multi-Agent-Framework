"""SQLite-based history tracking service for workflow logging."""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from pathlib import Path


class HistoryService:
    """
    SQLite-based workflow history tracking.
    
    Logs user queries and final results for audit trail and analysis.
    """
    
    SCHEMA = """
    CREATE TABLE IF NOT EXISTS workflow_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        user_query TEXT NOT NULL,
        final_result TEXT NOT NULL,
        metadata TEXT,
        execution_time_ms INTEGER,
        status TEXT
    );
    
    CREATE INDEX IF NOT EXISTS idx_timestamp ON workflow_history(timestamp);
    CREATE INDEX IF NOT EXISTS idx_status ON workflow_history(status);
    """
    
    def __init__(self, database_path: str = "./workflow_history.db"):
        """
        Initialize history service.
        
        Args:
            database_path: Path to SQLite database file
        """
        self.database_path = database_path
        self._ensure_database()
    
    def _ensure_database(self) -> None:
        """Create database and schema if they don't exist."""
        # Create parent directory if needed
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Create schema
        with sqlite3.connect(self.database_path) as conn:
            conn.executescript(self.SCHEMA)
    
    def log_workflow(
        self,
        user_query: str,
        final_result: str,
        metadata: Optional[Dict[str, Any]] = None,
        execution_time_ms: Optional[int] = None,
        status: str = "success"
    ) -> int:
        """
        Log a completed workflow.
        
        Args:
            user_query: Original user query
            final_result: Final output from workflow
            metadata: Optional metadata (machine_id, agent_count, etc.)
            execution_time_ms: Execution time in milliseconds
            status: Status ("success" or "failed")
            
        Returns:
            ID of created record
        """
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO workflow_history 
                (user_query, final_result, metadata, execution_time_ms, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    user_query,
                    final_result,
                    json.dumps(metadata) if metadata else None,
                    execution_time_ms,
                    status
                )
            )
            return cursor.lastrowid
    
    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent workflow history.
        
        Args:
            limit: Number of records to return
            
        Returns:
            List of workflow records
        """
        with sqlite3.connect(self.database_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, timestamp, user_query, final_result, metadata, 
                       execution_time_ms, status
                FROM workflow_history
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,)
            )
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def search(
        self,
        query: Optional[str] = None,
        status: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search workflow history.
        
        Args:
            query: Search in user_query field
            status: Filter by status
            since: Only return records after this timestamp
            limit: Maximum records to return
            
        Returns:
            Matching workflow records
        """
        sql = """
            SELECT id, timestamp, user_query, final_result, metadata,
                   execution_time_ms, status
            FROM workflow_history
            WHERE 1=1
        """
        params = []
        
        if query:
            sql += " AND user_query LIKE ?"
            params.append(f"%{query}%")
        
        if status:
            sql += " AND status = ?"
            params.append(status)
        
        if since:
            sql += " AND timestamp >= ?"
            params.append(since.isoformat())
        
        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.database_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def cleanup_old_records(self, retention_days: int = 90) -> int:
        """
        Delete records older than retention period.
        
        Args:
            retention_days: Number of days to keep
            
        Returns:
            Number of records deleted
        """
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM workflow_history WHERE timestamp < ?",
                (cutoff_date.isoformat(),)
            )
            return cursor.rowcount
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get usage statistics.
        
        Returns:
            Dictionary with statistics
        """
        with sqlite3.connect(self.database_path) as conn:
            cursor = conn.cursor()
            
            # Total queries
            cursor.execute("SELECT COUNT(*) FROM workflow_history")
            total = cursor.fetchone()[0]
            
            # Success/failure counts
            cursor.execute(
                "SELECT status, COUNT(*) FROM workflow_history GROUP BY status"
            )
            status_counts = dict(cursor.fetchall())
            
            # Average execution time
            cursor.execute(
                "SELECT AVG(execution_time_ms) FROM workflow_history "
                "WHERE execution_time_ms IS NOT NULL"
            )
            avg_time = cursor.fetchone()[0]
            
            # Oldest and newest records
            cursor.execute(
                "SELECT MIN(timestamp), MAX(timestamp) FROM workflow_history"
            )
            oldest, newest = cursor.fetchone()
            
            return {
                "total_workflows": total,
                "status_counts": status_counts,
                "average_execution_time_ms": avg_time,
                "oldest_record": oldest,
                "newest_record": newest
            }
    
    def __repr__(self) -> str:
        stats = self.get_statistics()
        return f"HistoryService(db={self.database_path}, total={stats['total_workflows']})"
