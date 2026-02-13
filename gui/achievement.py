import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import json
import os

from gui.view.table import TableView  # your class file


def normalize(text):
    return text.lower().strip()


class AchievementTrackerUI:
    def __init__(self, master, all_path, account_path):
        self.master = master
        self.master.title("Genshin Achievement Tracker")
        self.master.geometry("1400x750")

        self.all_path = all_path
        self.account_path = account_path

        self._startup_choice()

    def _startup_choice(self):
        os.makedirs("json_data", exist_ok=True)

        completed_path = os.path.join("json_data", "completed.json")
        uncompleted_path = os.path.join("json_data", "uncompleted.json")

        if os.path.exists(completed_path) and os.path.exists(uncompleted_path):
            answer = messagebox.askyesno(
                "Load Existing Data",
                "Do you want to load existing saved progress?\n\n"
                "Yes = Load saved progress\n"
                "No = Recalculate from account file"
            )

            if answer:
                self.completed_data = self._load_json(completed_path)
                self.uncompleted_data = self._load_json(uncompleted_path)
                self.all_data = self.completed_data + self.uncompleted_data
            else:
                self._populate_from_account()
        else:
            self._populate_from_account()

        self._build_ui()

    def _populate_from_account(self):
        self.all_data = self._load_json(self.all_path)
        self.account_data = self._load_json(self.account_path)
        self.completed_data, self.uncompleted_data = self._split_data()

    def _load_json(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _split_data(self):
        # Build lookup dict: { normalized_title: progress_string }
        account_progress = {
            normalize(item["title"]): item.get("progress", "").strip()
            for item in self.account_data
        }

        completed = []
        uncompleted = []

        for item in self.all_data:
            title_norm = normalize(item["Achievement"])
            progress = account_progress.get(title_norm, "")

            # ✅ Check if progress starts with "Completed"
            if progress.lower().startswith("completed"):
                completed.append(item)
            else:
                uncompleted.append(item)

        return completed, uncompleted

    def _build_ui(self):
        os.makedirs("json_data", exist_ok=True)

        completed_path = os.path.join("json_data", "completed.json")
        uncompleted_path = os.path.join("json_data", "uncompleted.json")

        with open(completed_path, "w", encoding="utf-8") as f:
            json.dump(self.completed_data, f, indent=4, ensure_ascii=False)

        with open(uncompleted_path, "w", encoding="utf-8") as f:
            json.dump(self.uncompleted_data, f, indent=4, ensure_ascii=False)

        # Store total count
        self.total_count = len(self.all_data)

        # 🔥 Notebook
        self.notebook = ttk.Notebook(self.master)
        self.notebook.pack(fill="both", expand=True)

        self.completed_tab = ttk.Frame(self.notebook)
        self.uncompleted_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.completed_tab, text="")
        self.notebook.add(self.uncompleted_tab, text="")

        # Create tables
        self.completed_table = TableView(
            master=self.completed_tab,
            json_file="completed.json",
            transfer_label="Mark as Incomplete"
        )

        self.uncompleted_table = TableView(
            master=self.uncompleted_tab,
            json_file="uncompleted.json",
            transfer_label="Mark as Complete"
        )

        self.completed_table.set_other(self.uncompleted_table)
        self.uncompleted_table.set_other(self.completed_table)

        # Give tables access to parent controller
        self.completed_table.controller = self
        self.uncompleted_table.controller = self

        # Summary label
        self.summary_label = tk.Label(
            self.master,
            font=("Arial", 14)
        )
        self.summary_label.pack(pady=5)

        self.save_button = tk.Button(
            self.master,
            text="💾 Save Progress",
            command=self.save_progress,
            font=("Arial", 12)
        )
        self.save_button.pack(pady=5)

        self.update_progress()

    def save_progress(self):
        completed_path = os.path.join("json_data", "completed.json")
        uncompleted_path = os.path.join("json_data", "uncompleted.json")

        with open(completed_path, "w", encoding="utf-8") as f:
            json.dump(self.completed_table.data, f, indent=4, ensure_ascii=False)

        with open(uncompleted_path, "w", encoding="utf-8") as f:
            json.dump(self.uncompleted_table.data, f, indent=4, ensure_ascii=False)

        messagebox.showinfo("Saved", "Progress saved successfully!")

    def update_progress(self):
        completed = len(self.completed_table.data)
        total = self.total_count

        percent = (completed / total * 100) if total > 0 else 0

        # Update summary text
        self.summary_label.config(
            text=f"Progress: {completed} / {total}  ({percent:.1f}%)"
        )

        # Update tab titles dynamically
        self.notebook.tab(
            self.completed_tab,
            text=f"✅ Completed ({completed})"
        )

        self.notebook.tab(
            self.uncompleted_tab,
            text=f"❌ Uncompleted ({total - completed})"
        )



if __name__ == "__main__":
    root = tk.Tk()
    app = AchievementTrackerUI(
        root,
        all_path="all_achievements.json",
        account_path="achievements.json"
    )
    root.mainloop()
