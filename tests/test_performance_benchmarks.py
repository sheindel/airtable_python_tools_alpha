"""Performance benchmarks for code generators.

Tests the performance of various code generation operations to track
and identify bottlenecks, especially for large schemas.

Usage:
    # Run all benchmarks
    pytest tests/test_performance_benchmarks.py -v
    
    # Run with custom schema
    BENCHMARK_SCHEMA=/path/to/schema.json pytest tests/test_performance_benchmarks.py
    
    # Run specific benchmark
    pytest tests/test_performance_benchmarks.py::TestPythonGeneratorPerformance::test_python_library_generation_time -v
"""

import sys
import time
import json
import os
from pathlib import Path
from typing import Dict, Any

import pytest

# Add web directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))

from code_generators.python_runtime_generator import generate_python_library
from code_generators.javascript_runtime_generator import generate_javascript_library
from code_generators.sql_runtime_generator import generate_all_sql_files
from code_generators.workflows import create_workflow
from types_generator import generate_all_python_files, generate_all_typescript_files


# Performance thresholds (in seconds)
THRESHOLDS = {
    "python_library": 5.0,  # Python SDK generation should complete in < 5s
    "javascript_library": 3.0,  # JS library should be faster
    "sql_generation": 4.0,  # SQL generation
    "typescript_types": 2.0,  # TypeScript types
    "python_types": 2.0,  # Python types
    "full_workflow": 10.0,  # Complete workflow
}


def get_benchmark_schema() -> Dict[str, Any]:
    """
    Load schema for benchmarking.
    
    Priority:
    1. Environment variable BENCHMARK_SCHEMA (path to JSON file)
    2. External schema in tests/schemas/benchmark.json (gitignored)
    3. Default demo_base_schema.json
    
    Returns:
        Airtable metadata dictionary
    """
    # Check environment variable
    env_schema = os.environ.get("BENCHMARK_SCHEMA")
    if env_schema and os.path.exists(env_schema):
        with open(env_schema, 'r') as f:
            return json.load(f)
    
    # Check for external benchmark schema
    external_schema = Path(__file__).parent / "schemas" / "benchmark.json"
    if external_schema.exists():
        with open(external_schema, 'r') as f:
            return json.load(f)
    
    # Fall back to demo schema
    demo_schema = Path(__file__).parent.parent / "demo_base_schema.json"
    with open(demo_schema, 'r') as f:
        return json.load(f)


def measure_time(func, *args, **kwargs):
    """
    Measure execution time of a function.
    
    Returns:
        Tuple of (result, elapsed_time_seconds)
    """
    start = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed = time.perf_counter() - start
    return result, elapsed


def get_schema_stats(metadata: Dict[str, Any]) -> Dict[str, int]:
    """Get statistics about the schema for context."""
    stats = {
        "tables": len(metadata.get("tables", [])),
        "total_fields": 0,
        "formula_fields": 0,
        "lookup_fields": 0,
        "rollup_fields": 0,
    }
    
    for table in metadata.get("tables", []):
        fields = table.get("fields", [])
        stats["total_fields"] += len(fields)
        
        for field in fields:
            field_type = field.get("type", "")
            if field_type == "formula":
                stats["formula_fields"] += 1
            elif field_type == "multipleLookupValues":
                stats["lookup_fields"] += 1
            elif field_type == "rollup":
                stats["rollup_fields"] += 1
    
    return stats


