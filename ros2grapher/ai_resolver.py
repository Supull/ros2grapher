import os
import json
import time
import urllib.request
import urllib.error

GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent"

MAX_REQUESTS_PER_MINUTE = 14
REQUEST_INTERVAL = 60.0 / MAX_REQUESTS_PER_MINUTE

_last_request_time = 0.0

PROMPT_TEMPLATE = """You are analyzing ROS2 Python or C++ source code.
Your task is to find the TOPIC NAME string used in a create_publisher or create_subscription call.
The topic name is stored in the variable: `{variable}`

Rules:
- Return the TOPIC NAME only — a string like '/chatter' or '/camera/image_raw'.
- Topic names start with / or are plain strings like 'chatter'.
- If the topic comes from declare_parameter, return the default value string.
- If the topic is constructed (e.g., f-strings), return a template like /robot/{{id}}/cmd_vel.
- If the topic name cannot be determined, return "UNKNOWN".
- Do NOT return message types like 'String', 'Image', 'Twist' — those are NOT topic names.
- Do NOT return variable names like 'topic', 'topic_name' — find the actual string value.
- Do NOT guess or invent values.

After the topic name, on a new line write one of:
- HIGH if found directly in declare_parameter default value
- MEDIUM if inferred from context
- LOW if it is a best guess

Format:
<topic_name>
<confidence>

Source code:
{source}
"""

import hashlib

CACHE_FILE = '.ros2grapher_cache.json'

def get_api_key():
    return os.environ.get('GEMINI_API_KEY')

def _load_cache() -> dict:
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def _save_cache(cache: dict):
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=2)
    except Exception:
        pass

def _cache_key(source: str, variable: str) -> str:
    """Generate a cache key from source code and variable name."""
    content = f"{variable}:{source[:3000]}"
    return hashlib.md5(content.encode()).hexdigest()

def _wait_for_rate_limit():
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < REQUEST_INTERVAL:
        time.sleep(REQUEST_INTERVAL - elapsed)
    _last_request_time = time.time()

def _call_api(prompt, api_key, retries=3):
    payload = json.dumps({
        "contents": [{
            "parts": [{"text": prompt}]
        }],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 64,
        }
    }).encode('utf-8')

    for attempt in range(retries):
        try:
            _wait_for_rate_limit()
            req = urllib.request.Request(
                GEMINI_API_URL,
                data=payload,
                headers={
                    'Content-Type': 'application/json',
                    'x-goog-api-key': api_key
                },
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                result = json.loads(response.read().decode('utf-8'))
                if result.get('promptFeedback', {}).get('blockReason'):
                    return None
                candidates = result.get('candidates', [])
                if not candidates:
                    return None
                parts = candidates[0].get('content', {}).get('parts', [])
                if not parts:
                    return None
                return parts[0].get('text', '').strip()

        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 30 * (attempt + 1)
                print(f"    rate limited, waiting {wait}s...")
                time.sleep(wait)
            elif e.code == 503:
                wait = 10 * (attempt + 1)
                print(f"    service unavailable, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"    api error: {e.code}")
                return None
        except Exception as e:
            print(f"    ai resolver error: {e}")
            if attempt < retries - 1:
                time.sleep(5)

    return None

def _parse_response(text):
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    if not lines:
        return 'UNKNOWN', 'unknown'
    topic = lines[0]
    confidence = 'low'
    if len(lines) >= 2:
        level = lines[1].upper()
        if 'HIGH' in level:
            confidence = 'high'
        elif 'MEDIUM' in level:
            confidence = 'medium'
        else:
            confidence = 'low'
    if topic == 'UNKNOWN':
        return '[dynamic]', 'unknown'
    return topic, confidence

def resolve_dynamic_topic(source, variable):
    api_key = get_api_key()
    if not api_key:
        return '[dynamic]', 'unknown'

    # check cache first
    cache = _load_cache()
    key = _cache_key(source, variable)
    if key in cache:
        cached = cache[key]
        print(f"    (cached) {cached[0]} ({cached[1]} confidence)")
        return cached[0], cached[1]

    prompt = PROMPT_TEMPLATE.format(variable=variable, source=source[:3000])
    text = _call_api(prompt, api_key)
    if not text:
        return '[dynamic]', 'unknown'

    result = _parse_response(text)

    # save to cache
    cache[key] = result
    _save_cache(cache)

    return result

def resolve_nodes(nodes, source_map):
    api_key = get_api_key()
    if not api_key:
        print("  no GEMINI_API_KEY found — skipping AI resolution")
        return nodes

    print("  running AI resolver for dynamic topics...")

    for node in nodes:
        source = source_map.get(node.file, '')
        if not source:
            continue

        for pub in node.publishers:
            if pub.dynamic and pub.topic == '[dynamic]':
                print(f"    resolving dynamic publisher in {node.name}...")
                topic, confidence = resolve_dynamic_topic(source, 'topic')
                if confidence != 'unknown':
                    pub.topic = topic
                    pub.dynamic = False
                    pub.ai_resolved = True
                    pub.ai_confidence = confidence
                    print(f"    resolved to {topic} ({confidence} confidence)")

        for sub in node.subscribers:
            if sub.dynamic and sub.topic == '[dynamic]':
                print(f"    resolving dynamic subscriber in {node.name}...")
                topic, confidence = resolve_dynamic_topic(source, 'topic')
                if confidence != 'unknown':
                    sub.topic = topic
                    sub.dynamic = False
                    sub.ai_resolved = True
                    sub.ai_confidence = confidence
                    print(f"    resolved to {topic} ({confidence} confidence)")

    return nodes

if __name__ == '__main__':
    test_source = """
class CameraNode(Node):
    def __init__(self):
        super().__init__('camera_node')
        self.declare_parameter('topic', '/camera/image_raw')
        topic = self.get_parameter('topic').value
        self.create_publisher(Image, topic, 10)
"""
    print("testing AI resolver...")
    result, confidence = resolve_dynamic_topic(test_source, 'topic')
    print(f"resolved to: {result} (confidence: {confidence})")
