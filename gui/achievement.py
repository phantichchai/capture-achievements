import tkinter as tk
from tkinter import ttk
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

        self.all_data = self._load_json(all_path)
        self.account_data = self._load_json(account_path)

        self.completed_data, self.uncompleted_data = self._split_data()

        self._build_ui()

    def _load_json(self, path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _split_data(self):
        master_titles = {
            normalize(item["Achievement"]) for item in self.all_data
        }

        account_titles = {
            normalize(item["title"]) for item in self.account_data
            if normalize(item["title"]) in master_titles
        }

        completed = []
        uncompleted = []

        for item in self.all_data:
            title_norm = normalize(item["Achievement"])

            if title_norm in account_titles:
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

        # 🔥 Create Notebook (Tabs)
        notebook = ttk.Notebook(self.master)
        notebook.pack(fill="both", expand=True)

        completed_tab = ttk.Frame(notebook)
        uncompleted_tab = ttk.Frame(notebook)

        notebook.add(completed_tab, text=f"✅ Completed ({len(self.completed_data)})")
        notebook.add(uncompleted_tab, text=f"❌ Uncompleted ({len(self.uncompleted_data)})")

        # Create TableViews inside tabs
        self.completed_table = TableView(
            master=completed_tab,
            json_file="completed.json",
            transfer_label="Mark as Incomplete"
        )

        self.uncompleted_table = TableView(
            master=uncompleted_tab,
            json_file="uncompleted.json",
            transfer_label="Mark as Complete"
        )

        self.completed_table.set_other(self.uncompleted_table)
        self.uncompleted_table.set_other(self.completed_table)

        # Summary label
        total = len(self.all_data)
        completed = len(self.completed_data)

        summary = tk.Label(
            self.master,
            text=f"Progress: {completed} / {total}  ({round(completed/total*100, 1)}%)",
            font=("Arial", 14)
        )
        summary.pack(pady=5)


if __name__ == "__main__":
    root = tk.Tk()
    app = AchievementTrackerUI(
        root,
        all_path="all_achievements.json",
        account_path="achievements.json"
    )
    root.mainloop()
