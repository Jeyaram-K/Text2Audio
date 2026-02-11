"""
Batch Text-to-Speech Processing Script

This standalone script processes multiple text/SRT files and converts them to speech
using Microsoft Edge TTS. It can be run from command line or imported as a module.

Usage:
    python batch_process.py --input_dir ./files --output_dir ./output --voice "en-US-AriaNeural" --generate_subtitles
"""

import edge_tts
import asyncio
import tempfile
import os
import re
import shutil
import argparse
from pathlib import Path


def format_time(milliseconds):
    """Convert milliseconds to SRT time format (HH:MM:SS,mmm)"""
    milliseconds = int(milliseconds)
    seconds, milliseconds = divmod(milliseconds, 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"


def time_to_ms(time_str):
    """Convert SRT time format (HH:MM:SS,mmm) to milliseconds"""
    hours, minutes, rest = time_str.split(':')
    seconds, milliseconds = rest.split(',')
    return int(hours) * 3600000 + int(minutes) * 60000 + int(seconds) * 1000 + int(milliseconds)


def parse_srt_content(content):
    """Parse SRT file content and extract text and timing data"""
    lines = content.split('\n')
    timing_data = []
    text_only = []
    
    i = 0
    while i < len(lines):
        if not lines[i].strip():
            i += 1
            continue
            
        if lines[i].strip().isdigit():
            subtitle_num = int(lines[i].strip())
            i += 1
            if i >= len(lines):
                break
                
            timestamp_match = re.search(r'(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})', lines[i])
            if timestamp_match:
                start_time = timestamp_match.group(1)
                end_time = timestamp_match.group(2)
                
                start_ms = time_to_ms(start_time)
                end_ms = time_to_ms(end_time)
                
                i += 1
                subtitle_text = ""
                
                while i < len(lines) and lines[i].strip():
                    subtitle_text += lines[i] + " "
                    i += 1
                
                subtitle_text = subtitle_text.strip()
                text_only.append(subtitle_text)
                timing_data.append({
                    'text': subtitle_text,
                    'start': start_ms,
                    'end': end_ms
                })
        else:
            i += 1
    
    return " ".join(text_only), timing_data


async def get_voices():
    """Get all available Edge TTS voices"""
    voices = await edge_tts.list_voices()
    return {
        f"{v['ShortName']} - {v['Locale']} ({v['Gender']})": v["ShortName"]
        for v in voices
    }


async def process_file(file_path):
    """Process a file and detect if it's SRT or plain text"""
    try:
        file_extension = os.path.splitext(file_path)[1].lower()
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        is_subtitle = False
        timing_data = None
        
        if file_extension == '.srt' or re.search(r'^\d+\s*\n\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}', content, re.MULTILINE):
            is_subtitle = True
            text_content, timing_data = parse_srt_content(content)
            return text_content, timing_data, is_subtitle, content, base_name
        else:
            text_content = content
        
        return text_content, timing_data, is_subtitle, content, base_name
    except Exception as e:
        return f"Error processing file: {str(e)}", None, False, None, None


async def text_to_speech(text, voice_short_name, rate=0, pitch=0, volume=0, generate_subtitles=False):
    """Convert text to speech with Edge TTS"""
    if not text.strip():
        return None, None, "Please enter text to convert."
    
    rate_str = f"{rate:+d}%"
    pitch_str = f"{pitch:+d}Hz"
    volume_str = f"{volume:+d}%"
    
    # Determine if text is SRT format
    is_srt_format = bool(re.search(r'^\d+\s*\n\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}', text, re.MULTILINE))
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        audio_path = tmp_file.name
    
    subtitle_path = None
    
    if is_srt_format:
        text_content, timing_data = parse_srt_content(text)
        
        with tempfile.TemporaryDirectory() as temp_dir:
            audio_segments = []
            max_end_time = 0
            
            for i, entry in enumerate(timing_data):
                segment_text = entry['text'].strip()
                start_time = entry['start']
                end_time = entry['end']
                max_end_time = max(max_end_time, end_time)
                
                if not segment_text:
                    continue
                
                segment_file = os.path.join(temp_dir, f"segment_{i}.mp3")
                
                try:
                    communicate = edge_tts.Communicate(
                        segment_text, voice_short_name, rate=rate_str, volume=volume_str, pitch=pitch_str
                    )
                    await communicate.save(segment_file)
                except edge_tts.exceptions.NoAudioReceived:
                    print(f"Warning: Skipped segment {i+1} - no audio received for text: '{segment_text[:50]}...'")
                    continue
                except Exception as e:
                    print(f"Warning: Skipped segment {i+1} due to error: {e}")
                    continue
                
                audio_segments.append({
                    'file': segment_file,
                    'start': start_time,
                    'end': end_time,
                    'text': segment_text
                })
            
            from pydub import AudioSegment
            
            final_audio = AudioSegment.silent(duration=max_end_time + 1000)
            
            for segment in audio_segments:
                segment_audio = AudioSegment.from_file(segment['file'])
                final_audio = final_audio.overlay(segment_audio, position=segment['start'])
            
            final_audio.export(audio_path, format="mp3")
            
            if generate_subtitles:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".srt") as srt_file:
                    subtitle_path = srt_file.name
                    with open(subtitle_path, "w", encoding="utf-8") as f:
                        for i, entry in enumerate(timing_data):
                            f.write(f"{i+1}\n")
                            f.write(f"{format_time(entry['start'])} --> {format_time(entry['end'])}\n")
                            f.write(f"{entry['text']}\n\n")
    else:
        text_to_convert = text.strip()
        if not text_to_convert:
            return None, None, "Please enter some text to convert."
        
        communicate = edge_tts.Communicate(
            text_to_convert, voice_short_name, rate=rate_str, volume=volume_str, pitch=pitch_str
        )
        
        try:
            if not generate_subtitles:
                await communicate.save(audio_path)
            else:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".srt") as srt_file:
                    subtitle_path = srt_file.name
                
                word_boundaries = []
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        with open(audio_path, "ab") as audio_file:
                            audio_file.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        word_boundaries.append(chunk)
                
                # Generate subtitles from word boundaries
                phrases = []
                current_phrase = []
                current_text = ""
                phrase_start = 0
                
                for i, boundary in enumerate(word_boundaries):
                    word = boundary["text"]
                    start_time = boundary["offset"] / 10000
                    duration = boundary["duration"] / 10000
                    end_time = start_time + duration
                    
                    if not current_phrase:
                        phrase_start = start_time
                    
                    current_phrase.append(boundary)
                    
                    if word in ['.', ',', '!', '?', ':', ';'] or word.startswith(('.', ',', '!', '?', ':', ';')):
                        current_text = current_text.rstrip() + word + " "
                    else:
                        current_text += word + " "
                    
                    should_break = False
                    if word.endswith(('.', '!', '?', ':', ';', ',')) or i == len(word_boundaries) - 1:
                        should_break = True
                    elif len(current_phrase) >= 5:
                        should_break = True
                    elif i < len(word_boundaries) - 1:
                        next_start = word_boundaries[i + 1]["offset"] / 10000
                        if next_start - end_time > 300:
                            should_break = True
                
                    if should_break or i == len(word_boundaries) - 1:
                        if current_phrase:
                            last_boundary = current_phrase[-1]
                            phrase_end = (last_boundary["offset"] + last_boundary["duration"]) / 10000
                            phrases.append({
                                "text": current_text.strip(),
                                "start": phrase_start,
                                "end": phrase_end
                            })
                            current_phrase = []
                            current_text = ""
                
                with open(subtitle_path, "w", encoding="utf-8") as srt_file:
                    for i, phrase in enumerate(phrases):
                        srt_file.write(f"{i+1}\n")
                        srt_file.write(f"{format_time(phrase['start'])} --> {format_time(phrase['end'])}\n")
                        srt_file.write(f"{phrase['text']}\n\n")
                        
        except edge_tts.exceptions.NoAudioReceived:
            return None, None, "No audio was received from TTS service. Please check your text and try again."
        except Exception as e:
            return None, None, f"Error generating audio: {str(e)}"
    
    return audio_path, subtitle_path, None


