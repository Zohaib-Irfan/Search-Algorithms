Pathfinder Visualizer

A modern, dark-themed Python application built with tkinter to visualize various uninformed search algorithms. This tool allows users to interactively build walls, move start/target points, and observe how different pathfinding strategies navigate a grid using a specific clockwise movement order.

🚀 Key Features

Interactive Grid: Drag the Start (Green) and Target (Red) nodes to reposition them instantly.

Dynamic Wall Building: Click and drag on the grid to paint obstacles in real-time.

Visual Search Progress: Watch as the algorithms explore nodes and establish the frontier before finalizing the path.

Custom Depth Control: A dedicated slider allows you to set the search depth for limit-based algorithms (DLS and IDDFS).

🧭 Strict Movement Logic

To ensure consistent tie-breaking and deterministic behavior, the search engine expands neighbors in a strict clockwise order using the Main Diagonal:

Up (-1, 0)

Right (0, 1)

Bottom (1, 0)

Bottom-Right (1, 1) (Diagonal)

Left (0, -1)

Top-Left (-1, -1) (Diagonal)

🧠 Supported Search Algorithms

1. Breadth-First Search (BFS)

Guarantees the shortest path in unweighted grids by exploring level by level.

2. Depth-First Search (DFS)

Explores as far as possible along each branch before backtracking; memory efficient but non-optimal.

3. Uniform-Cost Search (UCS)

Optimal pathfinding using edge costs:

Cardinal Movement: 1 unit

Diagonal Movement: 2 units

4. Depth-Limited Search (DLS)

Prevents DFS from getting stuck in infinite paths by imposing a hard limit on depth.

5. Iterative Deepening DFS (IDDFS)

Combines the completeness of BFS with the memory efficiency of DFS by gradually increasing the depth limit.

6. Bidirectional Search

Runs two simultaneous searches from the start and target, significantly reducing the search space.

🛠️ Installation & Execution

This project is built using standard Python libraries, requiring no external dependencies like pygame.

Clone the repository:

git clone https://github.com/Zohaib-Irfan/Search-Algorithms/


Python Version: Ensure you have Python 3.8 or higher installed.

Run the App:

python search visualizer.py
