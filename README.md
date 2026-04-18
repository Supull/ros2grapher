# ros2grapher

Visualize ROS2 node topology from Python and C++ source code — no robot required.

Point it at your ROS2 workspace and get an interactive graph showing how nodes, topics, services and message types connect. No ROS2 installation needed, no running system, no simulator.

<img width="1459" height="779" alt="Screenshot 2026-04-18 at 1 38 09 PM" src="https://github.com/user-attachments/assets/5bd93465-6b45-43b0-8217-f5b0ca8951b6" />

------------------------------------------------------------------------------------------------------------------------------------------------

<img width="1101" height="692" alt="Screenshot 2026-04-18 at 1 33 29 PM" src="https://github.com/user-attachments/assets/01b173b8-4194-40ea-a3ee-0d483727f402" />

## Why

Every existing ROS2 visualization tool requires a live running system. If you just cloned a repo, you are doing code review, or you are in CI — none of those tools work.

ros2grapher reads your source files directly using static analysis and builds the graph without executing anything.

|                        | ros2grapher | rqt_graph | ros_network_viz |
|------------------------|-------------|-----------|-----------------|
| Requires ROS2 running  | no          | yes       | yes             |
| Works on cloned repos  | yes         | no        | no              |
| Works in CI/CD         | yes         | no        | no              |
| Supports C++ nodes     | yes         | yes       | yes             |
| No install needed      | yes         | no        | no              |

## Install

    git clone https://github.com/Supull/ros2grapher.git
    cd ros2grapher
    pip install -e .

## Usage

    ros2grapher /path/to/your/ros2_ws

Then open http://localhost:8888 in your browser.

## Options

    ros2grapher ./src                  # scan a specific folder
    ros2grapher ./src --ai             # use AI to resolve dynamic topics
    ros2grapher ./src --port 9000      # use a different port
    ros2grapher ./src --no-serve       # just generate index.html
    ros2grapher ./src --print          # print graph to terminal

## How it works

ros2grapher uses two layers of analysis:

**Layer 1 — Static analysis (always runs)**

Walks your workspace and parses every Python and C++ source file using Python AST parsing and regex pattern matching. It looks for:

- Python classes extending Node or C++ classes extending rclcpp::Node or rclcpp_lifecycle::LifecycleNode
- create_publisher calls to extract topic names and message types
- create_subscription calls to extract topic names and message types
- create_service calls to extract service names and types
- Cross-package topic matching — a publisher in one package connects to a subscriber in another if they share the same topic name

Hardcoded topic names are resolved with full certainty and shown in green. Topics that cannot be resolved statically are flagged as [dynamic].

**Layer 2 — AI resolution (optional, requires --ai flag)**

When a topic name is stored in a variable or comes from a parameter, static analysis cannot determine it. With --ai, ros2grapher sends the source file to Gemini AI with a structured prompt asking it to determine the topic name from context — for example by reading the default value passed to declare_parameter.

Each AI resolution comes with a confidence score:
- High — topic found directly in a declare_parameter default value
- Medium — inferred from variable names, class names, or context
- Low — best guess from surrounding code

AI resolved connections are shown in orange in the graph so you always know what is certain and what is inferred.

## AI-assisted dynamic topic resolution

Requires a free Gemini API key from https://aistudio.google.com

    export GEMINI_API_KEY=your_key_here
    ros2grapher ./src --ai

## Visual output

- Blue circles — ROS2 nodes
- Green ellipses — topics (statically certain)
- Orange ellipses — topics (AI resolved)
- Red dashed ellipses — orphan topics (no publisher or no subscriber)
- Orange rectangles — services
- Dashed colored borders — package groups
- node to topic arrow — node publishes to that topic
- topic to node arrow — node subscribes to that topic
- Orange line — connection resolved by AI

Hover over any node or topic to see details. Drag to rearrange. Scroll to zoom. Drag a package border to move the whole group.

## What it detects

- ROS2 nodes — Python classes extending Node, C++ classes extending rclcpp::Node
- LifecycleNodes — rclcpp_lifecycle::LifecycleNode
- Publishers — create_publisher
- Subscribers — create_subscription
- Services — create_service
- Dynamic topic names — flagged as [dynamic] or resolved by AI with confidence score
- Orphan topics — published but never subscribed or vice versa
- Cross-language connections — C++ publisher to Python subscriber and vice versa
- Package grouping — nodes grouped visually by their ROS2 package

## Limitations

- Dynamic topic names cannot always be resolved statically
- C++ nodes with variable node names show as unknown_ClassName
- AI resolution requires a free Gemini API key
- AI resolution is slower on large workspaces due to API rate limits

## Roadmap

- [ ] GitHub Action for CI/CD
- [ ] VS Code extension
- [ ] Launch file awareness
- [ ] Action visualization

## License

MIT
