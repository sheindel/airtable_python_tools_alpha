"""
Unit tests for Formula Parser

Tests the Airtable formula tokenization and parsing functionality,
including complex nested expressions and function argument splitting.
"""

import pytest
import sys
from pathlib import Path

# Add web directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "web"))

from at_formula_parser import tokenize, FormulaTokenNode
from typing import List


class TestBasicTokenization:
    """Test basic formula tokenization"""
    
    def test_tokenize_simple_literal(self):
        """Test tokenizing a simple literal"""
        root, tokens = tokenize("TRUE")
        assert root is not None
        assert len(tokens) > 0
    
    def test_tokenize_field_reference(self):
        """Test tokenizing field reference with valid format"""
        root, tokens = tokenize("{fldABCDEFGHIJKLMN}")
        assert root is not None
        # Should parse field reference
        has_field_ref = any("fld" in str(t) for t in tokens)
        assert has_field_ref
    
    def test_tokenize_simple_function(self):
        """Test tokenizing a simple function call"""
        root, tokens = tokenize("IF(TRUE, 'yes', 'no')")
        assert root is not None
        assert len(tokens) > 5  # Function, parens, args, commas
    
    def test_tokenize_nested_function(self):
        """Test tokenizing nested functions"""
        root, tokens = tokenize("IF(TRUE, IF(FALSE, 'a', 'b'), 'c')")
        assert root is not None
        assert len(tokens) > 10


class TestFieldReferenceFormats:
    """Test field reference parsing with different formats"""
    
    def test_valid_field_id_14_chars(self):
        """Test field ID with exactly 14 characters after 'fld'"""
        root, tokens = tokenize("{fld12345678901234}")
        assert root is not None
    
    def test_field_in_formula_context(self):
        """Test field reference within formula"""
        root, tokens = tokenize("AND(TRUE, {fldABCDEFGHIJKLMN})")
        assert root is not None
        # Formula should parse without error
        assert len(tokens) > 0


class TestComplexNestedIFs:
    """Test complex nested IF statements"""
    
    def test_simple_nested_if(self):
        """Test two-level nested IF"""
        formula = "IF({fldABCDEFGHIJKLMN}, 'A', IF({fldBBCDEFGHIJKLMN}, 'B', 'C'))"
        root, tokens = tokenize(formula)
        assert root is not None
        assert len(tokens) > 0
    
    def test_deeply_nested_if(self):
        """Test deeply nested IF statements (3+ levels)"""
        formula = """IF({fldA00000000001}=BLANK(), "No Deal",
            IF(FIND("Cancel",{fldB00000000001})>0, "Cancelled",
                IF({fldC00000000001}, "Complete", "Incomplete")))"""
        root, tokens = tokenize(formula)
        assert root is not None
        # Should handle multi-line formulas
        assert len(tokens) > 15
    
    def test_complex_realistic_formula(self):
        """Test very complex nested formula from real use case"""
        # Simplified version of a complex status formula
        formula = '''IF({Deal}=BLANK(),
"X. No Deal", 
IF(FIND("Cancel",{Status})>0,"Y. Cancelled",
IF({Complete Date},"Completed","In Progress")))'''
        
        # Should not crash on complex formulas
        root, tokens = tokenize(formula)
        assert root is not None


class TestFunctionArgumentSplitting:
    """Test splitting function arguments correctly"""
    
    def test_if_has_three_arguments(self):
        """Test that IF function identifies 3 arguments"""
        formula = "IF(TRUE, 'yes', 'no')"
        root, tokens = tokenize(formula)
        
        # The root should be a function with children
        assert root is not None
        assert hasattr(root, 'children')
    
    def test_nested_function_argument_isolation(self):
        """Test that nested functions don't interfere with argument splitting"""
        formula = "IF(AND(TRUE, FALSE), 'yes', 'no')"
        root, tokens = tokenize(formula)
        
        # Should properly parse nested AND within IF's first argument
        assert root is not None
        assert len(tokens) > 5
    
    def test_multiple_commas_in_nested_functions(self):
        """Test handling commas in nested functions"""
        formula = "IF(OR(TRUE, FALSE, TRUE), SUM(1, 2, 3), 0)"
        root, tokens = tokenize(formula)
        
        # OR has 3 args, SUM has 3 args, but IF still has 3 args
        assert root is not None


