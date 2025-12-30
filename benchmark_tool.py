import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import speedtest
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import datetime
import statistics

class NetworkBenchmarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Network Benchmark Tool")
        self.root.geometry("1000x800")

        self.is_running = False
        self.results_download = []
        self.results_upload = []
        self.stops_event = threading.Event()
        self.num_runs = 20

        self.setup_ui()

    def setup_ui(self):
        # Top Control Frame
        control_frame = ttk.Frame(self.root, padding="10")
        control_frame.pack(fill=tk.X)

        self.start_btn = ttk.Button(control_frame, text=f"Start Benchmark ({self.num_runs} Runs)", command=self.start_benchmark)
        self.start_btn.pack(side=tk.LEFT, padx=5)

        self.stop_btn = ttk.Button(control_frame, text="Stop", command=self.stop_benchmark, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)

        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(control_frame, variable=self.progress_var, maximum=self.num_runs)
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        self.status_label = ttk.Label(control_frame, text="Ready")
        self.status_label.pack(side=tk.RIGHT)

        # Statistics Frame
        stats_frame = ttk.LabelFrame(self.root, text="Statistics", padding="10")
        stats_frame.pack(fill=tk.X, padx=10, pady=5)

        # Grid layout for stats
        stats_frame.columnconfigure(1, weight=1)
        stats_frame.columnconfigure(3, weight=1)
        
        ttk.Label(stats_frame, text="Download (Mbps)").grid(row=0, column=1, sticky="ew")
        ttk.Label(stats_frame, text="Upload (Mbps)").grid(row=0, column=3, sticky="ew")

        ttk.Label(stats_frame, text="Highest:").grid(row=1, column=0, sticky="e")
        self.high_down_lbl = ttk.Label(stats_frame, text="-")
        self.high_down_lbl.grid(row=1, column=1, sticky="w")
        
        ttk.Label(stats_frame, text="Highest:").grid(row=1, column=2, sticky="e")
        self.high_up_lbl = ttk.Label(stats_frame, text="-")
        self.high_up_lbl.grid(row=1, column=3, sticky="w")

        ttk.Label(stats_frame, text="Lowest:").grid(row=2, column=0, sticky="e")
        self.low_down_lbl = ttk.Label(stats_frame, text="-")
        self.low_down_lbl.grid(row=2, column=1, sticky="w")
        
        ttk.Label(stats_frame, text="Lowest:").grid(row=2, column=2, sticky="e")
        self.low_up_lbl = ttk.Label(stats_frame, text="-")
        self.low_up_lbl.grid(row=2, column=3, sticky="w")

        ttk.Label(stats_frame, text="Average:").grid(row=3, column=0, sticky="e")
        self.avg_down_lbl = ttk.Label(stats_frame, text="-")
        self.avg_down_lbl.grid(row=3, column=1, sticky="w")

        ttk.Label(stats_frame, text="Average:").grid(row=3, column=2, sticky="e")
        self.avg_up_lbl = ttk.Label(stats_frame, text="-")
        self.avg_up_lbl.grid(row=3, column=3, sticky="w")

        # Main Content Area (Split Text and Graph)
        content_pane = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        content_pane.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Log Area
        self.log_area = scrolledtext.ScrolledText(content_pane, width=40)
        content_pane.add(self.log_area, weight=1)

        # Graph Area
        self.graph_frame = ttk.Frame(content_pane)
        content_pane.add(self.graph_frame, weight=2)

        self.setup_graph()

    def setup_graph(self):
        self.fig, self.ax = plt.subplots(figsize=(5, 4), dpi=100)
        self.ax.set_title("Network Speed over Time")
        self.ax.set_xlabel("Run #")
        self.ax.set_ylabel("Speed (Mbps)")
        self.ax.grid(True)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def log(self, message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}") # Also log to stdout
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_area.see(tk.END)

    def update_graph(self):
        self.ax.clear()
        self.ax.set_title("Network Speed over Time")
        self.ax.set_xlabel("Run #")
        self.ax.set_ylabel("Speed (Mbps)")
        self.ax.grid(True)

        runs = range(1, len(self.results_download) + 1)
        self.ax.plot(runs, self.results_download, label="Download", marker='o')
        self.ax.plot(runs, self.results_upload, label="Upload", marker='x')
        self.ax.legend()
        self.canvas.draw()

    def update_stats(self):
        if not self.results_download:
            return

        # Download Stats
        max_d = max(self.results_download)
        min_d = min(self.results_download)
        avg_d = statistics.mean(self.results_download)

        self.high_down_lbl.config(text=f"{max_d:.2f}")
        self.low_down_lbl.config(text=f"{min_d:.2f}")
        self.avg_down_lbl.config(text=f"{avg_d:.2f}")

        # Upload Stats
        max_u = max(self.results_upload)
        min_u = min(self.results_upload)
        avg_u = statistics.mean(self.results_upload)

        self.high_up_lbl.config(text=f"{max_u:.2f}")
        self.low_up_lbl.config(text=f"{min_u:.2f}")
        self.avg_up_lbl.config(text=f"{avg_u:.2f}")

    def run_benchmark(self):
        self.stops_event.clear()
        s = speedtest.Speedtest()
        
        self.log("Getting best server...")
        try:
            s.get_best_server()
            self.log(f"Found best server: {s.best['host']} located in {s.best['name']}, {s.best['country']}")
        except Exception as e:
            self.log(f"Error finding server: {e}")
            self.root.after(0, self.finish_benchmark)
            return

        for i in range(self.num_runs):
            if self.stops_event.is_set():
                break

            run_num = i + 1
            self.root.after(0, lambda r=run_num: self.status_label.config(text=f"Running Test {r}/{self.num_runs}..."))
            
            try:
                # Download
                self.root.after(0, lambda: self.log(f"Run {run_num}: Testing Download..."))
                d_speed = s.download() / 1_000_000  # Convert to Mbps
                
                if self.stops_event.is_set(): break

                # Upload
                self.root.after(0, lambda: self.log(f"Run {run_num}: Testing Upload..."))
                u_speed = s.upload() / 1_000_000  # Convert to Mbps

                self.results_download.append(d_speed)
                self.results_upload.append(u_speed)

                self.root.after(0, lambda d=d_speed, u=u_speed: self.log(f"Run {run_num} Result: D={d:.2f} Mbps, U={u:.2f} Mbps"))
                self.root.after(0, lambda r=run_num: self.progress_var.set(r))

            except Exception as e:
                self.root.after(0, lambda err=str(e): self.log(f"Error in run {run_num}: {err}"))
        
        self.root.after(0, self.update_stats)
        self.root.after(0, self.update_graph)
        self.root.after(0, self.finish_benchmark)

    def start_benchmark(self):
        if self.is_running:
            return
        
        self.is_running = True
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.results_download = []
        self.results_upload = []
        self.log_area.delete(1.0, tk.END)
        self.update_graph() # Reset graph
        
        # Reset stats
        for lbl in [self.high_down_lbl, self.low_down_lbl, self.avg_down_lbl,
                   self.high_up_lbl, self.low_up_lbl, self.avg_up_lbl]:
            lbl.config(text="-")

        threading.Thread(target=self.run_benchmark, daemon=True).start()

    def stop_benchmark(self):
        if self.is_running:
            self.stops_event.set()
            self.status_label.config(text="Stopping...")
            self.log("Stopping benchmark requested...")

    def finish_benchmark(self):
        self.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="Finished")
        self.log("Benchmark finished.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true", help="Run in test mode (1 run, auto-start)")
    parser.add_argument("--runs", type=int, default=20, help="Number of runs")
    args = parser.parse_args()

    root = tk.Tk()
    app = NetworkBenchmarkApp(root)
    
    if args.test:
        app.num_runs = 1 # Override for test
        app.progress_bar.config(maximum=1)
        app.start_btn.config(text="Start Benchmark (Test Mode)")
        # Auto-start after a short delay to ensure UI is ready
        root.after(1000, app.start_benchmark)
    elif args.runs != 20:
        app.num_runs = args.runs
        app.progress_bar.config(maximum=args.runs)
        app.start_btn.config(text=f"Start Benchmark ({args.runs} Runs)")
        
    root.mainloop()
