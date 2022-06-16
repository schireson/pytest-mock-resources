import importlib


def verify_import(*imports, extra_name):
    for module in imports:
        try:
            importlib.import_module(module)
        except ImportError:
            raise RuntimeError(
                f"Cannot use {extra_name} fixtures without {module}. "
                "Install pytest-mock-resources with one of the following "
                f"extras: {extra_name}."
            )


def try_import(module):
    try:
        return importlib.import_module(module)
    except ImportError:
        return None
