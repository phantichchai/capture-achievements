import tkinter as tk
from gui.achievement import AchievementTrackerUI


root = tk.Tk()
app = AchievementTrackerUI(
    root,
    all_path="all_achievements.json",
    account_path="achievements.json"
)
root.mainloop()
