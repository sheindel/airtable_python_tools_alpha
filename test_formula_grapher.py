#!/usr/bin/env python3
"""Test script for debugging formula grapher parsing"""

import sys
sys.path.insert(0, 'web')

from at_formula_parser import tokenize, FormulaTokenNode
from typing import List, Optional


def print_token_tree(node: FormulaTokenNode, indent: int = 0):
    """Print the token tree structure"""
    prefix = "  " * indent
    children_count = len(node.children)
    print(f"{prefix}{node.token_type}: '{node.value}' ({children_count} children)")
    for child in node.children:
        print_token_tree(child, indent + 1)


def split_arguments(children: List[FormulaTokenNode]) -> List[List[FormulaTokenNode]]:
    """Split function children into argument groups by top-level commas.
    
    The key insight is that function calls have their opening paren as a child,
    so we need to count those to know when a closing paren belongs to a nested
    function vs being a top-level paren.
    """
    args: List[List[FormulaTokenNode]] = []
    current_arg: List[FormulaTokenNode] = []
    paren_depth = 0
    
    # The children include the opening ( and closing ) of the function itself
    # We need to skip those - find the actual content
    start_idx = 0
    end_idx = len(children)
    
    # Skip the function's opening paren
    if children and children[0].token_type == "OPERATOR" and children[0].value == "(":
        start_idx = 1
    
    # Skip the function's closing paren - but we DON'T decrement end_idx 
    # because the closing paren might be mixed in with other tokens
    # Instead, we'll handle it by stopping when depth goes negative
    
    print(f"  Processing children[{start_idx}:{end_idx}]")
    
    for i in range(start_idx, end_idx):
        child = children[i]
        
        if child.token_type == "WHITESPACE":
            continue
        
        # Track if this is a function that has its own paren
        # Functions have their opening paren as a child
        if child.token_type == "FUNCTION_NAME" and child.children:
            # Check if first child is an opening paren
            has_paren = any(c.token_type == "OPERATOR" and c.value == "(" for c in child.children)
            if has_paren:
                # This function "owns" the next closing paren we see
                paren_depth += 1
                print(f"    [{i}] FUNCTION '{child.value}' with paren -> depth={paren_depth}")
                current_arg.append(child)
                continue
        
        if child.token_type == "OPERATOR":
            if child.value == "(":
                # This is an orphan open paren (not attached to a function)
                paren_depth += 1
                current_arg.append(child)
                print(f"    [{i}] ORPHAN OPEN PAREN -> depth={paren_depth}")
            elif child.value == ")":
                if paren_depth > 0:
                    paren_depth -= 1
                    current_arg.append(child)
                    print(f"    [{i}] CLOSE PAREN (nested) -> depth={paren_depth}")
                else:
                    # This is the closing paren of the function we're analyzing
                    print(f"    [{i}] CLOSE PAREN (function end) -> stopping")
                    break
            elif child.value == "," and paren_depth == 0:
                print(f"    [{i}] COMMA at depth 0 -> split! arg has {len(current_arg)} tokens")
                if current_arg:
                    args.append(current_arg)
                current_arg = []
            else:
                current_arg.append(child)
                print(f"    [{i}] OPERATOR '{child.value}' -> added to current arg")
        else:
            current_arg.append(child)
            print(f"    [{i}] {child.token_type} '{child.value}' -> added to current arg")
    
    # Add the last argument
    if current_arg:
        print(f"    Final arg has {len(current_arg)} tokens")
        args.append(current_arg)
    
    return args


def print_arguments(args: List[List[FormulaTokenNode]]):
    """Print the split arguments"""
    for i, arg in enumerate(args):
        tokens_str = " | ".join([f"{t.token_type}:'{t.value}'" for t in arg])
        print(f"  Arg {i}: [{tokens_str}]")


