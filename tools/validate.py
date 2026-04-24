#!/usr/bin/env python3
"""
Project validation script for Quizzer.

Runs focused checks that are safe to repeat locally:
- Python syntax compilation for repo modules
- Unit tests
- Optional config/database smoke checks if config.yaml exists
"""
import os
import py_compile
import sys
import unittest


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {'.git', '.venv', '__pycache__', '.cursor'}
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def iter_python_files():
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [directory for directory in dirs if directory not in SKIP_DIRS]
        for filename in files:
            if filename.endswith('.py'):
                yield os.path.join(root, filename)


def compile_python():
    print("== Python compile check ==")
    for path in iter_python_files():
        py_compile.compile(path, doraise=True)
    print("ok")


def run_tests():
    print("== Unit tests ==")
    loader = unittest.defaultTestLoader
    suite = loader.discover(os.path.join(REPO_ROOT, 'tests'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise RuntimeError("Unit tests failed")


def run_optional_smoke_checks():
    config_path = os.path.join(REPO_ROOT, 'config.yaml')
    if not os.path.exists(config_path):
        print("== Smoke checks ==")
        print("skipped (no config.yaml present)")
        return

    print("== Smoke checks ==")
    os.chdir(REPO_ROOT)
    from config import load_config, load_env_file
    from database import create_database

    load_env_file()
    load_config()
    create_database()
    print("ok")


def main():
    os.chdir(REPO_ROOT)
    compile_python()
    run_tests()
    run_optional_smoke_checks()
    print("All validation checks passed.")


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        sys.exit(1)
