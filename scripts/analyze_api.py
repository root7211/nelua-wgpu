#!/usr/bin/env python3
"""
analyze_api.py - Analyze WebGPU C API and generate a compatibility report.

This tool parses webgpu.h and wgpu.h headers and produces a structured report
showing all API elements, their categories, and potential binding issues.

Usage:
    python3 scripts/analyze_api.py [--json] [--markdown]
"""

import re
import sys
import os
import json
from collections import defaultdict

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODEGEN_DIR = os.path.join(PROJECT_DIR, 'wgpu-c', 'codegen')


def parse_header(path):
    """Parse a C header file and extract all API elements."""
    with open(path, 'r') as f:
        content = f.read()

    api = {
        'path': path,
        'lines': content.count('\n'),
        'functions': [],
        'enums': {},
        'structs': [],
        'typedefs': [],
        'callbacks': [],
        'macros': [],
        'opaque_types': [],
    }

    # Functions: WGPU_EXPORT <return_type> <name>(<params>);
    for m in re.finditer(
        r'WGPU_EXPORT\s+([\w\s\*]+?)\s+(wgpu\w+)\s*\(([^)]*)\)',
        content
    ):
        ret_type = m.group(1).strip()
        name = m.group(2)
        params = m.group(3).strip()
        api['functions'].append({
            'name': name,
            'return_type': ret_type,
            'params': params,
        })

    # Enums: typedef enum <Name> { ... } <Name>;
    for m in re.finditer(
        r'typedef\s+enum\s+(\w+)\s*\{([^}]*)\}\s*\w+;',
        content, re.DOTALL
    ):
        enum_name = m.group(1)
        body = m.group(2)
        values = []
        for v in re.finditer(r'(\w+)\s*=\s*(0x[0-9A-Fa-f]+|\d+)', body):
            values.append({'name': v.group(1), 'value': v.group(2)})
        api['enums'][enum_name] = values

    # Structs
    for m in re.finditer(r'typedef\s+struct\s+(\w+)\s*\{', content):
        api['structs'].append(m.group(1))

    # Callback typedefs
    for m in re.finditer(r'typedef\s+(\w[\w\s\*]*)\(\*(\w+)\)\s*\(([^)]*)\)', content):
        api['callbacks'].append({
            'name': m.group(2),
            'return_type': m.group(1).strip(),
            'params': m.group(3).strip(),
        })

    # Opaque pointer types: typedef struct <Name>Impl* <Name>;
    for m in re.finditer(r'typedef\s+struct\s+\w+Impl\s*\*\s*(\w+)\s*;', content):
        api['opaque_types'].append(m.group(1))

    # Macros
    for m in re.finditer(r'#define\s+(WGPU_\w+)\s+(.+)', content):
        name = m.group(1)
        value = m.group(2).strip()
        if name not in ('WGPU_OBJECT_ATTRIBUTE', 'WGPU_ENUM_ATTRIBUTE',
                        'WGPU_STRUCTURE_ATTRIBUTE', 'WGPU_FUNCTION_ATTRIBUTE',
                        'WGPU_NULLABLE', 'WGPU_EXPORT'):
            api['macros'].append({'name': name, 'value': value[:80]})

    return api


def identify_binding_issues(api):
    """Identify potential issues for Nelua binding generation."""
    issues = []

    # Check for bit fields (not supported by nelua-decl)
    # Check for unnamed fields
    # Check for complex macros

    macro_init_count = sum(1 for m in api['macros'] if '_INIT' in m['name'])
    if macro_init_count > 0:
        issues.append({
            'severity': 'info',
            'message': f'{macro_init_count} _INIT macros need manual Nelua helper functions',
        })

    complex_macros = [m for m in api['macros']
                      if '\\' in m['value'] or '##' in m['value']]
    if complex_macros:
        issues.append({
            'severity': 'warning',
            'message': f'{len(complex_macros)} multi-line/complex macros cannot be auto-generated',
        })

    return issues


def print_report(api_webgpu, api_wgpu, issues):
    """Print a formatted report."""
    print("=" * 60)
    print("  WebGPU API Analysis Report")
    print("=" * 60)
    print()

    for label, api in [("webgpu.h (Standard)", api_webgpu),
                       ("wgpu.h (Extensions)", api_wgpu)]:
        print(f"--- {label} ---")
        print(f"  Lines:        {api['lines']}")
        print(f"  Functions:    {len(api['functions'])}")
        print(f"  Enums:        {len(api['enums'])}")
        print(f"  Structs:      {len(api['structs'])}")
        print(f"  Callbacks:    {len(api['callbacks'])}")
        print(f"  Opaque types: {len(api['opaque_types'])}")
        print(f"  Macros:       {len(api['macros'])}")
        print()

    # Categorize functions by object
    print("--- Function Categories ---")
    categories = defaultdict(list)
    for fn in api_webgpu['functions']:
        name = fn['name']
        # wgpu<Object><Method> -> Object
        m = re.match(r'wgpu([A-Z][a-z]+(?:[A-Z][a-z]+)*?)([A-Z].*)', name)
        if m:
            obj = m.group(1)
            categories[obj].append(name)
        else:
            categories['Global'].append(name)

    for cat in sorted(categories.keys()):
        fns = categories[cat]
        print(f"  {cat}: {len(fns)} methods")

    print()

    # Opaque types (important for binding)
    if api_webgpu['opaque_types']:
        print("--- Opaque Handle Types ---")
        for t in sorted(api_webgpu['opaque_types']):
            print(f"  {t}")
        print()

    # Issues
    all_issues = issues
    if all_issues:
        print("--- Binding Issues ---")
        for issue in all_issues:
            severity = issue['severity'].upper()
            print(f"  [{severity}] {issue['message']}")
        print()

    # Auto-generation feasibility
    total_symbols = (
        len(api_webgpu['functions']) + len(api_webgpu['enums']) +
        len(api_webgpu['structs']) + len(api_webgpu['callbacks']) +
        len(api_wgpu['functions']) + len(api_wgpu['enums']) +
        len(api_wgpu['structs'])
    )
    auto_symbols = total_symbols - len([m for m in api_webgpu['macros'] if '_INIT' in m['name']])

    print("--- Auto-generation Feasibility ---")
    print(f"  Total symbols:      {total_symbols}")
    print(f"  Auto-generable:     {auto_symbols} ({auto_symbols/total_symbols*100:.0f}%)")
    print(f"  Manual handling:    {total_symbols - auto_symbols}")
    print()


def main():
    webgpu_h = os.path.join(CODEGEN_DIR, 'webgpu.h')
    wgpu_h = os.path.join(CODEGEN_DIR, 'wgpu.h')

    for h in [webgpu_h, wgpu_h]:
        if not os.path.exists(h):
            print(f"Error: {h} not found. Run scripts/fetch_headers.sh first.", file=sys.stderr)
            sys.exit(1)

    api_webgpu = parse_header(webgpu_h)
    api_wgpu = parse_header(wgpu_h)

    issues_webgpu = identify_binding_issues(api_webgpu)
    issues_wgpu = identify_binding_issues(api_wgpu)

    if '--json' in sys.argv:
        output = {
            'webgpu': api_webgpu,
            'wgpu': api_wgpu,
            'issues': issues_webgpu + issues_wgpu,
        }
        print(json.dumps(output, indent=2))
    else:
        print_report(api_webgpu, api_wgpu, issues_webgpu + issues_wgpu)


if __name__ == '__main__':
    main()