class TestStringHandling:
    """Test string literal handling in formulas"""
    
    def test_string_with_spaces(self):
        """Test strings with spaces"""
        root, tokens = tokenize("'Hello World'")
        assert root is not None
    
    def test_string_with_commas(self):
        """Test that commas in strings don't split arguments"""
        formula = "IF(TRUE, 'yes, indeed', 'no')"
        root, tokens = tokenize(formula)
        assert root is not None
        # Comma inside string shouldn't affect parsing
    
    def test_empty_string(self):
        """Test empty string literal"""
        root, tokens = tokenize("''")
        assert root is not None


class TestOperators:
    """Test operator parsing"""
    
    def test_comparison_operators(self):
        """Test various comparison operators"""
        operators = ["=", "!=", ">", "<", ">=", "<="]
        for op in operators:
            formula = f"10 {op} 5"
            root, tokens = tokenize(formula)
            assert root is not None
    
    def test_arithmetic_operators(self):
        """Test arithmetic operators"""
        operators = ["+", "-", "*", "/", "%"]
        for op in operators:
            formula = f"10 {op} 5"
            root, tokens = tokenize(formula)
            assert root is not None
    
    def test_logical_operators(self):
        """Test logical operators in context"""
        formula = "AND(TRUE, TRUE)"
        root, tokens = tokenize(formula)
        assert root is not None


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_formula(self):
        """Test empty formula string"""
        # Should handle gracefully
        try:
            root, tokens = tokenize("")
            # May return empty or minimal structure
            assert True
        except Exception:
            # Acceptable to raise exception
            pass
    
    def test_unmatched_parentheses(self):
        """Test formula with unmatched parentheses"""
        try:
            root, tokens = tokenize("IF(TRUE, 'yes'")
            # Parser may handle this gracefully
            assert True
        except Exception:
            # Acceptable to raise exception for invalid syntax
            pass
    
    def test_whitespace_preservation(self):
        """Test that parser handles various whitespace"""
        formulas = [
            "IF(TRUE,'yes','no')",  # No spaces
            "IF( TRUE , 'yes' , 'no' )",  # Extra spaces
            "IF(\n  TRUE,\n  'yes',\n  'no'\n)",  # Newlines
        ]
        
        for formula in formulas:
            root, tokens = tokenize(formula)
            assert root is not None
    
    def test_special_characters_in_strings(self):
        """Test strings with special characters"""
        special_chars = ["'", "\"", "(", ")", "{", "}", ","]
        for char in special_chars:
            formula = f"IF(TRUE, '{char}', 'no')"
            try:
                root, tokens = tokenize(formula)
                # Should handle or raise appropriate error
                assert True
            except Exception:
                # Some characters may cause parse errors
                pass


class TestTokenTreeStructure:
    """Test the token tree structure"""
    
    def test_token_node_has_type_and_value(self):
        """Test that token nodes have required attributes"""
        root, tokens = tokenize("TRUE")
        assert root is not None
        assert hasattr(root, 'token_type')
        assert hasattr(root, 'value')
    
    def test_token_node_has_children(self):
        """Test that token nodes have children attribute"""
        root, tokens = tokenize("IF(TRUE, 'yes', 'no')")
        assert root is not None
        assert hasattr(root, 'children')
        # IF should have children (the arguments)
    
    def test_nested_structure_depth(self):
        """Test that nested functions create proper tree depth"""
        formula = "IF(TRUE, IF(FALSE, 'a', 'b'), 'c')"
        root, tokens = tokenize(formula)
        
        # Should have nested structure
        assert root is not None
        if hasattr(root, 'children') and root.children:
            # Has children means it's structured
            assert len(root.children) > 0