def analyze_if_function(node: FormulaTokenNode, depth: int = 0):
    """Recursively analyze IF functions"""
    indent = "  " * depth
    
    if node.token_type != "FUNCTION_NAME" or node.value.upper() != "IF":
        return
    
    print(f"\n{indent}=== IF Function (depth {depth}) ===")
    print(f"{indent}Children count: {len(node.children)}")
    
    # Print all children
    print(f"{indent}Children:")
    for i, child in enumerate(node.children):
        print(f"{indent}  [{i}] {child.token_type}: '{child.value}' ({len(child.children)} children)")
    
    # Split arguments
    print(f"\n{indent}Splitting arguments:")
    args = split_arguments(node.children)
    
    print(f"\n{indent}Result: {len(args)} arguments")
    print_arguments(args)
    
    # Recursively analyze nested IFs
    for i, arg in enumerate(args):
        for token in arg:
            if token.token_type == "FUNCTION_NAME" and token.value.upper() == "IF":
                print(f"\n{indent}>>> Found nested IF in arg {i}")
                analyze_if_function(token, depth + 1)


def find_all_functions(node: FormulaTokenNode, func_name: str = "IF") -> List[FormulaTokenNode]:
    """Find all function nodes with a given name"""
    results = []
    
    if node.token_type == "FUNCTION_NAME" and node.value.upper() == func_name.upper():
        results.append(node)
    
    for child in node.children:
        results.extend(find_all_functions(child, func_name))
    
    return results


# Test formulas
test_formulas = [
    # Simple IF - use valid field ID format
    'IF({fldABCDEFGHIJKLMN}=BLANK(), "Yes", "No")',
    
    # Nested IF - use valid field ID format
    'IF({fldABCDEFGHIJKLMN}, "A", IF({fldBBCDEFGHIJKLMN}, "B", "C"))',
    
    # Complex nested IF (the problematic one) - keep original to test
    '''IF({Deal}=BLANK(),
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
IF( AND( FIND("Finalized",{Mission Status})=0, NOT({Field Ready Date})),"0. Unready & Unprepped","X. Error in Job State")))))))))))))))''',
]


def main():
    print("=" * 60)
    print("FORMULA PARSER DEBUG")
    print("=" * 60)
    
    # Only test the first two formulas for detailed analysis
    for i, formula in enumerate(test_formulas[:2]):
        print(f"\n\n{'#' * 60}")
        print(f"# TEST {i + 1}")
        print(f"{'#' * 60}")
        print(f"\nFormula:\n{formula[:200]}{'...' if len(formula) > 200 else ''}\n")
        
        # Parse the formula
        root_node, tokens = tokenize(formula)
        
        print("-" * 40)
        print("TOKEN TREE:")
        print("-" * 40)
        print_token_tree(root_node)
        
        # Find and analyze all IF functions
        if_nodes = find_all_functions(root_node, "IF")
        print(f"\n\nFound {len(if_nodes)} IF function(s)")
        
        if if_nodes:
            print("\n" + "-" * 40)
            print("ANALYZING TOP-LEVEL IF:")
            print("-" * 40)
            analyze_if_function(if_nodes[0])
    
    # For the complex formula, just show a summary
    print(f"\n\n{'#' * 60}")
    print("# TEST 3 (Complex nested IF) - Summary")
    print(f"{'#' * 60}")
    
    root_node, tokens = tokenize(test_formulas[2])
    if_nodes = find_all_functions(root_node, "IF")
    print(f"\nFound {len(if_nodes)} IF function(s) in complex formula")
    
    # Just analyze the top-level IF briefly
    if if_nodes:
        top_if = if_nodes[0]
        args = split_arguments(top_if.children)
        print(f"\nTop-level IF has {len(args)} arguments:")
        for j, arg in enumerate(args):
            tokens_str = " | ".join([f"{t.token_type[:4]}:'{t.value[:15]}'" for t in arg[:3]])
            if len(arg) > 3:
                tokens_str += f" ... ({len(arg)} total)"
            print(f"  Arg {j}: [{tokens_str}]")


if __name__ == "__main__":
    main()
