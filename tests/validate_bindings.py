#!/usr/bin/env python3
"""
validate_bindings.py - Validate generated Nelua bindings against C headers

Checks that all exported functions, types, enums from webgpu.h and wgpu.h
are present in the generated .nelua files.

Usage:
    python3 tests/validate_bindings.py
"""

import re
import sys
import os

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODEGEN_DIR = os.path.join(PROJECT_DIR, 'wgpu-c', 'codegen')
WGPU_C_DIR = os.path.join(PROJECT_DIR, 'wgpu-c')


def extract_c_symbols(header_path):
    """Extract exported symbols from a C header file."""
    symbols = {
        'functions': [],
        'enums': [],
        'structs': [],
        'typedefs': [],
        'callbacks': [],
    }

    if not os.path.exists(header_path):
        print(f"  WARNING: {header_path} not found")
        return symbols

    with open(header_path, 'r') as f:
        content = f.read()

    # Extract WGPU_EXPORT functions
    for m in re.finditer(r'WGPU_EXPORT\s+\w[\w\s\*]*\s+(wgpu\w+)\s*\(', content):
        symbols['functions'].append(m.group(1))

    # Extract typedef enum
    for m in re.finditer(r'typedef\s+enum\s+(\w+)', content):
        symbols['enums'].append(m.group(1))

    # Extract typedef struct
    for m in re.finditer(r'typedef\s+struct\s+(\w+)', content):
        symbols['structs'].append(m.group(1))

    # Extract callback typedefs
    for m in re.finditer(r'typedef\s+\w[\w\s\*]*\(\*(\w+)\)', content):
        symbols['callbacks'].append(m.group(1))

    return symbols


def check_nelua_binding(nelua_path, symbols):
    """Check if generated Nelua file contains all expected symbols."""
    if not os.path.exists(nelua_path):
        return None, "File not found"

    with open(nelua_path, 'r') as f:
        content = f.read()

    results = {
        'found': [],
        'missing': [],
    }

    all_symbols = (
        [(s, 'function') for s in symbols['functions']] +
        [(s, 'enum') for s in symbols['enums']] +
        [(s, 'struct') for s in symbols['structs']] +
        [(s, 'callback') for s in symbols['callbacks']]
    )

    for name, kind in all_symbols:
        if name in content:
            results['found'].append((name, kind))
        else:
            results['missing'].append((name, kind))

    return results, None


def check_macros_binding(macros_path, header_path):
    """Check if macro constants file covers important macros."""
    if not os.path.exists(macros_path):
        return None, "Macros file not found"
    if not os.path.exists(header_path):
        return None, "Header not found"

    with open(header_path, 'r') as f:
        header_content = f.read()
    with open(macros_path, 'r') as f:
        macros_content = f.read()

    # Important macros that should be covered
    important_macros = []
    for m in re.finditer(r'#define\s+(WGPU_(?:TRUE|FALSE|ARRAY_LAYER_COUNT_UNDEFINED|'
                         r'COPY_STRIDE_UNDEFINED|DEPTH_CLEAR_VALUE_UNDEFINED|'
                         r'DEPTH_SLICE_UNDEFINED|LIMIT_U32_UNDEFINED|LIMIT_U64_UNDEFINED|'
                         r'MIP_LEVEL_COUNT_UNDEFINED|QUERY_SET_INDEX_UNDEFINED|'
                         r'STRLEN|WHOLE_MAP_SIZE|WHOLE_SIZE))\b', header_content):
        important_macros.append(m.group(1))

    found = []
    missing = []
    for macro in important_macros:
        if macro in macros_content:
            found.append(macro)
        else:
            missing.append(macro)

    return {'found': found, 'missing': missing}, None


def main():
    print("=== nelua-wgpu Binding Validation ===")
    print()

    errors = 0

    # 1. Check that headers exist
    print("[1] Checking header files...")
    webgpu_h = os.path.join(CODEGEN_DIR, 'webgpu.h')
    wgpu_h = os.path.join(CODEGEN_DIR, 'wgpu.h')

    for h in [webgpu_h, wgpu_h]:
        if os.path.exists(h):
            lines = sum(1 for _ in open(h))
            print(f"  OK: {os.path.basename(h)} ({lines} lines)")
        else:
            print(f"  MISSING: {os.path.basename(h)}")
            errors += 1
    print()

    # 2. Extract C symbols
    print("[2] Extracting C symbols...")
    webgpu_symbols = extract_c_symbols(webgpu_h)
    wgpu_symbols = extract_c_symbols(wgpu_h)

    print(f"  webgpu.h: {len(webgpu_symbols['functions'])} functions, "
          f"{len(webgpu_symbols['enums'])} enums, "
          f"{len(webgpu_symbols['structs'])} structs, "
          f"{len(webgpu_symbols['callbacks'])} callbacks")
    print(f"  wgpu.h:   {len(wgpu_symbols['functions'])} functions, "
          f"{len(wgpu_symbols['enums'])} enums, "
          f"{len(wgpu_symbols['structs'])} structs")
    print()

    # 3. Check main binding file
    print("[3] Checking main binding file...")
    webgpu_nelua = os.path.join(WGPU_C_DIR, 'webgpu.nelua')
    if os.path.exists(webgpu_nelua):
        results, err = check_nelua_binding(webgpu_nelua, webgpu_symbols)
        if err:
            print(f"  ERROR: {err}")
            errors += 1
        else:
            total = len(results['found']) + len(results['missing'])
            coverage = len(results['found']) / total * 100 if total > 0 else 0
            print(f"  Coverage: {len(results['found'])}/{total} ({coverage:.1f}%)")
            if results['missing']:
                print(f"  Missing ({len(results['missing'])}):")
                for name, kind in results['missing'][:10]:
                    print(f"    - {name} ({kind})")
                if len(results['missing']) > 10:
                    print(f"    ... and {len(results['missing']) - 10} more")
    else:
        print("  SKIPPED: webgpu.nelua not generated yet")
        print("  (Run 'make generate' in wgpu-c/codegen/ to generate)")
    print()

    # 4. Check macros file
    print("[4] Checking macro constants...")
    macros_nelua = os.path.join(WGPU_C_DIR, 'webgpu_macros.nelua')
    if os.path.exists(macros_nelua):
        results, err = check_macros_binding(macros_nelua, webgpu_h)
        if err:
            print(f"  ERROR: {err}")
            errors += 1
        else:
            total = len(results['found']) + len(results['missing'])
            print(f"  Coverage: {len(results['found'])}/{total} macros")
            if results['missing']:
                print(f"  Missing: {', '.join(results['missing'])}")
                errors += 1
            else:
                print("  All important macros covered")
    else:
        print("  MISSING: webgpu_macros.nelua not found")
        errors += 1
    print()

    # Summary
    print("=== Summary ===")
    if errors == 0:
        print("All checks passed!")
        return 0
    else:
        print(f"{errors} issue(s) found")
        return 1


if __name__ == '__main__':
    sys.exit(main())