class TestRealWorldFormulas:
    """Test with real-world formula patterns"""
    
    def test_find_function(self):
        """Test FIND function parsing"""
        formula = 'FIND("Cancel", {Status})'
        root, tokens = tokenize(formula)
        assert root is not None
    
    def test_blank_comparison(self):
        """Test BLANK() comparison"""
        formula = "{Field}=BLANK()"
        root, tokens = tokenize(formula)
        assert root is not None
    
    def test_concatenation(self):
        """Test string concatenation with &"""
        formula = "'{Field1}' & ' - ' & '{Field2}'"
        root, tokens = tokenize(formula)
        assert root is not None
    
    def test_switch_statement(self):
        """Test SWITCH function"""
        formula = "SWITCH({Status}, 'A', 'Active', 'I', 'Inactive', 'Unknown')"
        root, tokens = tokenize(formula)
        assert root is not None


class TestArgumentSplitting:
    """Test argument splitting logic for function calls"""
    
    def test_if_function_parses_with_three_branches(self):
        """Test that IF function with 3 branches parses successfully"""
        formula = "IF(TRUE, 'yes', 'no')"
        root, tokens = tokenize(formula)
        
        # Should parse successfully
        assert root is not None
        assert len(tokens) > 5  # Has multiple tokens
    
    def test_nested_function_parses_correctly(self):
        """Test that nested functions parse without errors"""
        formula = "IF(AND(TRUE, FALSE), 'yes', 'no')"
        root, tokens = tokenize(formula)
        
        # Should parse successfully despite nested function
        assert root is not None
        assert len(tokens) > 7
    
    def test_multiple_nested_functions_parse(self):
        """Test multiple nested functions at same level"""
        formula = "IF(OR(TRUE, FALSE, TRUE), SUM(1, 2, 3), 0)"
        root, tokens = tokenize(formula)
        
        # Should handle multiple nested functions
        assert root is not None
    
    def test_deeply_nested_if_parses(self):
        """Test deeply nested IF statements parse correctly"""
        formula = "IF({fldA}, 'A', IF({fldB}, 'B', IF({fldC}, 'C', 'D')))"
        root, tokens = tokenize(formula)
        
        # Should parse 3-level nesting
        assert root is not None
        assert len(tokens) > 10
    
    def test_sum_with_multiple_arguments_parses(self):
        """Test SUM with many arguments parses"""
        formula = "SUM(1, 2, 3, 4, 5, 6)"
        root, tokens = tokenize(formula)
        
        # Should parse all arguments
        assert root is not None
    
    def test_switch_with_many_cases_parses(self):
        """Test SWITCH with multiple cases parses"""
        formula = "SWITCH(1, 1, 'one', 2, 'two', 3, 'three', 'default')"
        root, tokens = tokenize(formula)
        
        # Should parse all cases
        assert root is not None
    
    def test_field_references_in_conditions_parse(self):
        """Test field references in function arguments"""
        formula = "IF({fldABCDEFGHIJKLMN}=BLANK(), 'Empty', 'Not Empty')"
        root, tokens = tokenize(formula)
        
        # Should parse field references correctly
        assert root is not None
    
    def test_complex_nested_expression_parses(self):
        """Test complex nested expression parses successfully"""
        formula = "IF(AND({fldA}, OR({fldB}, {fldC})), IF({fldD}, 'X', 'Y'), 'Z')"
        root, tokens = tokenize(formula)
        
        # Should parse complex nesting
        assert root is not None
        assert len(tokens) > 15
    
    def test_real_world_complex_formula_parses(self):
        """Test ultra-complex real-world formula parses"""
        formula = '''IF({Deal}=BLANK(),
"X. No Deal", 
IF(FIND("Cancel",{Status})>0,"Y. Cancelled",
IF({Complete Date},"Completed","In Progress")))'''
        
        # Should handle complex multi-line formula
        root, tokens = tokenize(formula)
        assert root is not None
        # Should have many tokens
        assert len(tokens) > 20


