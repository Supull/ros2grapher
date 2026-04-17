# ros2grapher

Visualize ROS2 node topology from Python source code with no robot required.

Point it at your ROS2 workspace and get an interactive graph showing how nodes, topics and message types connect. No ROS2 installation needed, no running system, no simulator.

<img width="1461" height="779" alt="Screenshot 2026-04-17 at 12 49 49 AM" src="https://github.com/user-attachments/assets/e324f9d0-e33f-4b7d-9fc6-ee9ced975af2" />

## Why

Every existing ROS2 visualization tool requires a live running system. If you just cloned a repo, you're doing code review, or you're in CI. None of those tools work.

ros2grapher reads your Python source files directly using static analysis and builds the graph without executing anything.

|                        | ros2grapher | rqt_graph | ros_network_viz |
|------------------------|-------------|-----------|-----------------|
| Requires ROS2 running  | no          | yes       | yes             |
| Works on cloned repos  | yes         | no        | no              |
| Works in CI/CD         | yes         | no        | no              |
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
    ros2grapher ./src --port 9000      # use a different port
    ros2grapher ./src --no-serve       # just generate index.html
    ros2grapher ./src --print          # print graph to terminal

## How it works

    .py source files
          |
      AST parser — extracts nodes, publishers, subscribers, services
          |
      graph builder — matches topics across files, detects orphans
          |
      D3.js visualization — interactive, draggable, color coded

## What it detects

- ROS2 nodes (classes extending Node)
- Publishers (create_publisher)
- Subscribers (create_subscription)
- Services (create_service)
- Dynamic topic names flagged as [dynamic]
- Orphan topics — published but never subscribed or vice versa

## Visual output

- Blue circles — ROS2 nodes
- Green ellipses — connected topics
- Red dashed ellipses — orphan topics (no publisher or no subscriber)

Hover over any node or topic to see details. Drag to rearrange. Scroll to zoom.

## Limitations

- Python nodes only (C++ support planned)
- Dynamic topic names cannot always be resolved statically

## Roadmap

- [ ] C++ node support
- [ ] AI-assisted dynamic topic resolution
- [ ] VS Code extension
- [ ] GitHub Action for CI/CD

## License

MIT
