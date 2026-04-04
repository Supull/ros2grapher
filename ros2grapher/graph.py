import os
from dataclasses import dataclass, field
from ros2grapher.parser import scan_workspace, ROS2Node

@dataclass
class TopicConnection:
    topic: str
    msg_type: str
    publishers: list = field(default_factory=list)
    subscribers: list = field(default_factory=list)
    dynamic: bool = False

@dataclass
class ServiceConnection:
    name: str
    srv_type: str
    servers: list = field(default_factory=list)
    clients: list = field(default_factory=list)

@dataclass
class ROS2Graph:
    nodes: list = field(default_factory=list)
    topics: list = field(default_factory=list)
    orphan_topics: list = field(default_factory=list)
    services: list = field(default_factory=list)

def get_package_name(filepath: str) -> str:
    parts = filepath.split(os.sep)
    for i in range(len(parts) - 1, 0, -1):
        candidate = os.sep.join(parts[:i])
        if os.path.exists(os.path.join(candidate, 'package.xml')):
            return parts[i - 1]
    return 'unknown'

def deduplicate_node_names(nodes: list[ROS2Node]) -> list[ROS2Node]:
    name_counts = {}
    for node in nodes:
        name_counts[node.name] = name_counts.get(node.name, 0) + 1
    for node in nodes:
        if name_counts[node.name] > 1:
            pkg = get_package_name(node.file)
            node.name = f"{node.name} ({pkg})"
    return nodes

def build_graph(nodes: list[ROS2Node]) -> ROS2Graph:
    nodes = deduplicate_node_names(nodes)
    graph = ROS2Graph(nodes=nodes)
    topic_map = {}
    service_map = {}

    for node in nodes:
        for pub in node.publishers:
            if pub.dynamic:
                graph.orphan_topics.append(TopicConnection(
                    topic=f'[dynamic] ({node.name})',
                    msg_type=pub.msg_type,
                    publishers=[node.name],
                    dynamic=True
                ))
                continue
            if pub.topic not in topic_map:
                topic_map[pub.topic] = TopicConnection(
                    topic=pub.topic,
                    msg_type=pub.msg_type,
                )
            topic_map[pub.topic].publishers.append(node.name)

        for sub in node.subscribers:
            if sub.dynamic:
                graph.orphan_topics.append(TopicConnection(
                    topic=f'[dynamic] ({node.name})',
                    msg_type=sub.msg_type,
                    subscribers=[node.name],
                    dynamic=True
                ))
                continue
            if sub.topic not in topic_map:
                topic_map[sub.topic] = TopicConnection(
                    topic=sub.topic,
                    msg_type=sub.msg_type,
                )
            topic_map[sub.topic].subscribers.append(node.name)

        for srv in node.services:
            if srv.name not in service_map:
                service_map[srv.name] = ServiceConnection(
                    name=srv.name,
                    srv_type=srv.srv_type,
                )
            service_map[srv.name].servers.append(node.name)

    for topic in topic_map.values():
        has_pub = len(topic.publishers) > 0
        has_sub = len(topic.subscribers) > 0
        if has_pub and has_sub:
            graph.topics.append(topic)
        else:
            graph.orphan_topics.append(topic)

    graph.services = list(service_map.values())

    return graph

def print_graph(graph: ROS2Graph):
    print(f"nodes ({len(graph.nodes)}):")
    for node in graph.nodes:
        print(f"  {node.name}")

    print(f"\nconnected topics ({len(graph.topics)}):")
    for topic in graph.topics:
        for pub in topic.publishers:
            for sub in topic.subscribers:
                print(f"  {pub} --> [{topic.topic} ({topic.msg_type})] --> {sub}")

    if graph.services:
        print(f"\nservices ({len(graph.services)}):")
        for srv in graph.services:
            for server in srv.servers:
                print(f"  {server} serves [{srv.name} ({srv.srv_type})]")

    if graph.orphan_topics:
        print(f"\norphan topics ({len(graph.orphan_topics)}):")
        for topic in graph.orphan_topics:
            if topic.publishers and not topic.subscribers:
                print(f"  {topic.publishers[0]} --> [{topic.topic}] --> ??? (no subscriber)")
            elif topic.subscribers and not topic.publishers:
                print(f"  ??? --> [{topic.topic}] --> {topic.subscribers[0]} (no publisher)")
            elif topic.dynamic:
                print(f"  [{topic.topic}] (dynamic, unresolved)")

if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    print(f"scanning {path}...\n")
    nodes = scan_workspace(path)
    graph = build_graph(nodes)
    print_graph(graph)
