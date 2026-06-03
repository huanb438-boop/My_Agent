import json

class ToolRegistry:
    def __init__(self):
        self._tools = {}
        self._handlers = {}

    def register(self, name: str, description: str, parameters: dict, handler):
        self._tools[name] = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        }
        self._handlers[name] = handler

    def get_definitions(self) -> list:
        return list(self._tools.values())

    def dispatch(self, name: str, args: dict) -> str:
        handler = self._handlers.get(name)
        if not handler:
            return json.dumps({"error": f"Tool {name} not found."})
        try:
            return handler(**args)
        except Exception as e:
            return json.dumps({"error": f"Error in tool {name}: {str(e)}"})

registry = ToolRegistry()
