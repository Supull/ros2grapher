import re
import os
from ros2grapher.parser import ROS2Node, Publisher, Subscriber, Service

# matches: class MyNode : public rclcpp::Node
CLASS_PATTERN = re.compile(
    r'class\s+(\w+)\s*:.*?public\s+(?:rclcpp::)?Node'
)

# matches: Node("node_name") in constructor initializer
NODE_NAME_PATTERN = re.compile(
    r'(?:rclcpp::)?Node\s*\(\s*"([^"]+)"\s*[,)]'
)

# matches: create_publisher<pkg::msg::Type>("/topic", qos)
PUBLISHER_PATTERN = re.compile(
    r'create_publisher\s*<\s*([\w:]+)\s*>\s*\(\s*"([^"]+)"\s*,'
)

# matches: create_subscription<pkg::msg::Type>("/topic", qos, cb)
SUBSCRIPTION_PATTERN = re.compile(
    r'create_subscription\s*<\s*([\w:]+)\s*>\s*\(\s*"([^"]+)"\s*,'
)

# matches: create_publisher<pkg::msg::Type>(some_var, qos) — dynamic
PUBLISHER_DYNAMIC_PATTERN = re.compile(
    r'create_publisher\s*<\s*([\w:]+)\s*>\s*\(\s*(\w+)\s*,'
)

# matches: create_subscription<pkg::msg::Type>(some_var, qos, cb) — dynamic
SUBSCRIPTION_DYNAMIC_PATTERN = re.compile(
    r'create_subscription\s*<\s*([\w:]+)\s*>\s*\(\s*(\w+)\s*,'
)

# matches: create_service<pkg::srv::Type>("/service", cb)
SERVICE_PATTERN = re.compile(
    r'create_service\s*<\s*([\w:]+)\s*>\s*\(\s*"([^"]+)"\s*,'
)

def extract_short_type(full_type: str) -> str:
    """Extract short type name from full qualified type e.g. std_msgs::msg::String -> String"""
    return full_type.split('::')[-1]

def parse_cpp_file(filepath: str) -> list[ROS2Node]:
    """Parse a C++ file and extract ROS2 nodes."""
    with open(filepath, 'r', errors='ignore') as f:
        source = f.read()

    # check if this file uses rclcpp at all — skip if not
    if 'rclcpp' not in source:
        return []

    nodes = []

    # find all classes that extend rclcpp::Node
    class_matches = list(CLASS_PATTERN.finditer(source))

    if not class_matches:
        return []

    for i, class_match in enumerate(class_matches):
        class_name = class_match.group(1)

        # get the source chunk for this class
        start = class_match.start()
        end = class_matches[i + 1].start() if i + 1 < len(class_matches) else len(source)
        class_source = source[start:end]

        ros_node = ROS2Node(
            name=f"unknown_{class_name}",
            file=filepath
        )

        # extract node name from Node("name")
        name_match = NODE_NAME_PATTERN.search(class_source)
        if name_match:
            ros_node.name = name_match.group(1)

        # extract publishers — hardcoded topics
        for match in PUBLISHER_PATTERN.finditer(class_source):
            msg_type = extract_short_type(match.group(1))
            topic = match.group(2)
            ros_node.publishers.append(
                Publisher(topic=topic, msg_type=msg_type)
            )

        # extract publishers — dynamic topics
        already_matched = {m.group(2) for m in PUBLISHER_PATTERN.finditer(class_source)}
        for match in PUBLISHER_DYNAMIC_PATTERN.finditer(class_source):
            topic_var = match.group(2)
            if topic_var not in already_matched and topic_var != 'this':
                msg_type = extract_short_type(match.group(1))
                ros_node.publishers.append(
                    Publisher(topic='[dynamic]', msg_type=msg_type, dynamic=True)
                )

        # extract subscriptions — hardcoded topics
        for match in SUBSCRIPTION_PATTERN.finditer(class_source):
            msg_type = extract_short_type(match.group(1))
            topic = match.group(2)
            ros_node.subscribers.append(
                Subscriber(topic=topic, msg_type=msg_type)
            )

        # extract subscriptions — dynamic topics
        already_matched = {m.group(2) for m in SUBSCRIPTION_PATTERN.finditer(class_source)}
        for match in SUBSCRIPTION_DYNAMIC_PATTERN.finditer(class_source):
            topic_var = match.group(2)
            if topic_var not in already_matched and topic_var != 'this':
                msg_type = extract_short_type(match.group(1))
                ros_node.subscribers.append(
                    Subscriber(topic='[dynamic]', msg_type=msg_type, dynamic=True)
                )

        # extract services
        for match in SERVICE_PATTERN.finditer(class_source):
            srv_type = extract_short_type(match.group(1))
            name = match.group(2)
            ros_node.services.append(
                Service(name=name, srv_type=srv_type)
            )

        nodes.append(ros_node)

    return nodes

def scan_cpp_files(path: str) -> list[ROS2Node]:
    """Recursively scan a directory for C++ ROS2 nodes."""
    all_nodes = []

    SKIP_DIRS = {
        'build', 'install', 'log', '__pycache__', '.git',
        'test', 'tests', 'launch', 'doc', 'docs'
    }

    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

        for file in files:
            if not file.endswith(('.cpp', '.cxx', '.cc', '.hpp', '.h')):
                continue

            filepath = os.path.join(root, file)
            print(f"  scanning {filepath}")
            nodes = parse_cpp_file(filepath)
            all_nodes.extend(nodes)

    return all_nodes

if __name__ == '__main__':
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else '.'
    print(f"scanning {path} for C++ nodes...\n")
    nodes = scan_cpp_files(path)
    print(f"\nfound {len(nodes)} C++ node(s):\n")
    for node in nodes:
        print(f"  [{node.name}] in {os.path.basename(node.file)}")
        for pub in node.publishers:
            print(f"    publishes  -> {pub.topic} ({pub.msg_type})")
        for sub in node.subscribers:
            print(f"    subscribes -> {sub.topic} ({sub.msg_type})")
        for srv in node.services:
            print(f"    service    -> {srv.name} ({srv.srv_type})")
