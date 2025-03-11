from __future__ import annotations

import importlib
import inspect
import pkgutil
import sys

from pathlib import Path

from gooey import Gooey, GooeyParser

# Add PyKotor to Python path
pykotor_path = Path(__file__).parent.parent.parent.parent.parent / "Libraries" / "PyKotor" / "src"
sys.path.append(str(pykotor_path))

import pykotor


def get_all_modules(package):
    """Recursively get all modules from a package."""
    modules = {}

    # Get the package name
    package_name = package.__name__

    # Walk through all modules in the package
    for loader, module_name, is_pkg in pkgutil.walk_packages(package.__path__, package_name + "."):
        try:
            # Import the module
            module = importlib.import_module(module_name)
            modules[module_name] = module

        except Exception as e:
            print(f"Warning: Could not import {module_name}: {e}")

    return modules

def get_module_items(module):
    """Get all public functions and classes from a module."""
    items = []

    for name, obj in inspect.getmembers(module):
        # Skip private/internal items
        if name.startswith("_"):
            continue

        # Get functions
        if inspect.isfunction(obj):
            items.append(("function", name, obj))

        # Get classes
        elif inspect.isclass(obj):
            methods = []
            for method_name, method in inspect.getmembers(obj):
                if (not method_name.startswith("_") and
                    inspect.isfunction(method)):
                    methods.append((method_name, method))
            if methods:
                items.append(("class", name, obj, methods))

    return items

@Gooey(
    program_name="PyKotor Auto GUI",
    navigation="TABBED",
    default_size=(1000, 800),
    richtext_controls=False,
    terminal_font_family="Courier New",
    terminal_font_size=9,
    show_success_modal=False,
    show_failure_modal=False
)
def main():
    parser = GooeyParser(description="Automatically generated GUI for PyKotor")

    # Get all modules recursively
    all_modules = get_all_modules(pykotor)

    # Create module tabs
    subs = parser.add_subparsers(dest="module")

    # Track all items for execution
    all_items = {}

    # Create a tab for each module
    for module_name, module in all_modules.items():
        # Skip if no public items
        items = get_module_items(module)
        if not items:
            continue

        # Create module parser
        module_parser = subs.add_parser(module_name.split(".")[-1], help=module.__doc__)
        module_subs = module_parser.add_subparsers(dest=f"{module_name}_item")

        # Store items for later execution
        all_items[module_name] = items

        # Add functions and classes
        for item in items:
            item_type = item[0]
            name = item[1]
            obj = item[2]

            if item_type == "function":
                func_parser = module_subs.add_parser(name, help=obj.__doc__)
                sig = inspect.signature(obj)
                for param_name, param in sig.parameters.items():
                    if param.kind not in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                        param_type = param.annotation if param.annotation != inspect._empty else str
                        param_type_name = getattr(param_type, "__name__", str(param_type))
                        func_parser.add_argument(
                            f"--{param_name}",
                            help=f"Type: {param_type_name}",
                            required=param.default == param.empty
                        )

            elif item_type == "class":
                class_parser = module_subs.add_parser(name, help=obj.__doc__)
                class_subs = class_parser.add_subparsers(dest=f"{module_name}_{name}_method")
                methods = item[3]

                for method_name, method in methods:
                    method_parser = class_subs.add_parser(method_name, help=method.__doc__)
                    sig = inspect.signature(method)
                    for param_name, param in sig.parameters.items():
                        if param_name != "self" and param.kind not in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                            param_type = param.annotation if param.annotation != inspect._empty else str
                            param_type_name = getattr(param_type, "__name__", str(param_type))
                            method_parser.add_argument(
                                f"--{param_name}",
                                help=f"Type: {param_type_name}",
                                required=param.default == param.empty
                            )

    args = parser.parse_args()

    # Execute the selected function/method
    try:
        if args.module:
            module_name = next(name for name in all_modules.keys() if name.endswith("." + args.module))
            items = all_items[module_name]
            item_arg = getattr(args, f"{module_name}_item", None)

            if item_arg:
                selected_item = next(item for item in items if item[1] == item_arg)

                if selected_item[0] == "function":
                    # Call function
                    func = selected_item[2]
                    kwargs = {k: v for k, v in vars(args).items()
                            if k not in ["module", f"{module_name}_item"]
                            and v is not None
                            and k in inspect.signature(func).parameters}
                    result = func(**kwargs)
                    print(f"Result: {result}")

                elif selected_item[0] == "class":
                    # Get method name
                    method_arg = getattr(args, f"{module_name}_{selected_item[1]}_method", None)
                    if method_arg:
                        # Create instance and call method
                        cls = selected_item[2]
                        obj = cls()
                        method = getattr(obj, method_arg)
                        kwargs = {k: v for k, v in vars(args).items()
                                if k not in ["module", f"{module_name}_item", f"{module_name}_{selected_item[1]}_method"]
                                and v is not None
                                and k in inspect.signature(method).parameters}
                        result = method(**kwargs)
                        print(f"Result: {result}")

    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()
