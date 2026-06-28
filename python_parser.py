import ast
import os


class PythonParser:
    def parse(self, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_text = f.read()
            
            tree = ast.parse(original_text)
            
            imports = []
            classes = []
            functions = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ''
                    imports.append(module)
                
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                
                elif isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
            
            return {
                "text": original_text,
                "structured_data": {
                    "imports": imports,
                    "classes": classes,
                    "functions": functions
                },
                "character_count": len(original_text),
                "extension": ".py"
            }
        
        except Exception:
            return None