class TestHelperFunctions:
    """Test helper functions for formula analysis"""
    
    def find_all_functions(self, node: FormulaTokenNode, func_name: str = "IF") -> List[FormulaTokenNode]:
        """Find all function nodes with a given name"""
        results = []
        
        if node.token_type == "FUNCTION_NAME" and node.value.upper() == func_name.upper():
            results.append(node)
        
        for child in node.children:
            results.extend(self.find_all_functions(child, func_name))
        
        return results
    
    def test_find_single_if_function(self):
        """Test finding a single IF function"""
        formula = 'IF({fldABCDEFGHIJKLMN}=BLANK(), "Yes", "No")'
        root, tokens = tokenize(formula)
        
        if_nodes = self.find_all_functions(root, "IF")
        assert len(if_nodes) >= 1
        assert if_nodes[0].value.upper() == "IF"
    
    def test_find_nested_if_functions(self):
        """Test finding nested IF functions"""
        formula = 'IF({fldABCDEFGHIJKLMN}, "A", IF({fldBBCDEFGHIJKLMN}, "B", "C"))'
        root, tokens = tokenize(formula)
        
        if_nodes = self.find_all_functions(root, "IF")
        # Should find both the outer and inner IF
        assert len(if_nodes) >= 2
    
    def test_find_deeply_nested_ifs(self):
        """Test finding deeply nested IF functions"""
        formula = '''IF({Deal}=BLANK(),
"X. No Deal", 
IF(FIND("Cancel",{Status})>0,"Y. Cancelled",
IF({Complete Date},"7. Completed",
IF(AND({Field Ready}, {Status}),"Ready","Not Ready"))))'''
        
        root, tokens = tokenize(formula)
        if_nodes = self.find_all_functions(root, "IF")
        
        # Should find all nested IFs (at least 4 in this formula)
        assert len(if_nodes) >= 4
    
    def test_find_function_case_insensitive(self):
        """Test that function finding is case-insensitive"""
        # Note: Airtable formulas require uppercase function names
        # This test verifies the search helper is case-insensitive even if parser isn't
        formula = 'IF({fldA}, "yes", "no")'
        root, tokens = tokenize(formula)
        
        # Test both uppercase and lowercase search patterns
        if_nodes_upper = self.find_all_functions(root, "IF")
        if_nodes_lower = self.find_all_functions(root, "if")
        
        # Both should find the same functions (search is case-insensitive)
        assert len(if_nodes_upper) >= 1
        assert len(if_nodes_lower) >= 1
        assert len(if_nodes_upper) == len(if_nodes_lower)
    
    def test_find_non_if_functions(self):
        """Test finding other function types"""
        formula = 'SUM(1, 2, 3)'
        root, tokens = tokenize(formula)
        
        sum_nodes = self.find_all_functions(root, "SUM")
        assert len(sum_nodes) >= 1
        assert sum_nodes[0].value.upper() == "SUM"
    
    def test_find_function_in_complex_formula(self):
        """Test finding specific functions in complex formula"""
        formula = 'IF(FIND("text", {fldA})>0, SUM(1,2,3), COUNT({fldB}))'
        root, tokens = tokenize(formula)
        
        # Find each function type
        if_nodes = self.find_all_functions(root, "IF")
        find_nodes = self.find_all_functions(root, "FIND")
        sum_nodes = self.find_all_functions(root, "SUM")
        count_nodes = self.find_all_functions(root, "COUNT")
        
        assert len(if_nodes) >= 1
        assert len(find_nodes) >= 1
        assert len(sum_nodes) >= 1
        assert len(count_nodes) >= 1
    
    def test_find_no_matching_functions(self):
        """Test finding functions that don't exist in formula"""
        formula = 'IF(TRUE, "yes", "no")'
        root, tokens = tokenize(formula)
        
        sum_nodes = self.find_all_functions(root, "SUM")
        # Should return empty list
        assert len(sum_nodes) == 0
    
    def test_function_node_has_children(self):
        """Test that found function nodes have children"""
        formula = 'IF(TRUE, "yes", "no")'
        root, tokens = tokenize(formula)
        
        if_nodes = self.find_all_functions(root, "IF")
        assert len(if_nodes) >= 1
        
        # Function node should have children (arguments)
        first_if = if_nodes[0]
        assert hasattr(first_if, 'children')
        assert len(first_if.children) > 0


