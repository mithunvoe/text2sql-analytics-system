"""
Integration tests for the complete Text2SQL pipeline
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import time

from src.query_cache import QueryCache
from src.query_history import QueryHistory
from src.performance_monitor import PerformanceMonitor


class TestQueryCache:
    """Tests for query caching system"""
    
    @pytest.fixture
    def cache(self, tmp_path):
        """Create temporary cache"""
        db_path = tmp_path / "test_cache.db"
        return QueryCache(db_path=str(db_path), ttl_seconds=60)
    
    def test_cache_miss(self, cache):
        """Test cache miss on first request"""
        result = cache.get("What is the total revenue?")
        assert result is None
    
    def test_cache_put_and_get(self, cache):
        """Test storing and retrieving from cache"""
        question = "How many products?"
        sql = "SELECT COUNT(*) FROM products"
        results = [{'count': 77}]
        
        cache.put(question, sql, results, 0.5)
        
        cached = cache.get(question)
        assert cached is not None
        assert cached.generated_sql == sql
        assert cached.results == results
    
    def test_cache_hit_count(self, cache):
        """Test that hit count is incremented"""
        question = "List all customers"
        cache.put(question, "SELECT * FROM customers", [], 0.1)
        
        # First hit
        cached1 = cache.get(question)
        assert cached1.hit_count == 1
        
        # Second hit
        cached2 = cache.get(question)
        assert cached2.hit_count == 2
    
    def test_cache_expiration(self, cache):
        """Test cache entry expiration"""
        # Create cache with 1 second TTL
        cache.ttl_seconds = 1
        
        cache.put("test query", "SELECT 1", [], 0.1)
        
        # Should be available immediately
        assert cache.get("test query") is not None
        
        # Wait for expiration
        time.sleep(1.5)
        
        # Should be expired
        assert cache.get("test query") is None
    
    def test_cache_statistics(self, cache):
        """Test cache statistics"""
        cache.put("query1", "SELECT 1", [], 0.1)
        cache.put("query2", "SELECT 2", [], 0.2)
        
        stats = cache.get_stats()
        
        assert 'total_entries' in stats
        assert stats['total_entries'] >= 2


class TestQueryHistory:
    """Tests for query history tracking"""
    
    @pytest.fixture
    def history(self, tmp_path):
        """Create temporary history"""
        db_path = tmp_path / "test_history.db"
        return QueryHistory(db_path=str(db_path))
    
    def test_add_entry(self, history):
        """Test adding history entry"""
        entry_id = history.add_entry(
            natural_language="How many products?",
            generated_sql="SELECT COUNT(*) FROM products",
            execution_success=True,
            row_count=1,
            execution_time=0.5,
            quality_score=0.8
        )
        
        assert entry_id > 0
    
    def test_get_recent_queries(self, history):
        """Test retrieving recent queries"""
        # Add multiple entries
        for i in range(5):
            history.add_entry(
                natural_language=f"Query {i}",
                generated_sql=f"SELECT {i}",
                execution_success=True,
                row_count=1,
                execution_time=0.1
            )
        
        recent = history.get_recent_queries(limit=3)
        
        assert len(recent) == 3
        assert recent[0].natural_language == "Query 4"  # Most recent
    
    def test_get_successful_queries(self, history):
        """Test filtering successful queries"""
        history.add_entry("success 1", "SELECT 1", True, 1, 0.1)
        history.add_entry("fail 1", "SELECT 2", False, 0, 0.1, error_message="Error")
        history.add_entry("success 2", "SELECT 3", True, 1, 0.1)
        
        successful = history.get_successful_queries(limit=10)
        
        assert len(successful) == 2
        assert all(entry.execution_success for entry in successful)
    
    def test_get_failed_queries(self, history):
        """Test filtering failed queries"""
        history.add_entry("success 1", "SELECT 1", True, 1, 0.1)
        history.add_entry("fail 1", "SELECT 2", False, 0, 0.1, error_message="Error")
        
        failed = history.get_failed_queries(limit=10)
        
        assert len(failed) == 1
        assert not failed[0].execution_success
    
    def test_statistics(self, history):
        """Test history statistics"""
        # Add some successful and failed queries
        for i in range(7):
            history.add_entry(f"Query {i}", f"SELECT {i}", True, 1, 0.1, quality_score=0.8)
        
        for i in range(3):
            history.add_entry(f"Failed {i}", f"SELECT {i}", False, 0, 0.1, error_message="Error")
        
        stats = history.get_statistics()
        
        assert stats['total_queries'] == 10
        assert stats['successful_queries'] == 7
        assert stats['failed_queries'] == 3
        assert stats['success_rate'] == 70.0


class TestPerformanceMonitor:
    """Tests for performance monitoring"""
    
    @pytest.fixture
    def monitor(self, tmp_path):
        """Create temporary monitor"""
        db_path = tmp_path / "test_monitor.db"
        return PerformanceMonitor(db_path=str(db_path))
    
    def test_timer_operations(self, monitor):
        """Test start/end timer"""
        monitor.start_timer("test_operation")
        time.sleep(0.1)
        elapsed = monitor.end_timer("test_operation")
        
        assert elapsed >= 0.1
    
    def test_record_metric(self, monitor):
        """Test recording metrics"""
        monitor.record_metric("test_metric", 42.0, {"info": "test"})
        
        metrics = monitor.get_metrics("test_metric", hours=1)
        
        assert len(metrics) == 1
        assert metrics[0].metric_value == 42.0
    
    def test_get_statistics(self, monitor):
        """Test metric statistics"""
        # Record multiple values
        for i in range(10):
            monitor.record_metric("response_time", i * 0.1)
        
        stats = monitor.get_statistics("response_time", hours=1)
        
        assert stats['count'] == 10
        assert stats['minimum'] == 0.0
        assert stats['maximum'] == 0.9


class TestEndToEndIntegration:
    """End-to-end integration tests"""
    
    @pytest.fixture
    def components(self, tmp_path):
        """Set up all components"""
        cache = QueryCache(db_path=str(tmp_path / "cache.db"))
        history = QueryHistory(db_path=str(tmp_path / "history.db"))
        monitor = PerformanceMonitor(db_path=str(tmp_path / "monitor.db"))
        
        return {
            'cache': cache,
            'history': history,
            'monitor': monitor
        }
    
    def test_complete_query_flow(self, components):
        """Test complete query flow with all components"""
        cache = components['cache']
        history = components['history']
        monitor = components['monitor']
        
        question = "How many products?"
        sql = "SELECT COUNT(*) FROM products"
        results = [{'count': 77}]
        
        # Start monitoring
        monitor.start_timer("query_processing")
        
        # Check cache (miss)
        cached = cache.get(question)
        assert cached is None
        
        # Simulate query execution
        time.sleep(0.01)
        
        # Add to history
        entry_id = history.add_entry(
            natural_language=question,
            generated_sql=sql,
            execution_success=True,
            row_count=1,
            execution_time=0.01,
            quality_score=0.9
        )
        
        # Cache result
        cache.put(question, sql, results, 0.01)
        
        # End monitoring
        elapsed = monitor.end_timer("query_processing")
        
        # Verify all components worked
        assert entry_id > 0
        assert elapsed > 0
        
        # Second request should hit cache
        cached = cache.get(question)
        assert cached is not None
        assert cached.results == results


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=src", "--cov-report=html"])
