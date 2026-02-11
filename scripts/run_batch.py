"""
Run Batch Text-to-Speech Processing

Edit the configuration below to customize your batch processing.
"""

import asyncio
import os
from pathlib import Path
from scripts.batch_process import batch_process, list_available_voices
from scripts.merge_mp3 import merge_audio_files


# ============ CONFIGURATION - EDIT THESE VALUES ============

# List your input files here (can be .txt or .srt files)
INPUT_FILES = [
    # Add your file paths here, for example:
    # "C:/path/to/file1.txt",
    # "C:/path/to/file2.srt",
    # "./input/myfile.txt",
]

# Or specify a directory containing .txt and .srt files
INPUT_DIRECTORY = "./extracted"  # Default: use extracted folder

# Output directory where audio files will be saved
OUTPUT_DIRECTORY = "./mp3"

# Voice settings
VOICE = "ta-IN-PallaviNeural"  # Use list_voices() to see all options

# Speech adjustments
RATE = 0       # -50 to 50 (speech speed)
PITCH = 0      # -20 to 20 (voice pitch in Hz)
VOLUME = 0     # -50 to 50 (audio volume)

# Generate subtitle (.srt) files alongside audio
GENERATE_SUBTITLES = False

# Merge all generated MP3 files into a single file
MERGE_AFTER_PROCESSING = True
SILENCE_BETWEEN_TRACKS_MS = 500  # Silence between merged tracks

# ============================================================


async def run_batch_tts(
    input_files: list[str] = None,
    input_dir: str = None,
    output_dir: str = None,
    voice: str = None,
    rate: int = None,
    pitch: int = None,
    volume: int = None,
    generate_subtitles: bool = None,
    merge_after: bool = None,
    silence_between_ms: int = None
):
    """
    Run batch TTS with configurable options.
    
    Args:
        input_files: List of specific files to process
        input_dir: Directory containing .txt/.srt files
        output_dir: Directory for output audio files
        voice: Voice name (e.g., 'ta-IN-PallaviNeural')
        rate: Speech rate (-50 to 50)
        pitch: Voice pitch (-20 to 20)
        volume: Audio volume (-50 to 50)
        generate_subtitles: Whether to generate .srt files
        merge_after: Whether to merge all output files into one
        silence_between_ms: Silence between merged tracks
    """
    # Use provided values or fall back to defaults
    files = list(input_files) if input_files else INPUT_FILES.copy()
    directory = input_dir if input_dir is not None else INPUT_DIRECTORY
    out_dir = output_dir or OUTPUT_DIRECTORY
    voice_name = voice or VOICE
    speech_rate = rate if rate is not None else RATE
    speech_pitch = pitch if pitch is not None else PITCH
    speech_volume = volume if volume is not None else VOLUME
    gen_subs = generate_subtitles if generate_subtitles is not None else GENERATE_SUBTITLES
    do_merge = merge_after if merge_after is not None else MERGE_AFTER_PROCESSING
    silence_ms = silence_between_ms if silence_between_ms is not None else SILENCE_BETWEEN_TRACKS_MS
    
    # Add files from directory if specified
    if directory:
        input_path = Path(directory)
        if input_path.exists():
            for ext in ['.txt', '.srt']:
                files.extend([str(f) for f in input_path.glob(f'*{ext}')])
    
    if not files:
        print("❌ No input files found!")
        print("   Provide input files or set a valid input directory")
        return [], ""
    
    print(f"🎤 Starting batch processing...")
    print(f"   Files: {len(files)}")
    print(f"   Voice: {voice_name}")
    print(f"   Output: {out_dir}\n")
    
    output_files, summary = await batch_process(
        input_files=files,
        output_dir=out_dir,
        voice_short_name=voice_name,
        rate=speech_rate,
        pitch=speech_pitch,
        volume=speech_volume,
        generate_subtitles=gen_subs
    )
    
    print(f"\n{summary}")
    print(f"\n📁 Output saved to: {os.path.abspath(out_dir)}")
    
    # Merge audio files if enabled
    merged_file = None
    if do_merge and output_files:
        print("\n" + "="*50)
        merged_file = merge_audio_files(
            input_dir=out_dir,
            silence_between_ms=silence_ms
        )
    
    return output_files, summary, merged_file


async def main():
    # Uncomment the next line to see all available voices
    # await list_available_voices()
    
    await run_batch_tts()


if __name__ == "__main__":
    asyncio.run(main())
