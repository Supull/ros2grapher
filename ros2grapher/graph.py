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
class ROS2Graph:
    nodes: list = field(default_factory=list)
    topics: list = field(default_factory=list)
    orphan_topics: list = field(default_factory=list)

def get_package_name(filepath: str) -> str:
    """Extract package name from file path."""
    parts = filepath.split(os.sep)
    # walk up from filename looking for the package directory
    # package dir is usually the one containing __init__.py at top level
    for i in range(len(parts) - 1, 0, -1):
        candidate = os.sep.join(parts[:i])
        if os.path.exists(os.path.join(candidate, 'package.xml')):
            return parts[i - 1]
    return 'unknown'

def deduplicate_node_names(nodes: list[ROS2Node]) -> list[ROS2Node]:
    """If two nodes share the same name, append package name to differentiate."""
    name_counts = {}
    for node in nodes:
        name_counts[node.name] = name_counts.get(node.name, 0) + 1

    for node in nodes:
        if name_counts[node.name] > 1:
            pkg = get_package_name(node.file)
            node.name = f"{node.name} ({pkg})"

    return nodes

def build_graph(nodes: list[ROS2Node]) -> ROS2Graph:
    """Take a list of parsed nodes and build the connection graph."""

    nodes = deduplicate_node_names(nodes)

    graph = ROS2Graph(nodes=nodes)
    topic_map = {}

    for node in nodes:
        for pub in node.publishers:
            # never match dynamic topics with each other
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
            # never match dynamic topics with each other
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

    # split into connected and orphan topics
    for topic in topic_map.values():
        has_pub = len(topic.publishers) > 0
        has_sub = len(topic.subscribers) > 0

        if has_pub and has_sub:
            graph.topics.append(topic)
        else:
            graph.orphan_topics.append(topic)

    return graph

def print_graph(graph: ROS2Graph):
    """Pretty print the graph to terminal."""
    print(f"nodes ({len(graph.nodes)}):")
    for node in graph.nodes:
        print(f"  {node.name}")

    print(f"\nconnected topics ({len(graph.topics)}):")
    for topic in graph.topics:
        for pub in topic.publishers:
            for sub in topic.subscribers:
                print(f"  {pub} --> [{topic.topic} ({topic.msg_type})] --> {sub}")

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
