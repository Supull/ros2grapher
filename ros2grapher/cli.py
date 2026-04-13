import argparse
import os
import sys
import threading
import http.server
import socketserver
from ros2grapher.parser import scan_workspace_all as scan_workspace
from ros2grapher.graph import build_graph, print_graph
from ros2grapher.renderer import render

def serve(directory, port=8888):
    handler = http.server.SimpleHTTPRequestHandler
    handler.log_message = lambda *args: None
    os.chdir(directory)
    with socketserver.TCPServer(("", port), handler) as httpd:
        httpd.serve_forever()

def main():
    parser = argparse.ArgumentParser(
        prog='ros2grapher',
        description='Visualize ROS2 node topology from source code — no robot required.'
    )
    parser.add_argument(
        'workspace',
        nargs='?',
        default='.',
        help='path to your ROS2 workspace or package (default: current directory)'
    )
    parser.add_argument(
        '--output', '-o',
        default='index.html',
        help='output HTML file (default: index.html)'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8888,
        help='port to serve graph on (default: 8888)'
    )
    parser.add_argument(
        '--no-serve',
        action='store_true',
        help='do not serve graph, just generate the HTML file'
    )
    parser.add_argument(
        '--print',
        action='store_true',
        help='print graph to terminal instead of rendering HTML'
    )

    args = parser.parse_args()

    workspace = os.path.abspath(args.workspace)

    if not os.path.isdir(workspace):
        print(f"error: '{workspace}' is not a directory")
        sys.exit(1)

    print(f"ros2grapher scanning {workspace}...\n")

    nodes = scan_workspace(workspace)

    if not nodes:
        print("no ROS2 nodes found.")
        sys.exit(0)

    graph = build_graph(nodes)

    if args.print:
        print_graph(graph)
        return

    output = os.path.abspath(args.output)
    output_dir = os.path.dirname(output)

    render(graph, workspace, output)

    print(f"\n  nodes:   {len(graph.nodes)}")
    print(f"  topics:  {len(graph.topics)}")
    print(f"  orphans: {len(graph.orphan_topics)}")

    if not args.no_serve:
        print(f"\n  serving at http://localhost:{args.port}")
        print(f"  press Ctrl+C to stop\n")
        thread = threading.Thread(target=serve, args=(output_dir, args.port), daemon=True)
        thread.start()
        try:
            thread.join()
        except KeyboardInterrupt:
            print("\n  stopped.")

if __name__ == '__main__':
    main()
