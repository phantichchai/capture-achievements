# process/processor.py

import argparse
import time
import os
from process.video_processor import process_video_file
from process.text_processor import update_catalogue

def run_video_processor(video_path):
    """Backward-compatible CLI helper using the shared video processor."""
    json_data_folder = "json_data"
    if not os.path.exists(json_data_folder):
        os.makedirs(json_data_folder)

    start_time = time.time()
    update_catalogue()
    results = process_video_file(video_path)
    video_duration = time.time() - start_time
    return results, f"Video processing time: {video_duration:.2f} seconds"

def find_and_save_matching_data(table_processor, text_data) -> str:
    start_time = time.time()
    (uncompleted_achievement_data, completed_achievement_data) = table_processor.find_matching_data(text_data)
    uncompleted_output_file = os.path.join('json_data', 'uncompleted_achievement_data.json')
    table_processor.save_data_to_json(uncompleted_achievement_data, uncompleted_output_file)
    completed_output_file = os.path.join('json_data', 'completed_achievement_data.json')
    table_processor.save_data_to_json(completed_achievement_data, completed_output_file)
    finding_and_saving_duration = time.time() - start_time
    print(f"Uncompleted data saved to {uncompleted_output_file}")
    print(f"Completed data saved to {completed_output_file}")
    return f"Finding and saving time: {finding_and_saving_duration:.2f} seconds"

def run(video_path):
    (video_processor, _) = run_video_processor(video_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process Genshin Impact achievements data.")
    parser.add_argument("video_path", help="Path to the video file")
    args = parser.parse_args()

    run(args.video_path)
