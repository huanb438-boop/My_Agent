import json
import requests
from bs4 import BeautifulSoup
from tools.registry import registry

def web_fetch(url: str, timeout: int = 30) -> str:
    try:
        resp = requests.get(url, timeout=timeout, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        resp.raise_for_status()

        content_type = resp.headers.get("Content-Type", "")
        text = resp.text

        try:
            soup = BeautifulSoup(text, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            if len(text) > 10000:
                text = text[:10000] + "\n\n... [truncated]"
        except Exception:
            pass

        return json.dumps({
            "url": url,
            "status_code": resp.status_code,
            "content_type": content_type,
            "content": text,
        })
    except requests.Timeout:
        return json.dumps({"error": f"Timeout after {timeout}s: {url}"})
    except requests.HTTPError as e:
        return json.dumps({"error": f"HTTP {e.response.status_code}: {url}"})
    except requests.ConnectionError:
        return json.dumps({"error": f"Connection failed: {url}"})
    except Exception as e:
        return json.dumps({"error": f"Error fetching {url}: {str(e)}"})

registry.register(
    name="web_fetch",
    description="Fetch the content of a web page and extract readable text.",
    parameters={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to fetch.",
            },
            "timeout": {
                "type": "integer",
                "description": "Timeout in seconds (default: 30).",
                "default": 30,
            },
        },
        "required": ["url"],
    },
    handler=web_fetch,
)
