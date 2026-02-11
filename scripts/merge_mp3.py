"""
Merge MP3 Audio Files

Merges multiple MP3 files into a single file, sorting by numeric prefix.
"""

import glob
import re
import os
from pathlib import Path


def extract_number(filename: str) -> int:
    """Extract numeric prefix from filename (e.g., '1' from '1-hello.mp3')."""
    basename = os.path.basename(filename)
    match = re.match(r"(\d+)-", basename)
    return int(match.group(1)) if match else float("inf")


def merge_audio_files(
    input_dir: str = "./mp3",
    output_file: str = None,
    file_pattern: str = "*.mp3",
    silence_between_ms: int = 500
) -> str:
    """
    Merge multiple MP3 files into a single file.
    
    Args:
        input_dir: Directory containing MP3 files to merge
        output_file: Output file path (default: input_dir/merged.mp3)
        file_pattern: Glob pattern for files to merge
        silence_between_ms: Milliseconds of silence between tracks
    
    Returns:
        Path to the merged output file
    """
    from pydub import AudioSegment
    
    input_path = Path(input_dir)
    
    if output_file is None:
        output_file = str(input_path / "merged.mp3")
    
    # Get all matching files and sort by number prefix
    pattern = str(input_path / file_pattern)
    files = sorted(glob.glob(pattern), key=extract_number)
    
    if not files:
        print(f"❌ No files matching '{file_pattern}' found in {input_dir}")
        return None
    
    print(f"🔗 Merging {len(files)} audio files...")
    for i, f in enumerate(files, 1):
        print(f"   {i}. {os.path.basename(f)}")
    
    # Create silence segment for gaps between files
    silence = AudioSegment.silent(duration=silence_between_ms)
    
    # Merge all audio files
    combined = AudioSegment.empty()
    for i, f in enumerate(files):
        audio = AudioSegment.from_mp3(f)
        combined += audio
        # Add silence between files (not after the last one)
        if i < len(files) - 1:
            combined += silence
    
    # Export merged file
    combined.export(output_file, format="mp3")
    
    print(f"✅ Merged audio saved to: {output_file}")
    print(f"   Total duration: {len(combined) / 1000:.1f} seconds")
    
    return output_file


if __name__ == "__main__":
    # Standalone execution
    merge_audio_files()
