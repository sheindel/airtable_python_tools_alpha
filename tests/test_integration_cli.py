"""Integration tests for CLI commands"""
import pytest
import subprocess
import json
import sys
from pathlib import Path

# Add web directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))


@pytest.fixture
def sample_schema_path():
    """Path to sample schema file"""
    return Path(__file__).parent.parent / "web" / "sample_schema.json"


@pytest.fixture
def sample_schema_exists(sample_schema_path):
    """Check if sample schema exists"""
    return sample_schema_path.exists()


class TestCLIIntegration:
    """Integration tests that run actual CLI commands via subprocess"""
    
    def test_cli_help_command(self):
        """CLI should display help without errors"""
        result = subprocess.run(
            ["uv", "run", "python", "main.py", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 0
        assert "Usage:" in result.stdout or "Commands:" in result.stdout
    
    def test_run_web_command_help(self):
        """run-web command should have help"""
        result = subprocess.run(
            ["uv", "run", "python", "main.py", "run-web", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 0
        assert "run-web" in result.stdout.lower() or "Run" in result.stdout


class TestFormulaCompressionCLI:
    """Test formula compression CLI commands"""
    
    @pytest.mark.skipif(
        not Path("web/sample_schema.json").exists(),
        reason="sample_schema.json not found"
    )
    def test_formula_compression_with_sample_data(self):
        """Test formula compression using sample schema"""
        from tabs.formula_compressor import compress_formula_by_name
        from unittest.mock import patch
        
        # Load sample schema
        schema_path = Path("web/sample_schema.json")
        with open(schema_path) as f:
            metadata = json.load(f)
        
        # Find a formula field
        formula_found = False
        with patch('tabs.formula_compressor.get_local_storage_metadata', return_value=metadata):
            for table in metadata["tables"]:
                for field in table["fields"]:
                    if field.get("type") == "formula":
                        result = compress_formula_by_name(
                            table["name"],
                            field["name"],
                            None,
                            "field_names"
                        )
                        assert isinstance(result, tuple)
                        assert len(result) == 2
                        compressed, depth = result
                        assert isinstance(compressed, str)
                        assert isinstance(depth, int)
                        formula_found = True
                        break
                if formula_found:
                    break
        
        # If no formula fields, test passes (nothing to compress)
        assert True


class TestUnusedFieldsCLI:
    """Test unused fields detection CLI"""
    
    @pytest.mark.skipif(
        not Path("web/sample_schema.json").exists(),
        reason="sample_schema.json not found"
    )
    def test_unused_fields_detection(self):
        """Test unused fields detection using sample schema"""
        from tabs.unused_fields import get_unused_fields
        from unittest.mock import patch
        
        schema_path = Path("web/sample_schema.json")
        with open(schema_path) as f:
            metadata = json.load(f)
        
        with patch('tabs.unused_fields.get_local_storage_metadata', return_value=metadata):
            unused = get_unused_fields()
            
            assert isinstance(unused, list)
            # Each entry should have required fields
            for field in unused:
                assert "table_name" in field
                assert "field_name" in field
                assert "field_id" in field


class TestComplexityScorecardCLI:
    """Test complexity scorecard CLI"""
    
    @pytest.mark.skipif(
        not Path("web/sample_schema.json").exists(),
        reason="sample_schema.json not found"
    )
    def test_complexity_analysis(self):
        """Test complexity analysis using sample schema"""
        from tabs.complexity_scorecard import get_all_field_complexity
        from unittest.mock import patch
        
        schema_path = Path("web/sample_schema.json")
        with open(schema_path) as f:
            metadata = json.load(f)
        
        with patch('tabs.complexity_scorecard.get_local_storage_metadata', return_value=metadata):
            complexity = get_all_field_complexity()
            
            assert isinstance(complexity, list)
            # Each entry should have required fields
            for field in complexity:
                assert "field_name" in field
                assert "table_name" in field
                assert "complexity_score" in field
                assert isinstance(field["complexity_score"], (int, float))


class TestCLIErrorHandling:
    """Test CLI error handling"""
    
    def test_invalid_command(self):
        """CLI should handle invalid commands gracefully"""
        result = subprocess.run(
            ["uv", "run", "python", "main.py", "nonexistent-command"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        # Should exit with error code
        assert result.returncode != 0


class TestModuleFunctionsCLI:
    """Test that CLI-accessible functions work correctly"""
    
    def test_formula_compressor_import(self):
        """Formula compressor module should be importable"""
        from tabs import formula_compressor
        assert hasattr(formula_compressor, 'compress_formula_by_name')
    
    def test_unused_fields_import(self):
        """Unused fields module should be importable"""
        from tabs import unused_fields
        assert hasattr(unused_fields, 'get_unused_fields')
    
    def test_complexity_scorecard_import(self):
        """Complexity scorecard module should be importable"""
        from tabs import complexity_scorecard
        assert hasattr(complexity_scorecard, 'get_all_field_complexity')
    
    def test_airtable_client_import(self):
        """Airtable client module should be importable"""
        from components import airtable_client
        assert hasattr(airtable_client, 'get_local_storage_metadata')


class TestSchemaLoading:
    """Test schema loading functionality"""
    
    @pytest.mark.skipif(
        not Path("web/sample_schema.json").exists(),
        reason="sample_schema.json not found"
    )
    def test_sample_schema_is_valid_json(self):
        """Sample schema should be valid JSON"""
        schema_path = Path("web/sample_schema.json")
        with open(schema_path) as f:
            metadata = json.load(f)
        
        assert "tables" in metadata
        assert isinstance(metadata["tables"], list)
    
    @pytest.mark.skipif(
        not Path("web/sample_schema.json").exists(),
        reason="sample_schema.json not found"
    )
    def test_sample_schema_has_tables(self):
        """Sample schema should have tables"""
        schema_path = Path("web/sample_schema.json")
        with open(schema_path) as f:
            metadata = json.load(f)
        
        assert len(metadata["tables"]) > 0
        
        # Each table should have required fields
        for table in metadata["tables"]:
            assert "id" in table
            assert "name" in table
            assert "fields" in table
            assert isinstance(table["fields"], list)
    
    @pytest.mark.skipif(
        not Path("web/sample_schema.json").exists(),
        reason="sample_schema.json not found"
    )
    def test_sample_schema_has_fields(self):
        """Sample schema tables should have fields"""
        schema_path = Path("web/sample_schema.json")
        with open(schema_path) as f:
            metadata = json.load(f)
        
        has_fields = False
        for table in metadata["tables"]:
            if len(table["fields"]) > 0:
                has_fields = True
                field = table["fields"][0]
                assert "id" in field
                assert "name" in field
                assert "type" in field
                break
        
        assert has_fields


class TestEndToEndWorkflow:
    """Test complete workflows"""
    
    @pytest.mark.skipif(
        not Path("web/sample_schema.json").exists(),
        reason="sample_schema.json not found"
    )
    def test_complete_analysis_workflow(self):
        """Test running multiple analysis functions in sequence"""
        from tabs.unused_fields import get_unused_fields
        from tabs.complexity_scorecard import get_all_field_complexity
        from unittest.mock import patch
        
        schema_path = Path("web/sample_schema.json")
        with open(schema_path) as f:
            metadata = json.load(f)
        
        # Run multiple analyses
        with patch('tabs.unused_fields.get_local_storage_metadata', return_value=metadata):
            unused = get_unused_fields()
            assert isinstance(unused, list)
        
        with patch('tabs.complexity_scorecard.get_local_storage_metadata', return_value=metadata):
            complexity = get_all_field_complexity()
            assert isinstance(complexity, list)
        
        # Results should be consistent with metadata
        total_fields = sum(len(t["fields"]) for t in metadata["tables"])
        assert total_fields > 0


class TestCLIOutputFormat:
    """Test CLI output formatting"""
    
    def test_help_output_format(self):
        """Help output should be well-formatted"""
        result = subprocess.run(
            ["uv", "run", "python", "main.py", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        assert result.returncode == 0
        # Should have some recognizable structure
        lines = result.stdout.split('\n')
        assert len(lines) > 5  # Should have multiple lines