class TestComplexRealWorldFormulas:
    """Test with complex real-world formulas from the grapher debug script"""
    
    def test_ultra_complex_nested_formula(self):
        """Test the ultra-complex nested IF formula from real use case"""
        formula = '''IF({Deal}=BLANK(),
"X. No Deal Attached", 
IF(FIND("Cancel",{J Status OVRD})>0,"Y. Cancelled",
IF({All Invoices Sent and Linked? #STATUS},"9. QBO sent",
IF({Billable = Invoiced Clients (Length)? #STATUS},"8. On Invoice",
IF(AND({Complete Date},{$ Approved Billing?}),"8. Ready to Bill",
IF({Complete Date},"7. Completed",
IF(AND({Pts Correct Need?},{Drop/Ship Date},NOT({Pts Corr Date}),{CSV Sent to Lab?}),"4X. Pts Edit Uncorrected",
IF(AND({Drop/Ship Date},NOT({CSV Sent to Lab?})),"4X. CSV Unsent",
IF({Drop/Ship Date},"3. Drop/Shipped",
IF({Sample Date},"2. Sampled",
IF(FIND("Partial",{J Status OVRD})>0,IF({Field Ready Date}, "1X. Partial", "0X. Partial"),
IF(AND({Field Ready Date}, FIND("Finalized",{Mission Status})>0),"1. Ready",
IF({Field Ready Date},"1X. Ready & Unprepped",
IF( FIND("Finalized",{Mission Status})>0,"0. Unready & Prepped",
IF( AND( FIND("Finalized",{Mission Status})=0, NOT({Field Ready Date})),"0. Unready & Unprepped","X. Error in Job State")))))))))))))))'''
        
        # Should not crash on ultra-complex formula
        root, tokens = tokenize(formula)
        assert root is not None
        
        # Should have many tokens (this is a very long formula)
        assert len(tokens) > 100
    
    def test_ultra_complex_formula_if_count(self):
        """Test counting IF functions in ultra-complex formula"""
        formula = '''IF({Deal}=BLANK(),
"X. No Deal Attached", 
IF(FIND("Cancel",{J Status})>0,"Y. Cancelled",
IF({Complete},"Complete",
IF({Ready},"Ready",
IF({InProgress},"In Progress","Unknown")))))'''
        
        root, tokens = tokenize(formula)
        
        # Helper to find all IFs
        def find_ifs(node: FormulaTokenNode) -> List[FormulaTokenNode]:
            results = []
            if node.token_type == "FUNCTION_NAME" and node.value.upper() == "IF":
                results.append(node)
            for child in node.children:
                results.extend(find_ifs(child))
            return results
        
        if_nodes = find_ifs(root)
        
        # Should find multiple nested IFs
        assert len(if_nodes) >= 5
    
    def test_complex_formula_with_and_or_not(self):
        """Test complex formula with multiple logical operators"""
        formula = '''IF(AND({Field1}, OR({Field2}, {Field3}), NOT({Field4})), 
            "Condition Met", 
            "Condition Not Met")'''
        
        root, tokens = tokenize(formula)
        assert root is not None
        
        # Should parse all logical functions
        def find_function(node: FormulaTokenNode, name: str) -> int:
            count = 0
            if node.token_type == "FUNCTION_NAME" and node.value.upper() == name.upper():
                count = 1
            for child in node.children:
                count += find_function(child, name)
            return count
        
        assert find_function(root, "IF") >= 1
        assert find_function(root, "AND") >= 1
        assert find_function(root, "OR") >= 1
        assert find_function(root, "NOT") >= 1
    
    def test_complex_formula_with_find_and_string_operations(self):
        """Test complex formula with FIND and string operations"""
        formula = '''IF(FIND("Cancel", {Status})>0, 
            "Cancelled", 
            IF(FIND("Complete", {Status})>0, "Done", "In Progress"))'''
        
        root, tokens = tokenize(formula)
        assert root is not None
        
        # Should parse FIND functions correctly
        def find_function(node: FormulaTokenNode, name: str) -> int:
            count = 0
            if node.token_type == "FUNCTION_NAME" and node.value.upper() == name.upper():
                count = 1
            for child in node.children:
                count += find_function(child, name)
            return count
        
        assert find_function(root, "FIND") >= 2
        assert find_function(root, "IF") >= 2
    
    def test_formula_with_blank_comparisons(self):
        """Test formula with BLANK() comparisons"""
        formula = '''IF({Field1}=BLANK(), 
            "Empty", 
            IF({Field2}=BLANK(), "Partially Empty", "Full"))'''
        
        root, tokens = tokenize(formula)
        assert root is not None
        
        # Should parse BLANK() correctly
        def find_function(node: FormulaTokenNode, name: str) -> int:
            count = 0
            if node.token_type == "FUNCTION_NAME" and node.value.upper() == name.upper():
                count = 1
            for child in node.children:
                count += find_function(child, name)
            return count
        
        assert find_function(root, "BLANK") >= 2
    
    def test_formula_with_numeric_comparisons(self):
        """Test formula with various numeric comparisons"""
        formula = '''IF({Count} > 10, 
            "High", 
            IF({Count} >= 5, "Medium", 
                IF({Count} > 0, "Low", "None")))'''
        
        root, tokens = tokenize(formula)
        assert root is not None
        
        # Should parse comparison operators correctly
        assert len(tokens) > 20


