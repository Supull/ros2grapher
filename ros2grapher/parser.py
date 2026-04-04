import ast
import os
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Publisher:
    topic: str
    msg_type: str
    dynamic: bool = False

@dataclass
class Subscriber:
    topic: str
    msg_type: str
    dynamic: bool = False

@dataclass
class Service:
    name: str
    srv_type: str

@dataclass
class ROS2Node:
    name: str
    file: str
    publishers: list = field(default_factory=list)
    subscribers: list = field(default_factory=list)
    services: list = field(default_factory=list)

def extract_string(node) -> Optional[str]:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None

def extract_name(node) -> Optional[str]:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None

def parse_file(filepath: str) -> list[ROS2Node]:
    with open(filepath, 'r') as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        print(f"  syntax error in {filepath}: {e}")
        return []

    nodes = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        bases = [extract_name(b) for b in node.bases]
        if 'Node' not in bases:
            continue

        ros_node = ROS2Node(name=f"unknown_{node.name}", file=filepath)

        for item in ast.walk(node):
            if isinstance(item, ast.Call):
                func = item.func
                if isinstance(func, ast.Attribute) and func.attr == '__init__':
                    if item.args:
                        name = extract_string(item.args[0])
                        if name:
                            ros_node.name = name

                if isinstance(func, ast.Attribute) and func.attr == 'create_publisher':
                    if len(item.args) >= 2:
                        msg_type = extract_name(item.args[0]) or 'Unknown'
                        topic = extract_string(item.args[1])
                        if topic:
                            ros_node.publishers.append(
                                Publisher(topic=topic, msg_type=msg_type)
                            )
                        else:
                            ros_node.publishers.append(
                                Publisher(topic='[dynamic]', msg_type=msg_type, dynamic=True)
                            )

                if isinstance(func, ast.Attribute) and func.attr == 'create_subscription':
                    if len(item.args) >= 2:
                        msg_type = extract_name(item.args[0]) or 'Unknown'
                        topic = extract_string(item.args[1])
                        if topic:
                            ros_node.subscribers.append(
                                Subscriber(topic=topic, msg_type=msg_type)
                            )
                        else:
                            ros_node.subscribers.append(
                                Subscriber(topic='[dynamic]', msg_type=msg_type, dynamic=True)
                            )

                if isinstance(func, ast.Attribute) and func.attr == 'create_service':
                    if len(item.args) >= 2:
                        srv_type = extract_name(item.args[0]) or 'Unknown'
                        name = extract_string(item.args[1])
                        if name:
                            ros_node.services.append(
                                Service(name=name, srv_type=srv_type)
                            )

        nodes.append(ros_node)

    return nodes

def scan_workspace(path: str) -> list[ROS2Node]:
    all_nodes = []

    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in ('build', 'install', 'log', '__pycache__', '.git')]

        for file in files:
            if not file.endswith('.py'):
                continue
            if file == '__init__.py':
                continue

            filepath = os.path.join(root, file)
            print(f"  scanning {filepath}")
            nodes = parse_file(filepath)
            all_nodes.extend(nodes)

    return all_nodes

if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    print(f"scanning {path}...\n")
    nodes = scan_workspace(path)
    print(f"\nfound {len(nodes)} node(s):\n")
    for node in nodes:
        print(f"  [{node.name}] in {os.path.basename(node.file)}")
        for pub in node.publishers:
            print(f"    publishes  → {pub.topic} ({pub.msg_type})")
        for sub in node.subscribers:
            print(f"    subscribes → {sub.topic} ({sub.msg_type})")
        for srv in node.services:
            print(f"    service    → {srv.name} ({srv.srv_type})")
