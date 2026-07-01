"""
TTS Pipeline - Unified CLI for Text-to-Speech Dataset Preparation

Usage:
    python pipeline.py pdf2txt <input.pdf> <output.txt>
    python pipeline.py normalize <input.txt> <output.txt>
    python pipeline.py split <input.txt> [-n N] [-o DIR] [-p PREFIX]
    python pipeline.py batch [--input-dir DIR] [--files FILE...] [--output-dir DIR]
    python pipeline.py merge [-i DIR] [-o FILE] [-s SILENCE]
    python pipeline.py all <input.pdf> [options]  # Full pipeline
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Reconfigure stdout/stderr to handle UTF-8 emojis on Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass


# Import functions from existing modules
from scripts.pdf2txt import pdf_to_txt
from scripts.normalize_for_tts import normalize_for_tts
from scripts.split_sentences import split_sentences_to_files
from scripts.run_batch import run_batch_tts, VOICE, OUTPUT_DIRECTORY
from scripts.merge_mp3 import merge_audio_files


def cmd_merge(args):
    """Merge MP3 audio files."""
    merge_audio_files(
        input_dir=args.input_dir,
        output_file=args.output,
        silence_between_ms=args.silence
    )



def cmd_pdf2txt(args):
    """Convert PDF to text."""
    pdf_to_txt(args.input, args.output)


def cmd_normalize(args):
    """Normalize text for TTS."""
    normalize_for_tts(args.input, args.output)


def cmd_split(args):
    """Split text into sentence files."""
    count = split_sentences_to_files(
        input_file=args.input,
        output_dir=args.output_dir,
        sentences_per_file=args.sentences,
        prefix=args.prefix
    )
    print(f"\n✅ Created {count} files in '{args.output_dir}'")


def cmd_batch(args):
    """Run batch TTS processing."""
    asyncio.run(run_batch_tts(
        input_files=args.files,
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        voice=args.voice
    ))


def cmd_all(args):
    """Run the full pipeline: PDF → TXT → Normalize → Split → TTS."""
    base_dir = Path(args.input).parent
    if base_dir == Path(''):
        base_dir = Path('.')
    pdf_path = args.input
    
    # Step 1: PDF to TXT
    txt_path = str(base_dir / "input.txt")
    print(f"\n📄 Step 1: Converting PDF to text...")
    pdf_to_txt(pdf_path, txt_path)
    
    # Step 2: Normalize
    normalized_path = str(base_dir / "input_normalized.txt")
    print(f"\n🧹 Step 2: Normalizing text for TTS...")
    normalize_for_tts(txt_path, normalized_path)
    
    # Step 3: Split sentences
    output_dir = args.output_dir or str(base_dir / "extracted")
    print(f"\n✂️  Step 3: Splitting into sentences...")
    count = split_sentences_to_files(
        input_file=normalized_path,
        output_dir=output_dir,
        sentences_per_file=args.sentences,
        prefix=args.prefix
    )
    
    print(f"\n✅ Pipeline complete! Created {count} text files in '{output_dir}'")
    
    # Step 4: Run TTS batch (optional)
    if args.tts:
        print(f"\n🎤 Step 4: Running batch TTS on extracted sentences...")
        asyncio.run(run_batch_tts(
            input_dir=output_dir,
            output_dir=args.tts_output or "./mp3",
            voice=args.voice
        ))


def main():
    parser = argparse.ArgumentParser(
        description="TTS Pipeline - Unified CLI for Text-to-Speech Dataset Preparation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pipeline.py pdf2txt book.pdf book.txt
  python pipeline.py normalize input.txt normalized.txt
  python pipeline.py split normalized.txt -n 2 -o ./sentences
  python pipeline.py batch
  python pipeline.py merge -i ./mp3 -o ./mp3/merged.mp3 -s 500
  python pipeline.py all book.pdf --tts
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # pdf2txt command
    p_pdf = subparsers.add_parser("pdf2txt", help="Convert PDF to text file")
    p_pdf.add_argument("input", help="Input PDF file path")
    p_pdf.add_argument("output", help="Output text file path")
    p_pdf.set_defaults(func=cmd_pdf2txt)
    
    # normalize command
    p_norm = subparsers.add_parser("normalize", help="Normalize text for TTS")
    p_norm.add_argument("input", help="Input text file path")
    p_norm.add_argument("output", help="Output normalized text file path")
    p_norm.set_defaults(func=cmd_normalize)
    
    # split command
    p_split = subparsers.add_parser("split", help="Split text into sentence files")
    p_split.add_argument("input", help="Input text file path")
    p_split.add_argument("-n", "--sentences", type=int, default=1,
                         help="Sentences per file (default: 1)")
    p_split.add_argument("-o", "--output-dir", default="extracted",
                         help="Output directory (default: extracted)")
    p_split.add_argument("-p", "--prefix", default="sentence",
                         help="Filename prefix (default: sentence)")
    p_split.set_defaults(func=cmd_split)
    
    # batch command
    p_batch = subparsers.add_parser("batch", help="Run batch TTS processing")
    p_batch.add_argument("-i", "--input-dir", default="./extracted",
                         help="Input directory with .txt/.srt files (default: ./extracted)")
    p_batch.add_argument("-f", "--files", nargs="+",
                         help="Specific input files to process")
    p_batch.add_argument("-o", "--output-dir", default="./mp3",
                         help="Output directory for audio (default: ./mp3)")
    p_batch.add_argument("-v", "--voice", default="ta-IN-PallaviNeural",
                         help="Voice name (default: ta-IN-PallaviNeural)")
    p_batch.set_defaults(func=cmd_batch)
    
    # merge command
    p_merge = subparsers.add_parser("merge", help="Merge MP3 files into a single file")
    p_merge.add_argument("-i", "--input-dir", default="./mp3",
                         help="Directory containing MP3 files to merge (default: ./mp3)")
    p_merge.add_argument("-o", "--output", default=None,
                         help="Output merged file path (default: input-dir/merged.mp3)")
    p_merge.add_argument("-s", "--silence", type=int, default=500,
                         help="Silence in milliseconds between tracks (default: 500)")
    p_merge.set_defaults(func=cmd_merge)
    
    # all command (full pipeline)
    p_all = subparsers.add_parser("all", help="Run full pipeline: PDF → TXT → Normalize → Split")

    p_all.add_argument("input", help="Input PDF file path")
    p_all.add_argument("-n", "--sentences", type=int, default=1,
                       help="Sentences per file (default: 1)")
    p_all.add_argument("-o", "--output-dir", default=None,
                       help="Output directory for split files")
    p_all.add_argument("-p", "--prefix", default="sentence",
                       help="Filename prefix (default: sentence)")
    p_all.add_argument("--tts", action="store_true",
                       help="Also run TTS batch processing after splitting")
    p_all.add_argument("-v", "--voice", default="ta-IN-PallaviNeural",
                       help="Voice for TTS (default: ta-IN-PallaviNeural)")
    p_all.add_argument("--tts-output", default=None,
                       help="Output directory for TTS audio (default: ./mp3)")
    p_all.set_defaults(func=cmd_all)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        sys.exit(1)
    
    args.func(args)


if __name__ == "__main__":
    main()
