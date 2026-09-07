import argparse

def main():
    parser = argparse.ArgumentParser(description="Genshin Impact achievement tracker")
    parser.add_argument(
        "command",
        nargs="?",
        choices=["fetch"],
        help="fetch, compare, and update the local achievement catalogue, then exit",
    )
    args = parser.parse_args()

    if args.command == "fetch":
        from process.media_wiki import CatalogueRefreshError
        from process.text_processor import update_catalogue

        try:
            update_catalogue()
        except CatalogueRefreshError as exc:
            parser.exit(1, f"Error: {exc}\n")
        return

    import tkinter as tk
    from gui.achievement import AchievementTrackerUI

    root = tk.Tk()
    AchievementTrackerUI(
        root,
        all_path="all_achievements.json",
        account_path="achievements.json",
    )
    root.mainloop()


if __name__ == "__main__":
    main()