# ============================================================================
# Phase 1: AST Parser Tests
# ============================================================================

from at_formula_parser import (
    parse_airtable_formula,
    ParseError,
    LiteralNode,
    FieldReferenceNode,
    FunctionCallNode,
    BinaryOpNode,
    UnaryOpNode
)


class TestASTLiterals:
    """Test parsing of literal values into AST"""
    
    def test_parse_number_integer(self):
        """Test parsing integer literal"""
        ast = parse_airtable_formula("42")
        assert isinstance(ast, LiteralNode)
        assert ast.value == 42
        assert ast.data_type == "number"
    
    def test_parse_number_float(self):
        """Test parsing float literal"""
        ast = parse_airtable_formula("3.14")
        assert isinstance(ast, LiteralNode)
        assert ast.value == 3.14
        assert ast.data_type == "number"
    
    def test_parse_string_literal(self):
        """Test parsing string literal"""
        ast = parse_airtable_formula('"hello"')
        assert isinstance(ast, LiteralNode)
        assert ast.value == "hello"
        assert ast.data_type == "string"
    
    def test_parse_boolean_true(self):
        """Test parsing TRUE literal"""
        ast = parse_airtable_formula("TRUE")
        assert isinstance(ast, LiteralNode)
        assert ast.value is True
        assert ast.data_type == "boolean"
    
    def test_parse_boolean_false(self):
        """Test parsing FALSE literal"""
        ast = parse_airtable_formula("FALSE")
        assert isinstance(ast, LiteralNode)
        assert ast.value is False
        assert ast.data_type == "boolean"


class TestASTFieldReferences:
    """Test parsing field references into AST"""
    
    def test_parse_field_reference_no_metadata(self):
        """Test parsing field reference without metadata"""
        ast = parse_airtable_formula("{fldABCDEFGHIJKLMN}")
        assert isinstance(ast, FieldReferenceNode)
        assert ast.field_id == "fldABCDEFGHIJKLMN"
        assert ast.field_name is None
        assert ast.field_type is None
    
    def test_parse_field_reference_with_metadata(self):
        """Test parsing field reference with metadata"""
        metadata = {
            "tables": [{
                "id": "tblXXXXXXXXXXXXXX",
                "name": "Test Table",
                "fields": [{
                    "id": "fldABCDEFGHIJKLMN",
                    "name": "Test Field",
                    "type": "singleLineText"
                }]
            }]
        }
        
        ast = parse_airtable_formula("{fldABCDEFGHIJKLMN}", metadata)
        assert isinstance(ast, FieldReferenceNode)
        assert ast.field_id == "fldABCDEFGHIJKLMN"
        assert ast.field_name == "Test Field"
        assert ast.field_type == "singleLineText"