class TestPythonGeneratorPerformance:
    """Benchmarks for Python code generator"""
    
    @pytest.fixture
    def metadata(self):
        """Load benchmark schema"""
        return get_benchmark_schema()
    
    @pytest.fixture
    def schema_stats(self, metadata):
        """Get schema statistics for reporting"""
        return get_schema_stats(metadata)
    
    def test_python_library_generation_time(self, metadata, schema_stats):
        """Benchmark Python runtime library generation"""
        result, elapsed = measure_time(
            generate_python_library,
            metadata,
            options={
                "data_access_mode": "dataclass",
                "include_null_checks": True,
                "include_types": False,
                "include_helpers": True,
            }
        )
        
        # Print statistics
        print(f"\n{'='*60}")
        print(f"Python Library Generation Benchmark")
        print(f"{'='*60}")
        print(f"Schema: {schema_stats['tables']} tables, {schema_stats['total_fields']} fields")
        print(f"  - {schema_stats['formula_fields']} formulas")
        print(f"  - {schema_stats['lookup_fields']} lookups")
        print(f"  - {schema_stats['rollup_fields']} rollups")
        print(f"Time: {elapsed:.3f}s")
        print(f"Threshold: {THRESHOLDS['python_library']}s")
        print(f"Generated: {len(result)} bytes")
        print(f"{'='*60}\n")
        
        # Assert within threshold
        assert elapsed < THRESHOLDS['python_library'], \
            f"Python library generation took {elapsed:.2f}s, exceeds threshold of {THRESHOLDS['python_library']}s"
    
    def test_python_types_generation_time(self, metadata, schema_stats):
        """Benchmark Python types generation"""
        result, elapsed = measure_time(
            generate_all_python_files,
            metadata,
            include_helpers=True,
            use_dataclasses=True
        )
        
        print(f"\n{'='*60}")
        print(f"Python Types Generation Benchmark")
        print(f"{'='*60}")
        print(f"Schema: {schema_stats['tables']} tables, {schema_stats['total_fields']} fields")
        print(f"Time: {elapsed:.3f}s")
        print(f"Threshold: {THRESHOLDS['python_types']}s")
        print(f"Generated files: {len(result)}")
        print(f"{'='*60}\n")
        
        assert elapsed < THRESHOLDS['python_types'], \
            f"Python types generation took {elapsed:.2f}s, exceeds threshold of {THRESHOLDS['python_types']}s"
    
    def test_server_sdk_workflow_time(self, metadata, schema_stats):
        """Benchmark complete Server SDK workflow"""
        workflow = create_workflow("server-sdk", metadata, {
            "include_helpers": True,
            "include_formula_runtime": True,
            "include_examples": True,
            "type_style": "dataclass",
            "data_access_mode": "dataclass",
            "null_checks": True,
        })
        
        result, elapsed = measure_time(workflow.generate)
        
        print(f"\n{'='*60}")
        print(f"Server SDK Workflow Benchmark")
        print(f"{'='*60}")
        print(f"Schema: {schema_stats['tables']} tables, {schema_stats['total_fields']} fields")
        print(f"Time: {elapsed:.3f}s")
        print(f"Threshold: {THRESHOLDS['full_workflow']}s")
        print(f"Generated files: {len(result)}")
        for filename in result.keys():
            print(f"  - {filename}: {len(result[filename])} bytes")
        print(f"{'='*60}\n")
        
        assert elapsed < THRESHOLDS['full_workflow'], \
            f"Server SDK workflow took {elapsed:.2f}s, exceeds threshold of {THRESHOLDS['full_workflow']}s"


class TestJavaScriptGeneratorPerformance:
    """Benchmarks for JavaScript/TypeScript generator"""
    
    @pytest.fixture
    def metadata(self):
        """Load benchmark schema"""
        return get_benchmark_schema()
    
    @pytest.fixture
    def schema_stats(self, metadata):
        """Get schema statistics for reporting"""
        return get_schema_stats(metadata)
    
    def test_javascript_library_generation_time(self, metadata, schema_stats):
        """Benchmark JavaScript runtime library generation"""
        result, elapsed = measure_time(
            generate_javascript_library,
            metadata,
            options={
                "data_access_mode": "object",
                "use_typescript": False,
                "module_format": "esm",
                "include_helpers": True,
                "include_comments": True,
            }
        )
        
        print(f"\n{'='*60}")
        print(f"JavaScript Library Generation Benchmark")
        print(f"{'='*60}")
        print(f"Schema: {schema_stats['tables']} tables, {schema_stats['total_fields']} fields")
        print(f"Time: {elapsed:.3f}s")
        print(f"Threshold: {THRESHOLDS['javascript_library']}s")
        print(f"Generated: {len(result)} bytes")
        print(f"{'='*60}\n")
        
        assert elapsed < THRESHOLDS['javascript_library'], \
            f"JavaScript library generation took {elapsed:.2f}s, exceeds threshold of {THRESHOLDS['javascript_library']}s"
    
    def test_typescript_types_generation_time(self, metadata, schema_stats):
        """Benchmark TypeScript types generation"""
        result, elapsed = measure_time(
            generate_all_typescript_files,
            metadata,
            include_helpers=True
        )
        
        print(f"\n{'='*60}")
        print(f"TypeScript Types Generation Benchmark")
        print(f"{'='*60}")
        print(f"Schema: {schema_stats['tables']} tables, {schema_stats['total_fields']} fields")
        print(f"Time: {elapsed:.3f}s")
        print(f"Threshold: {THRESHOLDS['typescript_types']}s")
        print(f"Generated files: {len(result)}")
        print(f"{'='*60}\n")
        
        assert elapsed < THRESHOLDS['typescript_types'], \
            f"TypeScript types generation took {elapsed:.2f}s, exceeds threshold of {THRESHOLDS['typescript_types']}s"


