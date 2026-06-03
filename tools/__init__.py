import importlib
import pkgutil
import tools as tools_pkg

def discover_tools():
    for importer, modname, ispkg in pkgutil.iter_modules(tools_pkg.__path__):
        if modname != "__init__":
            importlib.import_module(f"tools.{modname}")
