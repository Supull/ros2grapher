# ros2grapher

Visualize ROS2 node topology from Python and C++ source code — no robot required.

Point it at your ROS2 workspace and get an interactive graph showing how nodes, topics, services and message types connect. No ROS2 installation needed, no running system, no simulator.

<img width="1459" height="779" alt="Screenshot 2026-04-18 at 1 38 09 PM" src="https://github.com/user-attachments/assets/3ae50bd2-52ff-4fe4-b2a5-a42b950732c7" />

------------------------------------------------------------------------------------------------------------------------------------------------

<img width="1101" height="692" alt="Screenshot 2026-04-18 at 1 33 29 PM" src="https://github.com/user-attachments/assets/6e0195e8-0a27-4bb3-b613-32889b972dfe" />

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

## AI-assisted dynamic topic resolution

Some ROS2 nodes use dynamic topic names set via parameters or config files. ros2grapher flags these as [dynamic] by default. With the --ai flag, it uses Gemini AI to infer the likely topic name from surrounding code context.

Requires a free Gemini API key from https://aistudio.google.com

    export GEMINI_API_KEY=your_key_here
    ros2grapher ./src --ai

AI resolved connections are shown in orange in the graph. Confidence levels — high, medium, low — indicate how certain the resolution is.

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

- ROS2 nodes (Python classes extending Node, C++ classes extending rclcpp::Node)
- Publishers (create_publisher)
- Subscribers (create_subscription)
- Services (create_service)
- LifecycleNodes (rclcpp_lifecycle::LifecycleNode)
- Dynamic topic names flagged as [dynamic] or resolved by AI
- Orphan topics — published but never subscribed or vice versa
- Cross-language connections — C++ publisher to Python subscriber and vice versa

## Limitations

- Dynamic topic names cannot always be resolved statically
- C++ nodes with variable node names show as unknown_ClassName
- AI resolution requires a Gemini API key

## Roadmap

- [ ] GitHub Action for CI/CD
- [ ] VS Code extension
- [ ] Launch file awareness
- [ ] Action visualization

## License

MIT
