#!/usr/bin/env python3
"""Generate DeNCS node implementations from Java source files.

This script reads the Java source files from vendor/DeNCS and generates
the corresponding Python implementations for placeholder files.
"""

from __future__ import annotations

import re

from pathlib import Path


def java_name_to_python(java_name: str) -> str:
    """Convert AEqualBinaryOp to a_equal_binary_op."""
    # Add underscore before uppercase letters (but not at start)
    result = re.sub(r'(?<!^)(?=[A-Z])', '_', java_name)
    return result.lower()


def python_name_to_java(python_name: str) -> str:
    """Convert a_equal_binary_op to AEqualBinaryOp."""
    parts = python_name.split('_')
    return ''.join(part.capitalize() for part in parts)


def parse_java_file(java_path: Path) -> dict:
    """Parse a Java file and extract class info."""
    content = java_path.read_text(encoding='utf-8')
    
    # Find class name and parent
    class_match = re.search(r'public final class (\w+) extends (\w+)', content)
    if not class_match:
        return None
    
    class_name = class_match.group(1)
    parent_name = class_match.group(2)
    
    # Find fields (private _field_ type)
    fields = []
    for match in re.finditer(r'private (\w+) _(\w+)_;', content):
        field_type = match.group(1)
        field_name = match.group(2)
        fields.append((field_type, field_name))
    
    return {
        'class_name': class_name,
        'parent_name': parent_name,
        'fields': fields,
    }


def generate_python_class(info: dict) -> str:
    """Generate Python class code from parsed Java info."""
    class_name = info['class_name']
    parent_name = info['parent_name']
    fields = info['fields']
    
    parent_python = java_name_to_python(parent_name)
    
    lines = [
        'from __future__ import annotations',
        '',
        'from typing import TYPE_CHECKING',
        '',
        f'from pykotor.resource.formats.ncs.dencs.node.{parent_python} import {parent_name}  # pyright: ignore[reportMissingImports]',
        '',
        'if TYPE_CHECKING:',
        '    from pykotor.resource.formats.ncs.dencs.node.node import Node  # pyright: ignore[reportMissingImports]',
        '    from pykotor.resource.formats.ncs.dencs.analysis.analysis_adapter import Analysis  # pyright: ignore[reportMissingImports]',
    ]
    
    # Add field type imports
    for field_type, _ in fields:
        field_type_python = java_name_to_python(field_type)
        lines.append(f'    from pykotor.resource.formats.ncs.dencs.node.{field_type_python} import {field_type}  # pyright: ignore[reportMissingImports]')
    
    lines.extend([
        '',
        '',
        f'class {class_name}({parent_name}):',
        f'    """Port of {class_name}.java from DeNCS."""',
        '',
    ])
    
    # Generate __init__
    if fields:
        init_params = ', '.join(f'{name}: {type_} | None = None' for type_, name in fields)
        lines.append(f'    def __init__(self, {init_params}):')
    else:
        lines.append('    def __init__(self):')
    
    lines.append('        super().__init__()')
    
    for field_type, field_name in fields:
        lines.append(f'        self._{field_name}: {field_type} | None = None')
    
    if fields:
        lines.append('')
        for field_type, field_name in fields:
            lines.append(f'        if {field_name} is not None:')
            lines.append(f'            self.set_{field_name}({field_name})')
    
    # Generate clone
    lines.extend(['', '    def clone(self):'])
    if fields:
        clone_args = ', '.join(f'self.clone_node(self._{name})' for _, name in fields)
        lines.append(f'        return {class_name}({clone_args})')
    else:
        lines.append(f'        return {class_name}()')
    
    # Generate apply
    case_method = f'case_{java_name_to_python(class_name)}'
    lines.extend([
        '',
        '    def apply(self, sw: Analysis):',
        f'        sw.{case_method}(self)',
    ])
    
    # Generate getters and setters for each field
    for field_type, field_name in fields:
        # Getter
        lines.extend([
            '',
            f'    def get_{field_name}(self) -> {field_type} | None:',
            f'        return self._{field_name}',
        ])
        
        # Setter
        lines.extend([
            '',
            f'    def set_{field_name}(self, node: {field_type} | None):',
            f'        if self._{field_name} is not None:',
            f'            self._{field_name}.set_parent(None)',
            '        if node is not None:',
            '            if node.parent() is not None:',
            '                node.parent().remove_child(node)',
            '            node.set_parent(self)',
            f'        self._{field_name} = node',
        ])
    
    # Generate __str__
    if fields:
        to_string_parts = ' + '.join(f'self.to_string(self._{name})' for _, name in fields)
        lines.extend([
            '',
            '    def __str__(self) -> str:',
            f'        return {to_string_parts}',
        ])
    
    # Generate remove_child
    lines.extend(['', '    def remove_child(self, child: Node):'])
    for _, field_name in fields:
        lines.extend([
            f'        if self._{field_name} == child:',
            f'            self._{field_name} = None',
            '            return',
        ])
    if not fields:
        lines.append('        pass')
    
    # Generate replace_child
    lines.extend(['', '    def replace_child(self, old_child: Node, new_child: Node):'])
    for _, field_name in fields:
        lines.extend([
            f'        if self._{field_name} == old_child:',
            f'            self.set_{field_name}(new_child)  # type: ignore',
            '            return',
        ])
    if not fields:
        lines.append('        pass')
    
    # Helper methods
    lines.extend([
        '',
        '    def clone_node(self, node):',
        '        if node is not None:',
        '            return node.clone()',
        '        return None',
        '',
        '    def to_string(self, node):',
        '        if node is not None:',
        '            return str(node)',
        '        return ""',
        '',
    ])
    
    return '\n'.join(lines)


def main():
    """Main function to generate missing node files."""
    java_nodes_path = Path("G:/GitHub/PyKotor/vendor/DeNCS/procyon/com/knights2end/nwscript/decomp/node")
    python_nodes_path = Path("G:/GitHub/PyKotor/Libraries/PyKotor/src/pykotor/resource/formats/ncs/dencs/node")
    
    generated = 0
    
    for py_file in sorted(python_nodes_path.glob("*.py")):
        if py_file.name == "__init__.py":
            continue
        
        # Check if it's a placeholder
        content = py_file.read_text(encoding='utf-8')
        if 'placeholder' not in content.lower():
            continue
        
        # Find corresponding Java file
        class_name = python_name_to_java(py_file.stem)
        java_file = java_nodes_path / f"{class_name}.java"
        
        if not java_file.exists():
            print(f"Warning: No Java source for {py_file.name}")
            continue
        
        # Parse and generate
        info = parse_java_file(java_file)
        if info is None:
            print(f"Warning: Could not parse {java_file.name}")
            continue
        
        python_code = generate_python_class(info)
        py_file.write_text(python_code, encoding='utf-8')
        print(f"Generated: {py_file.name}")
        generated += 1
    
    print(f"\nTotal files generated: {generated}")


if __name__ == "__main__":
    main()

