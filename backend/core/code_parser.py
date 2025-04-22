# backend/core/code_parser.py

import ast
from typing import List # <--- Added this import

def parse_python_code(code: str):
    """
    Parses Python code using the ast module.
    Returns the AST tree or None if parsing fails.
    """
    try:
        tree = ast.parse(code)
        return tree
    except SyntaxError as e:
        print(f"Syntax Error during parsing: {e}")
        return None

# Line 15 where the error occurred now has 'List' defined
def get_function_definitions(tree: ast.AST) -> List[str]:
    """Extracts function definition names from an AST tree."""
    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append(node.name)
    return functions

# Add more functions as needed, e.g., to get specific node details
# for line-by-line mapping (more complex)