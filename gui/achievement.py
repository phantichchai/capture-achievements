import tkinter as tk
from tkinter import ttk, filedialog
from tkinter import messagebox
import json
import os
import threading
import traceback
import queue

from process.text_processor import update_catalogue

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
        self._processing = False
        self._ui_events = queue.Queue()

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
        self.master.after(100, self._drain_ui_events)

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

        self._build_processing_tools()

        self.update_progress()

    def _build_processing_tools(self):
        tools = ttk.LabelFrame(self.master, text="Processing tools", padding=10)
        tools.pack(fill="x", padx=20, pady=(0, 10))

        self.catalogue_button = ttk.Button(
            tools, text="Update Achievement Catalogue", command=self.update_catalogue
        )
        self.catalogue_button.pack(side="left", padx=(0, 8))
        self.video_button = ttk.Button(
            tools, text="Process Video", command=self.select_and_process_video
        )
        self.video_button.pack(side="left")

        self.processing_status = tk.StringVar(value="Ready")
        ttk.Label(tools, textvariable=self.processing_status).pack(
            side="left", padx=15, fill="x", expand=True
        )
        self.processing_progress = ttk.Progressbar(tools, length=180, mode="determinate")
        self.processing_progress.pack(side="right")

        self.status_text = tk.Text(self.master, height=5, state="disabled", wrap="word")
        self.status_text.pack(fill="x", padx=20, pady=(0, 10))

    def _post_status(self, message, progress=None):
        self._ui_events.put((message, progress))

    def _drain_ui_events(self):
        try:
            while True:
                message, progress = self._ui_events.get_nowait()
                if message == "__PROCESSING_FINISHED__":
                    self._set_processing(False)
                    continue
                self.processing_status.set(message)
                self.status_text.configure(state="normal")
                self.status_text.insert("end", message + "\n")
                self.status_text.see("end")
                self.status_text.configure(state="disabled")
                if progress is None:
                    self.processing_progress.stop()
                    self.processing_progress.configure(mode="indeterminate")
                    self.processing_progress.start(10)
                else:
                    self.processing_progress.stop()
                    self.processing_progress.configure(mode="determinate", value=progress)
        except queue.Empty:
            pass
        self.master.after(100, self._drain_ui_events)

    def _set_processing(self, running):
        self._processing = running
        state = "disabled" if running else "normal"
        self.catalogue_button.configure(state=state)
        self.video_button.configure(state=state)
        if not running:
            self.processing_progress.stop()

    def _start_worker(self, operation, worker):
        if self._processing:
            return
        self._set_processing(True)
        self._post_status(operation)

        def run():
            try:
                worker()
            except Exception as exc:
                detail = f"Error: {exc}"
                self._post_status(detail)
                traceback.print_exc()
            finally:
                self._ui_events.put(("__PROCESSING_FINISHED__", None))
        threading.Thread(target=run, daemon=True).start()

    def update_catalogue(self):
        def worker():
            summary = update_catalogue(
                output_path=self.all_path,
                progress_callback=lambda message: self._post_status(message),
            )
            self._post_status(
                "Catalogue refresh complete: "
                f"{summary['added']} added, {summary['updated']} updated."
            )
        self._start_worker("Updating achievement catalogue…", worker)

    def select_and_process_video(self):
        if self._processing:
            return
        video_path = filedialog.askopenfilename(
            title="Select a video",
            filetypes=[("Video files", "*.mp4 *.mkv *.avi *.mov *.webm"), ("All files", "*.*")],
        )
        if not video_path:
            return

        def worker():
            catalogue_available = self._has_local_catalogue()
            try:
                update_catalogue(
                    output_path=self.all_path,
                    progress_callback=lambda message: self._post_status(message),
                )
                self._post_status("Catalogue refresh succeeded.")
            except Exception as exc:
                if not catalogue_available:
                    raise RuntimeError(
                        f"Catalogue refresh failed and no local catalogue is available: {exc}"
                    ) from exc
                self._post_status(
                    f"Catalogue refresh failed; continuing with local catalogue: {exc}"
                )

            from process.video_processor import process_video_file
            results = process_video_file(
                video_path,
                template_path="template.png",
                json_path=self.account_path,
                catalogue_path=self.all_path,
                progress_callback=lambda message, progress=None: self._post_status(message, progress),
            )
            self._post_status(f"Video processing complete. {len(results)} achievement records saved.")

        self._start_worker(f"Preparing video: {os.path.basename(video_path)}", worker)

    def _has_local_catalogue(self):
        try:
            with open(self.all_path, "r", encoding="utf-8") as catalogue_file:
                return isinstance(json.load(catalogue_file), list)
        except (OSError, ValueError, TypeError):
            return False

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
