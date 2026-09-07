from typing import Callable, Optional

from process.media_wiki import refresh_achievement_catalogue


def update_catalogue(
    output_path: str = "all_achievements.json",
    *,
    progress_callback: Optional[Callable[[str], None]] = None,
):
    """Refresh the local catalogue for both CLI and GUI callers."""
    if progress_callback:
        progress_callback("Fetching the achievement catalogue…")
    summary = refresh_achievement_catalogue(output_path=output_path, strict=True)
    if progress_callback:
        progress_callback(
            "Catalogue updated: "
            f"{summary['added']} added, {summary['updated']} updated, "
            f"{summary['unchanged']} unchanged."
        )
    return summary

if __name__ == "__main__":
    update_catalogue()
