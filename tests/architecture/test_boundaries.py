import ast
import os
from pathlib import Path

def get_imports(filepath: Path) -> set[str]:
    """Parses a Python file and returns all imported module names."""
    imports = set()
    try:
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    imports.add(name.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    # Resolve relative imports somewhat naively if possible
                    # but for this project we use absolute imports mostly (e.g. devclean.domain...)
                    imports.add(node.module)
    except SyntaxError:
        pass # Ignore malformed files if any
    return imports

def check_directory_imports(directory: Path, forbidden_prefixes: tuple[str, ...]) -> list[str]:
    violations = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                filepath = Path(root) / file
                imported_modules = get_imports(filepath)
                
                for module in imported_modules:
                    for forbidden in forbidden_prefixes:
                        if module.startswith(forbidden):
                            violations.append(f"{filepath} illegally imports {module}")
    return violations

def test_domain_boundary():
    """Domain layer must not depend on application, infrastructure, or presentation layers."""
    src_dir = Path("src/devclean/domain")
    if not src_dir.exists():
        return # Skip if run from wrong dir
        
    forbidden = (
        "devclean.application",
        "devclean.infrastructure",
        "devclean.presentation",
    )
    violations = check_directory_imports(src_dir, forbidden)
    
    assert not violations, f"Domain boundary violations found:\n" + "\n".join(violations)

def test_application_boundary():
    """Application layer must not depend on infrastructure or presentation layers."""
    src_dir = Path("src/devclean/application")
    if not src_dir.exists():
        return
        
    forbidden = (
        "devclean.infrastructure",
        "devclean.presentation",
    )
    violations = check_directory_imports(src_dir, forbidden)
    
    assert not violations, f"Application boundary violations found:\n" + "\n".join(violations)