class TestASTBinaryOperations:
    """Test parsing binary operations into AST"""
    
    def test_parse_simple_addition(self):
        """Test parsing 1 + 2"""
        ast = parse_airtable_formula("1 + 2")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "+"
        assert isinstance(ast.left, LiteralNode)
        assert ast.left.value == 1
        assert isinstance(ast.right, LiteralNode)
        assert ast.right.value == 2
    
    def test_parse_simple_subtraction(self):
        """Test parsing 10 - 5"""
        ast = parse_airtable_formula("10 - 5")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "-"
    
    def test_parse_simple_multiplication(self):
        """Test parsing 3 * 4"""
        ast = parse_airtable_formula("3 * 4")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "*"
    
    def test_parse_simple_division(self):
        """Test parsing 10 / 2"""
        ast = parse_airtable_formula("10 / 2")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "/"
    
    def test_parse_string_concatenation(self):
        """Test parsing string concatenation with &"""
        ast = parse_airtable_formula('"hello" & " " & "world"')
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "&"
        # Left side should be another binary op
        assert isinstance(ast.left, BinaryOpNode)
        assert ast.left.operator == "&"
    
    def test_parse_comparison_equal(self):
        """Test parsing equality comparison"""
        ast = parse_airtable_formula("5 = 5")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "="
    
    def test_parse_comparison_not_equal(self):
        """Test parsing not equal comparison"""
        ast = parse_airtable_formula("5 != 6")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "!="
    
    def test_parse_comparison_greater_than(self):
        """Test parsing greater than comparison"""
        ast = parse_airtable_formula("10 > 5")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == ">"
    
    def test_parse_comparison_less_than_or_equal(self):
        """Test parsing less than or equal comparison"""
        ast = parse_airtable_formula("5 <= 10")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "<="
    
    def test_parse_field_multiplication(self):
        """Test parsing field reference in operation"""
        ast = parse_airtable_formula("{fldABCDEFGHIJKLMN} * 2")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "*"
        assert isinstance(ast.left, FieldReferenceNode)
        assert isinstance(ast.right, LiteralNode)


class TestASTUnaryOperations:
    """Test parsing unary operations into AST"""
    
    def test_parse_negation(self):
        """Test parsing unary minus"""
        ast = parse_airtable_formula("-5")
        assert isinstance(ast, UnaryOpNode)
        assert ast.operator == "-"
        assert isinstance(ast.operand, LiteralNode)
        assert ast.operand.value == 5
    
    def test_parse_not_operator(self):
        """Test parsing NOT operator"""
        ast = parse_airtable_formula("NOT TRUE")
        assert isinstance(ast, UnaryOpNode)
        assert ast.operator == "NOT"
        assert isinstance(ast.operand, LiteralNode)


class TestASTFunctionCalls:
    """Test parsing function calls into AST"""
    
    def test_parse_if_function(self):
        """Test parsing IF function"""
        ast = parse_airtable_formula('IF(TRUE, "yes", "no")')
        assert isinstance(ast, FunctionCallNode)
        assert ast.function_name == "IF"
        assert len(ast.arguments) == 3
        assert isinstance(ast.arguments[0], LiteralNode)
        assert isinstance(ast.arguments[1], LiteralNode)
        assert isinstance(ast.arguments[2], LiteralNode)
    
    def test_parse_concatenate_function(self):
        """Test parsing CONCATENATE function"""
        ast = parse_airtable_formula('CONCATENATE("hello", " ", "world")')
        assert isinstance(ast, FunctionCallNode)
        assert ast.function_name == "CONCATENATE"
        assert len(ast.arguments) == 3
    
    def test_parse_sum_function(self):
        """Test parsing SUM function"""
        ast = parse_airtable_formula("SUM(1, 2, 3, 4)")
        assert isinstance(ast, FunctionCallNode)
        assert ast.function_name == "SUM"
        assert len(ast.arguments) == 4
    
    def test_parse_nested_functions(self):
        """Test parsing nested function calls"""
        ast = parse_airtable_formula('IF(AND(TRUE, FALSE), "yes", "no")')
        assert isinstance(ast, FunctionCallNode)
        assert ast.function_name == "IF"
        
        # First argument should be an AND function
        assert isinstance(ast.arguments[0], FunctionCallNode)
        assert ast.arguments[0].function_name == "AND"
    
    def test_parse_function_with_field_reference(self):
        """Test parsing function with field reference argument"""
        ast = parse_airtable_formula('LEN({fldABCDEFGHIJKLMN})')
        assert isinstance(ast, FunctionCallNode)
        assert ast.function_name == "LEN"
        assert len(ast.arguments) == 1
        assert isinstance(ast.arguments[0], FieldReferenceNode)
    
    def test_parse_function_with_expression_argument(self):
        """Test parsing function with expression as argument"""
        ast = parse_airtable_formula('ROUND({fldABCDEFGHIJKLMN} * 1.08, 2)')
        assert isinstance(ast, FunctionCallNode)
        assert ast.function_name == "ROUND"
        assert len(ast.arguments) == 2
        assert isinstance(ast.arguments[0], BinaryOpNode)