class TestSQLGeneratorPerformance:
    """Benchmarks for SQL generator"""
    
    @pytest.fixture
    def metadata(self):
        """Load benchmark schema"""
        return get_benchmark_schema()
    
    @pytest.fixture
    def schema_stats(self, metadata):
        """Get schema statistics for reporting"""
        return get_schema_stats(metadata)
    
    def test_sql_generation_time(self, metadata, schema_stats):
        """Benchmark SQL schema and functions generation"""
        result, elapsed = measure_time(
            generate_all_sql_files,
            metadata,
            mode="functions",
            dialect="postgresql",
            include_formulas=True,
            include_views=True,
        )
        
        print(f"\n{'='*60}")
        print(f"SQL Generation Benchmark")
        print(f"{'='*60}")
        print(f"Schema: {schema_stats['tables']} tables, {schema_stats['total_fields']} fields")
        print(f"Time: {elapsed:.3f}s")
        print(f"Threshold: {THRESHOLDS['sql_generation']}s")
        print(f"Generated files: {len(result)}")
        print(f"{'='*60}\n")
        
        assert elapsed < THRESHOLDS['sql_generation'], \
            f"SQL generation took {elapsed:.2f}s, exceeds threshold of {THRESHOLDS['sql_generation']}s"


class TestFullWorkflowPerformance:
    """Benchmarks for complete workflows"""
    
    @pytest.fixture
    def metadata(self):
        """Load benchmark schema"""
        return get_benchmark_schema()
    
    @pytest.fixture
    def schema_stats(self, metadata):
        """Get schema statistics for reporting"""
        return get_schema_stats(metadata)
    
    def test_fullstack_workflow_time(self, metadata, schema_stats):
        """Benchmark complete full-stack workflow"""
        workflow = create_workflow("fullstack", metadata, {
            "include_typescript": True,
            "include_python": True,
            "include_sql": True,
            "include_readme": True,
            "include_config": True,
        })
        
        result, elapsed = measure_time(workflow.generate)
        
        print(f"\n{'='*60}")
        print(f"Full-Stack Workflow Benchmark")
        print(f"{'='*60}")
        print(f"Schema: {schema_stats['tables']} tables, {schema_stats['total_fields']} fields")
        print(f"Time: {elapsed:.3f}s")
        print(f"Threshold: {THRESHOLDS['full_workflow']}s")
        print(f"Generated files: {len(result)}")
        total_bytes = sum(len(content) for content in result.values())
        print(f"Total output: {total_bytes:,} bytes ({total_bytes/1024:.1f} KB)")
        print(f"{'='*60}\n")
        
        assert elapsed < THRESHOLDS['full_workflow'], \
            f"Full-stack workflow took {elapsed:.2f}s, exceeds threshold of {THRESHOLDS['full_workflow']}s"
    
    @pytest.mark.parametrize("workflow_id", ["client-library", "server-sdk", "database-schema"])
    def test_individual_workflows_time(self, workflow_id, metadata, schema_stats):
        """Benchmark individual workflows"""
        workflow = create_workflow(workflow_id, metadata)
        result, elapsed = measure_time(workflow.generate)
        
        print(f"\n{'='*60}")
        print(f"{workflow_id} Workflow Benchmark")
        print(f"{'='*60}")
        print(f"Schema: {schema_stats['tables']} tables, {schema_stats['total_fields']} fields")
        print(f"Time: {elapsed:.3f}s")
        print(f"Generated files: {len(result)}")
        print(f"{'='*60}\n")
        
        # Each individual workflow should be faster than full workflow
        assert elapsed < THRESHOLDS['full_workflow'], \
            f"{workflow_id} workflow took {elapsed:.2f}s, exceeds threshold of {THRESHOLDS['full_workflow']}s"


if __name__ == "__main__":
    # Allow running directly for quick benchmarking
    print("Running performance benchmarks...")
    print(f"Using schema: {get_benchmark_schema().get('id', 'Unknown')}")
    pytest.main([__file__, "-v", "-s"])
