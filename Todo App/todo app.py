"""
Daily Life Tracker
------------------
A Tkinter desktop app to plan your day, punish yourself for unfinished tasks,
record strengths / weaknesses, score different areas of your life with charts,
and export everything into a single CSV report.

Requirements: numpy, matplotlib   (pip install numpy matplotlib)
"""

import csv
import json
import os
import tkinter as tk
from datetime import date, datetime
from tkinter import filedialog, messagebox, ttk

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# --------------------------------------------------------------------------- #
# Constants
# --------------------------------------------------------------------------- #
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "todo_data.json")
DATE_FMT = "%Y-%m-%d"
TIME_FMT = "%H:%M"
FIELDS = ["family", "education", "spiritual", "sport", "work"]

BG = "#1e1b2e"
CARD = "#2a2640"
CARD_LIGHT = "#37325a"
ACCENT = "#8b5cf6"
ACCENT_DARK = "#6d28d9"
TEXT = "#f1f5f9"
MUTED = "#a1a1c5"
GREEN = "#22c55e"
RED = "#ef4444"
AMBER = "#f59e0b"
BLUE = "#3b82f6"

FONT = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")


def today():
    return date.today().strftime(DATE_FMT)


def now_time():
    return datetime.now().strftime(TIME_FMT)


def normalize_time(text):
    """Return 'HH:MM' (zero-padded), '' if empty, or None if the text is invalid."""
    text = text.strip()
    if not text:
        return ""
    try:
        return datetime.strptime(text, TIME_FMT).strftime(TIME_FMT)
    except ValueError:
        return None


def is_overdue(task):
    """A task is overdue if it's unfinished and its finish time has passed."""
    if task["done"] or normalize_time(task["end"]) in (None, ""):
        return False
    if task["created"] < today():
        return True
    return task["end"] < now_time()


# --------------------------------------------------------------------------- #
# Storage layer (everything lives in one JSON file)
# --------------------------------------------------------------------------- #
class Storage:
    def __init__(self, path=DATA_FILE):
        self.path = path
        self.data = {"tasks": [], "days": {}, "next_id": 1}
        self.load()

    def load(self):
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                self.data.update(json.load(f))
        except (json.JSONDecodeError, OSError):
            messagebox.showwarning(
                "Data file problem",
                "Could not read the data file. Starting with an empty list.",
            )

    def save(self):
        # Write to a temp file first so a crash can never corrupt the real data.
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=4)
        os.replace(tmp, self.path)

    # ---- tasks ----
    @property
    def tasks(self):
        return self.data["tasks"]

    def add_task(self, title, start, end):
        task = {
            "id": self.data["next_id"],
            "title": title,
            "done": False,
            "start": start,
            "end": end,
            "created": today(),
            "punishment": "",
            "served": False,
        }
        self.data["next_id"] += 1
        self.tasks.append(task)
        self.save()
        return task

    def get_task(self, task_id):
        return next((t for t in self.tasks if t["id"] == task_id), None)

    def delete_task(self, task_id):
        self.data["tasks"] = [t for t in self.tasks if t["id"] != task_id]
        self.save()

    # ---- per-day reflection ----
    def day(self, day_str):
        return self.data["days"].setdefault(
            day_str, {"strengths": [], "weaknesses": [], "scores": {}}
        )

    # ---- CSV report ----
    def report_rows(self):
        rows = []
        for t in self.tasks:
            if t["done"]:
                status = "Done"
            elif t["served"]:
                status = "Not done - punishment served"
            else:
                status = "Not done"
            rows.append([t["created"], "Task", t["title"], status,
                         t["start"], t["end"], t["punishment"]])
        for d in sorted(self.data["days"]):
            info = self.data["days"][d]
            for s in info.get("strengths", []):
                rows.append([d, "Strength", s, "", "", "", ""])
            for w in info.get("weaknesses", []):
                rows.append([d, "Weakness", w, "", "", "", ""])
            for field, value in info.get("scores", {}).items():
                rows.append([d, "Score", field, value, "", "", ""])
        return rows


