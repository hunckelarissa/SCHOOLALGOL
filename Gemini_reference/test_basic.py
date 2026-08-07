"""Обратная совместимость: python -m pytest test_basic.py"""
import pytest
import sys

if __name__ == "__main__":
    sys.exit(pytest.main(["tests", "-v"]))
