import os
import json
from tools.registry import registry

def read_file(path: str, encoding: str = "utf-8") -> str:
    try:
        with open(path, "r", encoding=encoding) as f:
            content = f.read()
        return json.dumps({
            "path": os.path.abspath(path),
            "content": content,
            "size": len(content),
        })
    except FileNotFoundError:
        return json.dumps({"error": f"File not found: {path}"})
    except PermissionError:
        return json.dumps({"error": f"Permission denied: {path}"})
    except UnicodeDecodeError:
        return json.dumps({"error": f"Cannot decode file with encoding '{encoding}': {path}"})
    except Exception as e:
        return json.dumps({"error": f"Error reading file {path}: {str(e)}"})

registry.register(
    name="read_file",
    description="Read the contents of a text file from the local filesystem.",
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "The absolute or relative path to the file to read.",
            },
            "encoding": {
                "type": "string",
                "description": "The file encoding to use (default: utf-8).",
                "default": "utf-8",
            },
        },
        "required": ["path"],
    },
    handler=read_file,
)