async def process_single_file(file_path, voice_short_name, rate, pitch, volume, generate_subtitles, output_dir):
    """Process a single file for batch processing"""
    text_content, timing_data, is_subtitle, original_content, base_name = await process_file(file_path)
    
    if original_content is None:
        return None, None, f"Failed to process file: {file_path}"
    
    audio_path, subtitle_path, warning = await text_to_speech(
        original_content, voice_short_name, rate, pitch, volume, generate_subtitles
    )
    
    if warning:
        return None, None, warning
    
    # Rename audio file to match input filename
    if audio_path and base_name:
        new_audio_path = os.path.join(output_dir, f"{base_name}.mp3")
        shutil.copy2(audio_path, new_audio_path)
        os.remove(audio_path)
        audio_path = new_audio_path
    
    # Rename subtitle file to match input filename
    if subtitle_path and base_name:
        new_subtitle_path = os.path.join(output_dir, f"{base_name}.srt")
        shutil.copy2(subtitle_path, new_subtitle_path)
        os.remove(subtitle_path)
        subtitle_path = new_subtitle_path
    
    return audio_path, subtitle_path, None


async def batch_process(input_files, output_dir, voice_short_name, rate=0, pitch=0, volume=0, generate_subtitles=False):
    """
    Process multiple files and convert them to speech.
    
    Args:
        input_files: List of file paths to process
        output_dir: Directory to save output files
        voice_short_name: Edge TTS voice name (e.g., "en-US-AriaNeural")
        rate: Speech rate adjustment (-50 to 50)
        pitch: Pitch adjustment (-20 to 20)
        volume: Volume adjustment (-50 to 50)
        generate_subtitles: Whether to generate .srt subtitle files
    
    Returns:
        Tuple of (output_files, summary_message)
    """
    if not input_files:
        return [], "No files provided."
    
    os.makedirs(output_dir, exist_ok=True)
    
    results = []
    total_files = len(input_files)
    
    for i, file_path in enumerate(input_files):
        print(f"Processing {i+1}/{total_files}: {os.path.basename(file_path)}")
        
        audio_path, subtitle_path, error = await process_single_file(
            file_path, voice_short_name, rate, pitch, volume, generate_subtitles, output_dir
        )
        
        if error:
            results.append({"file": os.path.basename(file_path), "error": error})
            print(f"  ❌ Error: {error}")
        else:
            result_entry = {"audio": audio_path}
            if subtitle_path:
                result_entry["subtitle"] = subtitle_path
            results.append(result_entry)
            print(f"  ✅ Success: {os.path.basename(audio_path)}")
    
    # Collect all output files
    output_files = []
    for result in results:
        if "audio" in result:
            output_files.append(result["audio"])
        if "subtitle" in result:
            output_files.append(result["subtitle"])
    
    # Create summary message
    successful = len([r for r in results if "audio" in r])
    failed = len([r for r in results if "error" in r])
    summary = f"✅ Processed {successful}/{total_files} files successfully."
    if failed > 0:
        summary += f"\n❌ {failed} files failed."
        for r in results:
            if "error" in r:
                summary += f"\n  - {r.get('file', 'Unknown')}: {r['error']}"
    
    return output_files, summary