# --------------------------------------------------------------------------- #
# Styling
# --------------------------------------------------------------------------- #
def setup_style(root):
    s = ttk.Style(root)
    s.theme_use("clam")

    s.configure(".", background=BG, foreground=TEXT, font=FONT)
    s.configure("TFrame", background=BG)
    s.configure("TLabel", background=BG, foreground=TEXT)
    s.configure("Muted.TLabel", foreground=MUTED)
    s.configure("Title.TLabel", font=("Segoe UI", 18, "bold"))

    s.configure("TNotebook", background=BG, borderwidth=0)
    s.configure("TNotebook.Tab", background=CARD, foreground=MUTED,
                padding=(18, 8), font=FONT_BOLD, borderwidth=0)
    s.map("TNotebook.Tab",
          background=[("selected", ACCENT)],
          foreground=[("selected", "white")])

    s.configure("Treeview", background=CARD, fieldbackground=CARD,
                foreground=TEXT, rowheight=30, borderwidth=0)
    s.configure("Treeview.Heading", background=ACCENT_DARK, foreground="white",
                font=FONT_BOLD, relief="flat", padding=6)
    s.map("Treeview", background=[("selected", ACCENT)])
    s.map("Treeview.Heading", background=[("active", ACCENT)])

    s.configure("TEntry", fieldbackground=CARD_LIGHT, foreground=TEXT,
                insertcolor=TEXT, padding=6, borderwidth=0)
    s.configure("Vertical.TScrollbar", background=CARD_LIGHT, troughcolor=CARD,
                borderwidth=0, arrowcolor=TEXT)

    buttons = {
        "Accent": (ACCENT, ACCENT_DARK),
        "Success": (GREEN, "#16a34a"),
        "Danger": (RED, "#dc2626"),
        "Warning": (AMBER, "#d97706"),
        "Info": (BLUE, "#2563eb"),
    }
    for name, (base, hover) in buttons.items():
        s.configure(f"{name}.TButton", background=base, foreground="white",
                    font=FONT_BOLD, padding=(14, 7), borderwidth=0, focuscolor=base)
        s.map(f"{name}.TButton", background=[("active", hover)])


# --------------------------------------------------------------------------- #
# Add-task dialog
# --------------------------------------------------------------------------- #
class TaskDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("New task")
        self.configure(bg=BG, padx=24, pady=20)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.result = None

        specs = [
            ("title", "Task", ""),
            ("start", "Start time (HH:MM)", now_time()),
            ("end", "Finish time (HH:MM)", ""),
        ]
        self.vars = {}
        for row, (key, label, default) in enumerate(specs):
            ttk.Label(self, text=label).grid(row=row, column=0, sticky="w", pady=6)
            var = tk.StringVar(value=default)
            entry = ttk.Entry(self, textvariable=var, width=34)
            entry.grid(row=row, column=1, padx=(14, 0), pady=6)
            if row == 0:
                entry.focus_set()
            self.vars[key] = var

        bar = ttk.Frame(self)
        bar.grid(row=len(specs), column=0, columnspan=2, pady=(14, 0))
        ttk.Button(bar, text="Add", style="Success.TButton",
                   command=self._submit).pack(side="left", padx=6)
        ttk.Button(bar, text="Cancel", style="Danger.TButton",
                   command=self.destroy).pack(side="left", padx=6)

        self.bind("<Return>", lambda _e: self._submit())
        self.bind("<Escape>", lambda _e: self.destroy())
        self.wait_window(self)

    def _submit(self):
        title = self.vars["title"].get().strip()
        start = normalize_time(self.vars["start"].get())
        end = normalize_time(self.vars["end"].get())

        if not title:
            messagebox.showwarning("Missing title", "Please enter a task.", parent=self)
            return
        if start is None or end is None:
            messagebox.showerror("Invalid time",
                                 "Use the 24-hour format HH:MM, e.g. 08:30 or 17:45.",
                                 parent=self)
            return
        if start and end and end <= start:
            messagebox.showerror("Invalid range",
                                 "Finish time must be after the start time.", parent=self)
            return
        self.result = (title, start, end)
        self.destroy()


