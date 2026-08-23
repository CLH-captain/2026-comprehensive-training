import json
import urllib.request

payload = {
    "model": "qwen3.5-4b-64k:latest",
    "messages": [
        {"role": "user", "content": "用一句话回答：本地大语言模型有什么作用？"}
    ],
    "stream": False,
    "think": False,
    "options": {"num_predict": 64},
}

request = urllib.request.Request(
    "http://127.0.0.1:11434/api/chat",
    data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(request, timeout=180) as response:
    result = json.load(response)

print(json.dumps({
    "model": result.get("model"),
    "content": result.get("message", {}).get("content"),
    "done": result.get("done"),
}, ensure_ascii=False, indent=2))