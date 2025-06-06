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


def test_generate_files_constant_value(tmp_path):
    header = {'CEF Version': '0'}
    patterns = []
    mappings = [{
        'cef': 'deviceVendor',
        'value': 'ACME',
        'transform': 'none',
    }]

    paths = generate_files(header, mappings, patterns, tmp_path)
    loader = SourceFileLoader('cef_converter', paths[0])
    module = loader.load_module()
    conv = module.LogToCEFConverter()
    result = conv.convert_line('line')
    assert 'deviceVendor=ACME' in result


def test_generate_files_advanced(tmp_path):
    header = {
        'CEF Version': '0',
        'Device Vendor': 'ACME',
        'Device Product': 'LP',
        'Device Version': '1.0',
        'Event Class ID': '42',
        'Event Name': 'Test',
        'Severity (int)': '5',
    }
    patterns = [
        {'name': 'FullName', 'regex': r'full=(\w+) (\w+)'},
        {'name': 'Severity', 'regex': r'sev=(\w+)'},
        {'name': 'Status', 'regex': r'status=(\w+)'},
    ]
    mappings = [
        {
            'cef': 'suser',
            'pattern': 'FullName',
            'groups': [1, 2],
            'transform': 'upper',
        },
        {
            'cef': 'severity',
            'pattern': 'Severity',
            'group': 1,
            'value_map': {'info': '1', 'error': '8'},
            'transform': 'none',
        },
        {
            'cef': 'app',
            'pattern': 'Status',
            'group': 1,
            'replace_pattern': r'unknown',
            'replace_with': 'UNKNOWN',
            'transform': 'none',
        },
    ]

    paths = generate_files(header, mappings, patterns, tmp_path)
    loader = SourceFileLoader('cef_converter', paths[0])
    module = loader.load_module()
    conv = module.LogToCEFConverter()
    line = 'full=john doe sev=error status=unknown'
    result = conv.convert_line(line)
    assert 'suser=JOHN DOE' in result
    assert 'severity=8' in result
    assert 'app=UNKNOWN' in result