# --------------------------------------------------------------------------- #
# Main application
# --------------------------------------------------------------------------- #
class TodoApp:
    def __init__(self, root):
        self.root = root
        self.store = Storage()
        self.canvas = None

        root.title("Daily Life Tracker")
        root.geometry("900x640")
        root.minsize(840, 580)
        root.configure(bg=BG)
        setup_style(root)

        header = ttk.Frame(root)
        header.pack(fill="x", padx=24, pady=(18, 8))
        ttk.Label(header, text="🌙 Daily Life Tracker", style="Title.TLabel").pack(side="left")
        self.summary_var = tk.StringVar()
        ttk.Label(header, textvariable=self.summary_var,
                  style="Muted.TLabel").pack(side="right")

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        self._build_tasks_tab()
        self._build_punish_tab()
        self._build_reflection_tab()
        self._build_charts_tab()

        self.refresh_all()

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _make_tab(self, title):
        tab = ttk.Frame(self.notebook, padding=16)
        self.notebook.add(tab, text=title)
        return tab

    def _make_tree(self, parent, columns, widths, left_cols=("Task", "Punishment")):
        frame = ttk.Frame(parent)
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        for col, width in zip(columns, widths):
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor="w" if col in left_cols else "center")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        return tree

    def _selected_task(self, tree):
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("No selection", "Please select a task first.")
            return None
        return self.store.get_task(int(selection[0]))

    # ------------------------------------------------------------------ #
    # Tab 1: Today's programme
    # ------------------------------------------------------------------ #
    def _build_tasks_tab(self):
        tab = self._make_tab("📋  Today's Program")
        self.task_tree = self._make_tree(
            tab, ("Task", "Completed", "Start Time", "Finish Time"), (380, 110, 130, 130)
        )
        self.task_tree.tag_configure("done", foreground=GREEN)
        self.task_tree.tag_configure("overdue", foreground=RED)

        bar = ttk.Frame(tab)
        bar.pack(pady=(14, 0))
        for text, style, cmd in [
            ("＋ Add Task", "Success.TButton", self.add_task),
            ("✔ Toggle Done", "Warning.TButton", self.toggle_done),
            ("🗑 Delete", "Danger.TButton", self.delete_task),
            ("⭳ Export CSV", "Info.TButton", self.export_csv),
        ]:
            ttk.Button(bar, text=text, style=style, command=cmd).pack(side="left", padx=6)

    def add_task(self):
        result = TaskDialog(self.root).result
        if result:
            self.store.add_task(*result)
            self.refresh_all()

    def toggle_done(self):
        task = self._selected_task(self.task_tree)
        if task:
            task["done"] = not task["done"]
            self.store.save()
            self.refresh_all()

    def delete_task(self):
        task = self._selected_task(self.task_tree)
        if task and messagebox.askyesno("Confirm", "Delete this task?"):
            self.store.delete_task(task["id"])
            self.refresh_all()

    def refresh_tasks(self):
        tree = self.task_tree
        tree.delete(*tree.get_children())
        for t in self.store.tasks:
            tags = ()
            if t["done"]:
                tags = ("done",)
            elif is_overdue(t):
                tags = ("overdue",)
            tree.insert(
                "", tk.END, iid=str(t["id"]), tags=tags,
                values=(t["title"], "✔ Yes" if t["done"] else "✘ No",
                        t["start"] or "—", t["end"] or "—"),
            )

    # ------------------------------------------------------------------ #
    # Tab 2: Punishments
    # ------------------------------------------------------------------ #
    def _build_punish_tab(self):
        tab = self._make_tab("😈  Punish Yourself")
        ttk.Label(tab, text="Every task you haven't finished shows up here. "
                            "Choose one and decide your punishment.",
                  style="Muted.TLabel").pack(anchor="w", pady=(0, 10))

        self.pun_tree = self._make_tree(
            tab, ("Task", "Finish Time", "Punishment", "Status"), (280, 110, 280, 100)
        )
        self.pun_tree.tag_configure("served", foreground=GREEN)
        self.pun_tree.bind("<<TreeviewSelect>>", self._fill_punishment_entry)

        form = ttk.Frame(tab)
        form.pack(fill="x", pady=(14, 0))
        ttk.Label(form, text="Punishment:").pack(side="left")
        self.pun_var = tk.StringVar()
        entry = ttk.Entry(form, textvariable=self.pun_var)
        entry.pack(side="left", fill="x", expand=True, padx=10)
        entry.bind("<Return>", lambda _e: self.save_punishment())
        ttk.Button(form, text="Commit", style="Danger.TButton",
                   command=self.save_punishment).pack(side="left", padx=4)
        ttk.Button(form, text="Mark as Served", style="Success.TButton",
                   command=self.toggle_served).pack(side="left", padx=4)

    def _fill_punishment_entry(self, _event=None):
        selection = self.pun_tree.selection()
        if selection:
            task = self.store.get_task(int(selection[0]))
            if task:
                self.pun_var.set(task["punishment"])

    def save_punishment(self):
        task = self._selected_task(self.pun_tree)
        if not task:
            return
        text = self.pun_var.get().strip()
        if not text:
            messagebox.showwarning("Empty", "Write a punishment first.")
            return
        task["punishment"] = text
        task["served"] = False
        self.store.save()
        self.refresh_all()

    def toggle_served(self):
        task = self._selected_task(self.pun_tree)
        if not task:
            return
        if not task["punishment"]:
            messagebox.showwarning("No punishment", "Commit a punishment first.")
            return
        task["served"] = not task["served"]
        self.store.save()
        self.refresh_all()

    def refresh_punishments(self):
        tree = self.pun_tree
        selected = tree.selection()
        tree.delete(*tree.get_children())
        for t in self.store.tasks:
            if t["done"]:
                continue
            if t["served"]:
                status, tags = "Served", ("served",)
            else:
                status, tags = ("Pending" if t["punishment"] else "Not set"), ()
            tree.insert(
                "", tk.END, iid=str(t["id"]), tags=tags,
                values=(t["title"], t["end"] or "—", t["punishment"] or "—", status),
            )
        if selected and tree.exists(selected[0]):
            tree.selection_set(selected[0])

    # ------------------------------------------------------------------ #
    # Tab 3: Strengths & weaknesses
    # ------------------------------------------------------------------ #
    def _build_reflection_tab(self):
        tab = self._make_tab("💪  Strengths & Weaknesses")
        ttk.Label(tab, text=f"Reflect on today ({today()}). "
                            "Entries are saved automatically and included in the CSV.",
                  style="Muted.TLabel").pack(anchor="w", pady=(0, 10))

        columns = ttk.Frame(tab)
        columns.pack(fill="both", expand=True)
        columns.columnconfigure((0, 1), weight=1, uniform="col")
        columns.rowconfigure(0, weight=1)

        self.lists = {}
        self._build_list_column(columns, 0, "✨ Strengths", "strengths", GREEN)
        self._build_list_column(columns, 1, "⚠ Weaknesses", "weaknesses", RED)

    def _build_list_column(self, parent, column, title, key, color):
        box = ttk.Frame(parent)
        box.grid(row=0, column=column, sticky="nsew", padx=8)

        tk.Label(box, text=title, bg=color, fg="white", font=FONT_BOLD,
                 pady=6).pack(fill="x")
        listbox = tk.Listbox(
            box, bg=CARD, fg=TEXT, font=("Segoe UI", 11), selectbackground=ACCENT,
            borderwidth=0, highlightthickness=0, activestyle="none",
        )
        listbox.pack(fill="both", expand=True, pady=(6, 8))
        self.lists[key] = listbox

        var = tk.StringVar()
        entry = ttk.Entry(box, textvariable=var)
        entry.pack(fill="x")
        entry.bind("<Return>", lambda _e: self._add_reflection(key, var))

        bar = ttk.Frame(box)
        bar.pack(pady=(8, 0))
        ttk.Button(bar, text="Add", style="Success.TButton",
                   command=lambda: self._add_reflection(key, var)).pack(side="left", padx=4)
        ttk.Button(bar, text="Remove", style="Danger.TButton",
                   command=lambda: self._remove_reflection(key)).pack(side="left", padx=4)

    def _add_reflection(self, key, var):
        text = var.get().strip()
        if not text:
            return
        self.store.day(today())[key].append(text)
        self.store.save()
        var.set("")
        self.refresh_reflections()

    def _remove_reflection(self, key):
        selection = self.lists[key].curselection()
        if not selection:
            messagebox.showwarning("No selection", "Select an item to remove.")
            return
        del self.store.day(today())[key][selection[0]]
        self.store.save()
        self.refresh_reflections()

    def refresh_reflections(self):
        day = self.store.day(today())
        for key, listbox in self.lists.items():
            listbox.delete(0, tk.END)
            for item in day[key]:
                listbox.insert(tk.END, f"  •  {item}")

    # ------------------------------------------------------------------ #
    # Tab 4: Charts
    # ------------------------------------------------------------------ #
    def _build_charts_tab(self):
        tab = self._make_tab("📊  Judge Your Day")

        left = ttk.Frame(tab)
        left.pack(side="left", fill="y", padx=(0, 16))
        ttk.Label(left, text="Score each area (0-10)", font=FONT_BOLD).pack(pady=(0, 10))

        saved = self.store.day(today())["scores"]
        self.score_vars = {}
        for field in FIELDS:
            row = ttk.Frame(left)
            row.pack(fill="x", pady=4)
            ttk.Label(row, text=field.capitalize(), width=10).pack(side="left")
            var = tk.StringVar(value=str(saved.get(field, "")))
            ttk.Entry(row, textvariable=var, width=8).pack(side="left")
            self.score_vars[field] = var

        ttk.Button(left, text="🕸 Radar chart", style="Accent.TButton",
                   command=self.show_radar).pack(fill="x", pady=(16, 6))
        ttk.Button(left, text="🥧 Pie chart", style="Accent.TButton",
                   command=self.show_pie).pack(fill="x", pady=(0, 6))
        ttk.Button(left, text="📊 Bar chart", style="Accent.TButton",
                   command=self.show_bar).pack(fill="x")

        self.chart_frame = tk.Frame(tab, bg=CARD)
        self.chart_frame.pack(side="left", fill="both", expand=True)

    def _read_scores(self):
        try:
            values = [float(self.score_vars[f].get()) for f in FIELDS]
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for all fields.")
            return None
        if any(v < 0 or v > 10 for v in values):
            messagebox.showwarning("Warning", "Scores must be between 0 and 10.")
            return None
        self.store.day(today())["scores"] = dict(zip(FIELDS, values))
        self.store.save()
        return values

    def _show_figure(self, fig):
        # Destroy the previous chart so widgets don't pile up in memory.
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def show_radar(self):
        values = self._read_scores()
        if values is None:
            return

        angles = np.linspace(0, 2 * np.pi, len(FIELDS), endpoint=False).tolist()
        angles_closed = angles + angles[:1]
        values_closed = values + values[:1]

        # Figure() (not pyplot) avoids leaking figures every time you click.
        fig = Figure(figsize=(5, 4), dpi=100, facecolor=CARD)
        ax = fig.add_subplot(111, polar=True, facecolor=CARD)
        ax.set_theta_offset(np.pi / 2)
        ax.set_theta_direction(-1)
        ax.set_xticks(angles)
        ax.set_xticklabels([f.capitalize() for f in FIELDS], size=9, color=TEXT)
        ax.set_ylim(0, 10)
        ax.set_yticks([2, 4, 6, 8, 10])
        ax.set_yticklabels(["2", "4", "6", "8", "10"], color=MUTED, size=7)
        ax.grid(color=MUTED, alpha=0.3)
        ax.spines["polar"].set_color(MUTED)
        ax.plot(angles_closed, values_closed, color=ACCENT, linewidth=2, marker="o")
        ax.fill(angles_closed, values_closed, color=ACCENT, alpha=0.35)
        self._show_figure(fig)

    def show_pie(self):
        values = self._read_scores()
        if values is None:
            return
        if sum(values) == 0:
            messagebox.showwarning("Warning", "At least one score must be above 0.")
            return

        fig = Figure(figsize=(5, 4), dpi=100, facecolor=CARD)
        ax = fig.add_subplot(111, facecolor=CARD)
        ax.pie(
            values,
            labels=[f.capitalize() for f in FIELDS],
            autopct="%1.0f%%",
            colors=[ACCENT, GREEN, AMBER, BLUE, RED],
            textprops={"color": TEXT, "fontsize": 9},
            wedgeprops={"edgecolor": CARD, "linewidth": 2},
        )
        self._show_figure(fig)

    def show_bar(self):
        values = self._read_scores()
        if values is None:
            return

        labels = [f.capitalize() for f in FIELDS]
        colors = [ACCENT, GREEN, AMBER, BLUE, RED]

        fig = Figure(figsize=(5, 4), dpi=100, facecolor=CARD)
        ax = fig.add_subplot(111, facecolor=CARD)
        bars = ax.bar(labels, values, color=colors, width=0.6)
        ax.set_ylim(0, 10)
        ax.set_yticks(range(0, 11, 2))
        ax.tick_params(colors=TEXT, labelsize=9)
        ax.grid(axis="y", color=MUTED, alpha=0.3)
        ax.set_axisbelow(True)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(MUTED)
        # Show the exact score on top of each bar
        ax.bar_label(bars, fmt="%g", color=TEXT, fontsize=9, padding=3)
        fig.tight_layout()
        self._show_figure(fig)

    # ------------------------------------------------------------------ #
    # CSV export (tasks + punishments + strengths + weaknesses + scores)
    # ------------------------------------------------------------------ #
    def export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"daily_report_{today()}.csv",
            title="Save CSV report",
        )
        if not path:  # user cancelled
            return
        header = ["Date", "Category", "Item", "Status / Value",
                  "Start Time", "Finish Time", "Punishment"]
        try:
            # utf-8-sig so Excel displays non-English text correctly
            with open(path, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(header)
                writer.writerows(self.store.report_rows())
        except OSError as err:
            messagebox.showerror("Export failed", str(err))
        else:
            messagebox.showinfo("Exported", f"Report saved to:\n{path}")

    # ------------------------------------------------------------------ #
    def refresh_all(self):
        self.refresh_tasks()
        self.refresh_punishments()
        self.refresh_reflections()
        done = sum(1 for t in self.store.tasks if t["done"])
        self.summary_var.set(f"{today()}   •   {done}/{len(self.store.tasks)} tasks done")


if __name__ == "__main__":
    root = tk.Tk()
    TodoApp(root)
    root.mainloop()