async def list_available_voices():
    """List all available Edge TTS voices"""
    voices = await get_voices()
    print("\nAvailable voices:")
    print("-" * 60)
    for display_name, short_name in sorted(voices.items()):
        print(f"  {short_name}: {display_name}")
    print("-" * 60)
    return voices


async def main():
    parser = argparse.ArgumentParser(description="Batch Text-to-Speech using Edge TTS")
    parser.add_argument("--input_dir", "-i", type=str, help="Directory containing input files")
    parser.add_argument("--input_files", "-f", nargs="+", type=str, help="Individual input files")
    parser.add_argument("--output_dir", "-o", type=str, default="./output", help="Output directory")
    parser.add_argument("--voice", "-v", type=str, default="en-US-AriaNeural", help="Voice name (use --list_voices to see options)")
    parser.add_argument("--rate", "-r", type=int, default=0, help="Speech rate adjustment (-50 to 50)")
    parser.add_argument("--pitch", "-p", type=int, default=0, help="Pitch adjustment (-20 to 20)")
    parser.add_argument("--volume", type=int, default=0, help="Volume adjustment (-50 to 50)")
    parser.add_argument("--generate_subtitles", "-s", action="store_true", help="Generate subtitle files")
    parser.add_argument("--list_voices", "-l", action="store_true", help="List available voices and exit")
    
    args = parser.parse_args()
    
    if args.list_voices:
        await list_available_voices()
        return
    
    # Collect input files
    input_files = []
    
    if args.input_files:
        input_files.extend(args.input_files)
    
    if args.input_dir:
        input_path = Path(args.input_dir)
        if input_path.exists():
            for ext in ['.txt', '.srt']:
                input_files.extend([str(f) for f in input_path.glob(f'*{ext}')])
    
    if not input_files:
        print("Error: No input files provided. Use --input_dir or --input_files")
        parser.print_help()
        return
    
    print(f"\n🎤 Batch Text-to-Speech Processing")
    print(f"   Voice: {args.voice}")
    print(f"   Rate: {args.rate}%, Pitch: {args.pitch}Hz, Volume: {args.volume}%")
    print(f"   Subtitles: {'Yes' if args.generate_subtitles else 'No'}")
    print(f"   Output: {args.output_dir}")
    print(f"   Files: {len(input_files)}\n")
    
    output_files, summary = await batch_process(
        input_files,
        args.output_dir,
        args.voice,
        args.rate,
        args.pitch,
        args.volume,
        args.generate_subtitles
    )
    
    print(f"\n{summary}")
    print(f"\nOutput files saved to: {os.path.abspath(args.output_dir)}")


if __name__ == "__main__":
    asyncio.run(main())
