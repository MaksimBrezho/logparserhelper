import os
import sys
from importlib.machinery import SourceFileLoader

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.code_generator import generate_files


def test_generate_files_and_converter(tmp_path):
    header = {
        'CEF Version': '0',
        'Device Vendor': 'ACME',
        'Device Product': 'LP',
        'Device Version': '1.0',
        'Event Class ID': '42',
        'Event Name': 'Test',
        'Severity (int)': '5',
    }
    patterns = [{
        'name': 'UserName',
        'regex': r'user=(\w+)',
    }]
    mappings = [{
        'cef': 'suser',
        'pattern': 'UserName',
        'group': 1,
        'transform': 'upper',
    }]

    paths = generate_files(header, mappings, patterns, tmp_path)
    conv_path = os.path.join(tmp_path, 'cef_converter.py')
    assert conv_path in paths

    loader = SourceFileLoader('cef_converter', conv_path)
    module = loader.load_module()
    conv = module.LogToCEFConverter()
    result = conv.convert_line('user=john')
    assert 'ACME' in result and 'JOHN' in result

