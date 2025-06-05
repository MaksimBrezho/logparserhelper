import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gui.code_generator_dialog import CodeGeneratorDialog


def test_find_example():
    dlg = CodeGeneratorDialog.__new__(CodeGeneratorDialog)
    dlg.logs = ["user=john", "error 42"]
    assert dlg._find_example(r"user=\w+") == "user=john"
    assert dlg._find_example(r"error") == "error"
