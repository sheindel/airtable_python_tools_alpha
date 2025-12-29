#!/usr/bin/env python3
"""Generate PyScript configuration file from web directory structure.

This script automatically discovers Python files in the web/ directory
and generates the [files] section of pyscript.toml, eliminating the need
for manual maintenance.

Usage:
    python scripts/generate_pyscript_config.py
"""
import tomllib
import tomli_w
from pathlib import Path


def generate_files_mapping(web_dir: Path) -> dict[str, str]:
    """
    Generate file mappings for PyScript configuration.
    
    Args:
        web_dir: Path to the web directory
        
    Returns:
        Dictionary mapping source paths to target paths for PyScript
    """
    files = {}
    
    # Find all Python files except main.py (which is the entry point)
    for py_file in web_dir.rglob("*.py"):
        if py_file.name == "main.py" and py_file.parent == web_dir:
            continue  # Skip main entry point
        
        # Calculate relative path from web directory
        rel_path = py_file.relative_to(web_dir)
        
        # PyScript expects ./ prefix for source files
        source_path = f"./{rel_path}"
        target_path = str(rel_path)
        
        files[source_path] = target_path
    
    return files


def update_pyscript_config(config_path: Path, files_mapping: dict[str, str]) -> None:
    """
    Update pyscript.toml with new file mappings.
    
    Args:
        config_path: Path to pyscript.toml
        files_mapping: Dictionary of file mappings to add
    """
    # Read existing config
    with open(config_path, "rb") as f:
        config = tomllib.load(f)
    
    # Update files section
    config["files"] = files_mapping
    
    # Write back
    with open(config_path, "wb") as f:
        tomli_w.dump(config, f)


def main():
    """Main entry point."""
    # Get paths
    project_root = Path(__file__).parent.parent
    web_dir = project_root / "web"
    config_path = web_dir / "pyscript.toml"
    
    if not web_dir.exists():
        print(f"Error: web directory not found at {web_dir}")
        return 1
    
    if not config_path.exists():
        print(f"Error: pyscript.toml not found at {config_path}")
        return 1
    
    # Generate file mappings
    files = generate_files_mapping(web_dir)
    
    # Sort for consistent output
    files = dict(sorted(files.items()))
    
    print(f"Found {len(files)} Python files to include in PyScript config")
    print("\nFiles:")
    for src, dst in files.items():
        print(f"  {src} -> {dst}")
    
    # Update config
    update_pyscript_config(config_path, files)
    print(f"\n✓ Updated {config_path}")
    
    return 0


if __name__ == "__main__":
    exit(main())
