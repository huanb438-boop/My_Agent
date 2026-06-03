import subprocess
import json
from tools.registry import registry

def bash_execute(command: str, timeout: int = 30) -> str:
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
        )
        return json.dumps({
            "stdout": result.stdout[-3000:],
            "stderr": result.stderr[-3000:],
            "exit_code": result.returncode,
        })
    except subprocess.TimeoutExpired:
        return json.dumps({"error": f"Command {command} timed out after {timeout} seconds."})
    except Exception as e:
        return json.dumps({"error": f"Error in command {command}: {str(e)}"})

registry.register(
    name="bash_execute",
    description="Execute a shell command on the local system.",
    parameters={
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute.",
            },
            "timeout": {
                "type": "integer",
                "description": "The timeout in seconds for the command execution.",
                "default": 30,
            },
        },
        "required": ["command"],
    },
    handler=bash_execute,
)
