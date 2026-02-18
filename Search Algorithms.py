import tkinter as tk
from tkinter import ttk
from collections import deque
import heapq

ROWS, COLS = 20, 30
CELL_SIZE = 25

THEME = {
    'bg': '#0f172a',
    'sidebar': '#1e293b',
    'accent': '#0ea5e9',
    'text': '#f8fafc',
    'grid': '#334155',
    'wall': '#64748b',
    'start': '#10b981',
    'target': '#f43f5e',
    'explored': '#0ea5e933', 
    'frontier': '#f59e0b',
    'path': '#fbbf24',
    'explored_start': '#3b82f6',
    'explored_target': '#a855f7'
}

# Strict Movement Order: Up, Right, Bottom, Bottom-Right, Left, Top-Left
DIRS = [(-1, 0), (0, 1), (1, 0), (1, 1), (0, -1), (-1, -1)]

class SearchState:
    def __init__(self):
        self.reset()

    def reset(self):
        self.explored = set()
        self.frontier = set()
        self.parent = {}
        self.path = []
        self.bidirectional = False
        self.explored_start = set()
        self.explored_target = set()
        self.frontier_start = set()
        self.frontier_target = set()
        self.parent_start = {}
        self.parent_target = {}

class ModernSearchApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pathfinder Python")
        self.root.configure(bg=THEME['bg'])
        
        self.state = SearchState()
        self.walls = set()
        self.start_pos = (5, 5)
        self.target_pos = (15, 25)
        self.running = False
        self.generator = None
        self.after_id = None
        self.drag_mode = None

        self.setup_ui()
        self.draw_grid()

    def setup_ui(self):
        self.sidebar = tk.Frame(self.root, bg=THEME['sidebar'], width=240, padx=20, pady=20)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        title = tk.Label(self.sidebar, text="PATHFINDER", font=('Helvetica', 16, 'bold'), 
                         bg=THEME['sidebar'], fg=THEME['accent'])
        title.pack(pady=(0, 20))

        self.algo_var = tk.StringVar(value="BFS")
        algos = ["BFS", "DFS", "UCS", "DLS", "IDDFS", "Bidirectional"]
        for algo in algos:
            rb = tk.Radiobutton(self.sidebar, text=algo, variable=self.algo_var, value=algo,
                                bg=THEME['sidebar'], fg=THEME['text'], selectcolor=THEME['sidebar'],
                                activebackground=THEME['sidebar'], activeforeground=THEME['accent'],
                                font=('Helvetica', 10), command=self.reset_search)
            rb.pack(anchor=tk.W, pady=2)

        tk.Label(self.sidebar, text="DEPTH LIMIT (DLS/IDDFS)", font=('Helvetica', 8, 'bold'), 
                 bg=THEME['sidebar'], fg=THEME['grid']).pack(pady=(20, 5))
        self.limit_scale = tk.Scale(self.sidebar, from_=1, to=200, orient=tk.HORIZONTAL,
                                     bg=THEME['sidebar'], fg=THEME['text'], highlightthickness=0,
                                     troughcolor=THEME['grid'], activebackground=THEME['accent'])
        self.limit_scale.set(30)
        self.limit_scale.pack(fill=tk.X)

        self.btn_run = tk.Button(self.sidebar, text="VISUALIZE", font=('Helvetica', 10, 'bold'),
                                 bg=THEME['accent'], fg='white', relief=tk.FLAT, pady=10,
                                 command=self.toggle_search)
        self.btn_run.pack(fill=tk.X, pady=(30, 10))

        tk.Button(self.sidebar, text="RESET GRID", font=('Helvetica', 10, 'bold'),
                  bg=THEME['grid'], fg='white', relief=tk.FLAT, pady=5,
                  command=self.full_reset).pack(fill=tk.X)

        self.status_lbl = tk.Label(self.sidebar, text="READY", font=('Helvetica', 9, 'italic'),
                                   bg=THEME['sidebar'], fg=THEME['grid'])
        self.status_lbl.pack(side=tk.BOTTOM, pady=10)

        self.canvas = tk.Canvas(self.root, width=COLS*CELL_SIZE, height=ROWS*CELL_SIZE,
                                bg=THEME['bg'], highlightthickness=0)
        self.canvas.pack(side=tk.RIGHT, padx=40, pady=40)

        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)

    def draw_grid(self):
        self.canvas.delete("all")
        for r in range(ROWS):
            for c in range(COLS):
                x1, y1 = c * CELL_SIZE, r * CELL_SIZE
                x2, y2 = x1 + CELL_SIZE, y1 + CELL_SIZE
                
                color = THEME['bg']
                outline = THEME['grid']
                
                if (r, c) == self.start_pos: color = THEME['start']
                elif (r, c) == self.target_pos: color = THEME['target']
                elif (r, c) in self.walls: color = THEME['wall']
                elif (r, c) in self.state.path: color = THEME['path']
                elif self.state.bidirectional:
                    if (r, c) in self.state.explored_start: color = THEME['explored_start']
                    elif (r, c) in self.state.explored_target: color = THEME['explored_target']
                    elif (r, c) in self.state.frontier_start: color = THEME['grid']
                    elif (r, c) in self.state.frontier_target: color = THEME['grid']
                else:
                    if (r, c) in self.state.explored: color = '#1e293b' 
                    elif (r, c) in self.state.frontier: color = THEME['frontier']

                self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline=outline, width=0.5)

    def on_canvas_click(self, event):
        if self.running: return
        r, c = event.y // CELL_SIZE, event.x // CELL_SIZE
        if not (0 <= r < ROWS and 0 <= c < COLS): return
        
        if (r, c) == self.start_pos: self.drag_mode = "START"
        elif (r, c) == self.target_pos: self.drag_mode = "TARGET"
        else:
            self.drag_mode = "WALL"
            self.toggle_wall(r, c)

    def on_canvas_drag(self, event):
        if self.running or not self.drag_mode: return
        r, c = event.y // CELL_SIZE, event.x // CELL_SIZE
        if not (0 <= r < ROWS and 0 <= c < COLS): return

        if self.drag_mode == "START":
            if (r, c) != self.target_pos and (r, c) not in self.walls:
                self.start_pos = (r, c)
        elif self.drag_mode == "TARGET":
            if (r, c) != self.start_pos and (r, c) not in self.walls:
                self.target_pos = (r, c)
        elif self.drag_mode == "WALL":
            if (r, c) not in (self.start_pos, self.target_pos):
                self.walls.add((r, c))
        self.draw_grid()

    def on_mouse_release(self, event):
        self.drag_mode = None

    def toggle_wall(self, r, c):
        if (r, c) in self.walls: self.walls.remove((r, c))
        else: self.walls.add((r, c))
        self.draw_grid()

    def get_neighbors(self, r, c):
        nbs = []
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS and (nr, nc) not in self.walls:
                nbs.append((nr, nc))
        return nbs

    def bfs(self):
        queue = deque([self.start_pos])
        self.state.frontier = {self.start_pos}
        self.state.parent = {self.start_pos: None}
        while queue:
            curr = queue.popleft()
            if curr == self.target_pos:
                self.reconstruct_path(self.state.parent, curr)
                return
            self.state.explored.add(curr)
            for nb in self.get_neighbors(*curr):
                if nb not in self.state.explored and nb not in self.state.frontier:
                    self.state.parent[nb] = curr
                    self.state.frontier.add(nb)
                    queue.append(nb)
            yield

    def dfs(self):
        stack = [self.start_pos]
        self.state.parent = {self.start_pos: None}
        while stack:
            curr = stack.pop()
            if curr == self.target_pos:
                self.reconstruct_path(self.state.parent, curr)
                return
            if curr in self.state.explored: continue
            self.state.explored.add(curr)
            for nb in self.get_neighbors(*curr):
                if nb not in self.state.explored:
                    self.state.parent[nb] = curr
                    stack.append(nb)
                    self.state.frontier.add(nb)
            yield

    def ucs(self):
        pq = [(0, self.start_pos)]
        self.state.parent = {self.start_pos: None}
        costs = {self.start_pos: 0}
        while pq:
            cost, curr = heapq.heappop(pq)
            if curr in self.state.explored: continue
            if curr == self.target_pos:
                self.reconstruct_path(self.state.parent, curr)
                return
            self.state.explored.add(curr)
            for nb in self.get_neighbors(*curr):
                step = 2 if abs(nb[0]-curr[0]) + abs(nb[1]-curr[1]) == 2 else 1
                new_cost = cost + step
                if nb not in costs or new_cost < costs[nb]:
                    costs[nb] = new_cost
                    self.state.parent[nb] = curr
                    heapq.heappush(pq, (new_cost, nb))
                    self.state.frontier.add(nb)
            yield

    def dls(self, limit):
        stack = [(self.start_pos, 0)]
        self.state.parent = {self.start_pos: None}
        self.state.explored = set()
        self.state.frontier = {self.start_pos}
        while stack:
            curr, depth = stack.pop()
            if curr == self.target_pos:
                self.reconstruct_path(self.state.parent, curr)
                return
            self.state.explored.add(curr)
            if depth < limit:
                for nb in self.get_neighbors(*curr):
                    if nb not in self.state.explored:
                        self.state.parent[nb] = curr
                        stack.append((nb, depth + 1))
                        self.state.frontier.add(nb)
            yield

    def iddfs(self, max_limit):
        for limit in range(max_limit + 1):
            self.state.explored = set()
            self.state.frontier = {self.start_pos}
            self.state.parent = {self.start_pos: None}
            stack = [(self.start_pos, 0)]
            while stack:
                curr, depth = stack.pop()
                if curr == self.target_pos:
                    self.reconstruct_path(self.state.parent, curr)
                    return
                self.state.explored.add(curr)
                if depth < limit:
                    for nb in self.get_neighbors(*curr):
                        if nb not in self.state.explored:
                            self.state.parent[nb] = curr
                            stack.append((nb, depth + 1))
                            self.state.frontier.add(nb)
                yield
            if self.state.path: return

    def bidirectional(self):
        self.state.bidirectional = True
        f_start, f_target = deque([self.start_pos]), deque([self.target_pos])
        self.state.parent_start = {self.start_pos: None}
        self.state.parent_target = {self.target_pos: None}
        self.state.frontier_start = {self.start_pos}
        self.state.frontier_target = {self.target_pos}
        
        while f_start and f_target:
            if f_start:
                curr = f_start.popleft()
                self.state.explored_start.add(curr)
                if curr in self.state.explored_target:
                    self.reconstruct_bidi(curr)
                    return
                for nb in self.get_neighbors(*curr):
                    if nb not in self.state.explored_start and nb not in self.state.frontier_start:
                        self.state.parent_start[nb] = curr
                        f_start.append(nb)
                        self.state.frontier_start.add(nb)
            yield
            if f_target:
                curr = f_target.popleft()
                self.state.explored_target.add(curr)
                if curr in self.state.explored_start:
                    self.reconstruct_bidi(curr)
                    return
                for nb in self.get_neighbors(*curr):
                    if nb not in self.state.explored_target and nb not in self.state.frontier_target:
                        self.state.parent_target[nb] = curr
                        f_target.append(nb)
                        self.state.frontier_target.add(nb)
            yield

    def reconstruct_path(self, parent_map, curr):
        while curr:
            self.state.path.append(curr)
            curr = parent_map[curr]

    def reconstruct_bidi(self, meet):
        p1, p2 = [], []
        curr = meet
        while curr:
            p1.append(curr)
            curr = self.state.parent_start.get(curr)
        curr = self.state.parent_target.get(meet)
        if curr:
            while curr:
                p2.append(curr)
                curr = self.state.parent_target.get(curr)
        self.state.path = p1[::-1] + p2

    def step(self):
        if not self.running: return
        try:
            next(self.generator)
            self.draw_grid()
            ms = 30 # Fixed visual delay
            self.after_id = self.root.after(ms, self.step)
        except StopIteration:
            self.running = False
            self.btn_run.config(text="VISUALIZE", bg=THEME['accent'])
            self.status_lbl.config(text="FINISHED")
            self.draw_grid()

    def toggle_search(self):
        if self.running:
            self.stop_search()
        else:
            self.start_search()

    def start_search(self):
        self.reset_search()
        self.running = True
        self.btn_run.config(text="STOP", bg=THEME['target'])
        algo = self.algo_var.get()
        self.status_lbl.config(text=f"{algo} RUNNING...")
        
        limit_val = int(self.limit_scale.get())
        
        if algo == "BFS": self.generator = self.bfs()
        elif algo == "DFS": self.generator = self.dfs()
        elif algo == "UCS": self.generator = self.ucs()
        elif algo == "DLS": self.generator = self.dls(limit=limit_val)
        elif algo == "IDDFS": self.generator = self.iddfs(max_limit=limit_val)
        elif algo == "Bidirectional": self.generator = self.bidirectional()
        self.step()

    def stop_search(self):
        self.running = False
        if self.after_id: self.root.after_cancel(self.after_id)
        self.btn_run.config(text="VISUALIZE", bg=THEME['accent'])
        self.status_lbl.config(text="STOPPED")

    def reset_search(self):
        self.stop_search()
        self.state.reset()
        self.draw_grid()
        self.status_lbl.config(text="READY")

    def full_reset(self):
        self.walls.clear()
        self.reset_search()

if __name__ == "__main__":
    root = tk.Tk()
    root.resizable(False, False)
    app = ModernSearchApp(root)
    root.mainloop()
