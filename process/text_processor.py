from process.media_wiki import MediaWikiPageParser, GenshinAchievement
import json

if __name__ == "__main__":
    parser = MediaWikiPageParser()
    obj = GenshinAchievement(parser)

    achievements = obj.get_all_achievements()

    with open("all_achievements.json", "w", encoding="utf-8") as f:
        json.dump(achievements, f, indent=4, ensure_ascii=False)
