from dataclasses import dataclass, field
from ros2grapher.parser import scan_workspace, ROS2Node

@dataclass
class TopicConnection:
    topic: str
    msg_type: str
    publishers: list = field(default_factory=list)  # node names
    subscribers: list = field(default_factory=list) # node names
    dynamic: bool = False

@dataclass
class ROS2Graph:
    nodes: list = field(default_factory=list)        # list of ROS2Node
    topics: list = field(default_factory=list)       # list of TopicConnection
    orphan_topics: list = field(default_factory=list) # published but nobody subscribes, or vice versa

def build_graph(nodes: list[ROS2Node]) -> ROS2Graph:
    """Take a list of parsed nodes and build the connection graph."""
    graph = ROS2Graph(nodes=nodes)

    # collect all topics mentioned across all nodes
    topic_map = {}  # topic_name -> TopicConnection

    for node in nodes:
        for pub in node.publishers:
            if pub.topic not in topic_map:
                topic_map[pub.topic] = TopicConnection(
                    topic=pub.topic,
                    msg_type=pub.msg_type,
                    dynamic=pub.dynamic
                )
            topic_map[pub.topic].publishers.append(node.name)

        for sub in node.subscribers:
            if sub.topic not in topic_map:
                topic_map[sub.topic] = TopicConnection(
                    topic=sub.topic,
                    msg_type=sub.msg_type,
                    dynamic=sub.dynamic
                )
            topic_map[sub.topic].subscribers.append(node.name)

    # split into connected topics and orphans
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

if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    print(f"scanning {path}...\n")
    nodes = scan_workspace(path)
    graph = build_graph(nodes)
    print_graph(graph)
