import tkinter as tk
from tkinter import ttk
import os
import json

class TableView(tk.Frame):
    def __init__(self, 
                 master=None,
                 json_file: str=None, 
                 transfer_label: str=None,
                 **kwargs):
        super().__init__(master, **kwargs)
        self.parent = master
        self.other = None
        self.json_path = os.path.join("json_data", json_file)

        self.wrapper1 = tk.LabelFrame(self.parent, text="Filter Achievements", padx=20, pady=5)
        self.wrapper2 = tk.LabelFrame(self.parent, text="Achievements", padx=20, pady=10)

        self.wrapper1.pack(fill="x", padx=20, pady=20)
        self.wrapper2.pack(fill="both", expand="yes",padx=20, pady=20)
        self.tree = ttk.Treeview(self.wrapper2, selectmode="extended")

        # Define columns
        self.columns = ("Achievement", "Description", "Requirements", "Hidden?", "Type", "Version")
        
        # Create a vertical scrollbar
        self.scrollbar = ttk.Scrollbar(self.wrapper2, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")

        # Create entry widgets for searching in each column
        self.search_entry = tk.Entry(self.wrapper1, font=("Helvetica", 10))
        self.search_entry.pack(side="top", fill="x")

        # Create a variable to track the selected radio button
        self.selected_radio = tk.StringVar()

        self.radios = []
        self.populate_radio_buttons()
        self.selected_radio.set(self.columns[0])

        # Define columns
        self.tree["columns"] = self.columns

        # Create headings
        self.tree.heading("#0", text="", anchor=tk.W)
        self.tree.heading("Achievement", text="Achievement", anchor=tk.W)
        self.tree.heading("Description", text="Description", anchor=tk.W)
        self.tree.heading("Requirements", text="Requirements", anchor=tk.W)
        self.tree.heading("Hidden?", text="Hidden?", anchor=tk.W)
        self.tree.heading("Type", text="Type", anchor=tk.W)
        self.tree.heading("Version", text="Version", anchor=tk.W)

        # Load data from JSON file
        self.data = self.load_data_from_json()  # Load data and store it
        self.populate_tree()

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Create an option menu with some commands
        self.menu = tk.Menu(master, tearoff=0)
        self.menu.add_command(label="Copy", command=self.copy_to_clipboard)
        self.menu.add_separator()
        self.menu.add_command(label=transfer_label, command=self.transfer_data)
        
        # Bind the function to resize columns on window resize
        self.tree.bind("<Configure>", self.resize_columns)

        # Bind the function to the treeview
        self.tree.bind("<Button-3>", self.show_menu)
        
        # Bind the KeyRelease event to the search entry
        self.search_entry.bind("<KeyRelease>", lambda event: self.filter_data())

    
    def filter_data(self):
        search_text = self.search_entry.get().lower()  # Get the search text from the entry
        selected_column = self.selected_radio.get()  # Get the selected column from the radio button

        filtered_data = []

        for item in self.data:
            if search_text in item[selected_column].lower():  # Check if the search text is in the selected column
                filtered_data.append(item)

        self.populate_tree(filtered_data)  # Populate the Treeview with filtered data

    # Define a function to show the menu when left clicking on an item
    def show_menu(self, event):
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def load_data_from_json(self):
        try:
            with open(self.json_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                for item in data:
                    item.pop("processed_value", None)
                return data  # Return the loaded data

        except FileNotFoundError:
            print(f"JSON file '{self.json_path}' not found.")
            return []

    def populate_tree(self, data=None):
        if data is None:
            data = self.data
        
        # Clear existing items
        self.tree.delete(*self.tree.get_children())
        
        for item in data:
            values = (
                item["Achievement"], item["Description"], item["Requirements"],
                item["Hidden?"], item["Type"], item["Version"]
            )
            self.tree.insert(parent="", index="end", text="", values=values)

    def populate_radio_buttons(self):
        for col in self.columns:
            radio = tk.Radiobutton(self.wrapper1, text=col, variable=self.selected_radio, value=col)
            radio.pack(side="left", fill="y")
            self.radios.append(radio)

    def copy_to_clipboard(self):
        item = self.tree.selection()[0]  # Get the item under the mouse cursor
        if item:  # Ensure an item is found
            achievement_name = self.tree.item(item, "values")[0]
            self.parent.clipboard_clear()
            self.parent.clipboard_append(achievement_name)
            self.parent.update()

    def resize_columns(self, event):
        # Calculate column widths based on the current Treeview width
        tree_width = self.tree.winfo_width()
        column_width = tree_width // 6  # Divide evenly among the columns

        # Format columns
        self.tree.column("#0", width=0, stretch=tk.NO)
        for col in self.columns:
            self.tree.column(col, anchor=tk.W, width=column_width)

    def set_other(self, other):
        self.other = other

    def get_selected_items(self):
        selected_items = self.tree.selection()
        data = []
        for item in selected_items:
            values = self.tree.item(item, "values")
            record = {
                "Achievement": values[0],
                "Description": values[1],
                "Requirements": values[2],
                "Hidden?": values[3],
                "Type": values[4],
                "Version": values[5]
            }
            data.append(record)
            self.data.remove(record)

        self.tree.delete(selected_items)
        return data
    
    def insert_data(self, data):
        for item in data:
            values = (
                item["Achievement"], item["Description"], item["Requirements"],
                item["Hidden?"], item["Type"], item["Version"]
            )            
            self.data.append(item)
            self.tree.insert(parent="", index="end", text="", values=values)
            
    def transfer_data(self):
        selected_items = self.get_selected_items()
        if self.other:
            self.other.insert_data(selected_items)
        else:
            print("No other instance specified.")