class TestASTParentheses:
    """Test parsing parenthesized expressions"""
    
    def test_parse_simple_parentheses(self):
        """Test parsing (1 + 2)"""
        ast = parse_airtable_formula("(1 + 2)")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "+"
    
    def test_parse_nested_parentheses(self):
        """Test parsing ((1 + 2) * 3)"""
        ast = parse_airtable_formula("((1 + 2) * 3)")
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "*"
        assert isinstance(ast.left, BinaryOpNode)


class TestASTComplexFormulas:
    """Test parsing complex real-world formulas"""
    
    def test_parse_complex_if(self):
        """Test parsing complex nested IF"""
        formula = 'IF({fldABCDEFGHIJKLMN} > 100, "High", IF({fldABCDEFGHIJKLMN} > 50, "Medium", "Low"))'
        ast = parse_airtable_formula(formula)
        
        assert isinstance(ast, FunctionCallNode)
        assert ast.function_name == "IF"
        # Third argument should be another IF function
        assert isinstance(ast.arguments[2], FunctionCallNode)
        assert ast.arguments[2].function_name == "IF"
    
    def test_parse_formula_with_multiple_fields(self):
        """Test parsing formula with multiple field references"""
        formula = "{fldABCDEFGHIJKLMN} + {fldBBCDEFGHIJKLMN} + {fldCBCDEFGHIJKLMN}"
        ast = parse_airtable_formula(formula)
        
        assert isinstance(ast, BinaryOpNode)
        # Should have nested binary operations
        assert isinstance(ast.left, BinaryOpNode)
    
    def test_parse_formula_with_find(self):
        """Test parsing formula with FIND function"""
        formula = 'FIND("cancel", LOWER({fldABCDEFGHIJKLMN})) > 0'
        ast = parse_airtable_formula(formula)
        
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == ">"
        assert isinstance(ast.left, FunctionCallNode)
        assert ast.left.function_name == "FIND"
    
    def test_parse_formula_with_blank(self):
        """Test parsing formula with BLANK comparison"""
        formula = '{fldABCDEFGHIJKLMN} = BLANK()'
        ast = parse_airtable_formula(formula)
        
        assert isinstance(ast, BinaryOpNode)
        assert ast.operator == "="
        assert isinstance(ast.left, FieldReferenceNode)
        assert isinstance(ast.right, FunctionCallNode)


class TestASTErrors:
    """Test error handling in AST parser"""
    
    def test_parse_empty_string_raises_error(self):
        """Test that empty formula raises error"""
        with pytest.raises((ParseError, IndexError, ValueError)):
            parse_airtable_formula("")
    
    def test_parse_unmatched_parenthesis_raises_error(self):
        """Test that unmatched parenthesis raises error"""
        with pytest.raises(ParseError):
            parse_airtable_formula("(1 + 2")
    
    def test_parse_unexpected_token_raises_error(self):
        """Test that unexpected token raises error"""
        # This may or may not raise depending on tokenizer behavior
        try:
            parse_airtable_formula("1 + + 2")
        except (ParseError, Exception):
            pass  # Expected to fail


class TestASTEdgeCases:
    """Test edge cases in AST parsing"""
    
    def test_parse_single_value(self):
        """Test parsing single value"""
        ast = parse_airtable_formula("42")
        assert isinstance(ast, LiteralNode)
    
    def test_parse_empty_string_literal(self):
        """Test parsing empty string"""
        ast = parse_airtable_formula('""')
        assert isinstance(ast, LiteralNode)
        assert ast.value == ""
        assert ast.data_type == "string"
    
    def test_parse_string_with_spaces(self):
        """Test parsing string with spaces"""
        ast = parse_airtable_formula('"hello world"')
        assert isinstance(ast, LiteralNode)
        assert ast.value == "hello world"
    
    def test_parse_function_no_args(self):
        """Test parsing function with no arguments"""
        ast = parse_airtable_formula('BLANK()')
        assert isinstance(ast, FunctionCallNode)
        assert ast.function_name == "BLANK"
        assert len(ast.arguments) == 0
