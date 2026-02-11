"""
Sentence Splitter Script
Splits text from a source file into separate files, each containing N sentences.
A sentence is defined as text ending with a period (.)
"""

import os
import re
from pathlib import Path


def split_into_sentences(text: str) -> list[str]:
    """
    Split text into sentences based on period (.) as delimiter.
    Handles edge cases like abbreviations and decimal numbers.
    """
    # Split by period followed by space or end of text
    # This regex splits on periods followed by whitespace or end of string
    sentences = re.split(r'\.(?:\s+|$)', text)
    
    # Clean up: remove empty strings and strip whitespace
    sentences = [s.strip() for s in sentences if s.strip()]
    
    return sentences


def split_sentences_to_files(
    input_file: str,
    output_dir: str = "extracted",
    sentences_per_file: int = 1,
    prefix: str = "sentence"
) -> int:
    """
    Read a text file, split into sentences, and write N sentences per output file.
    
    Args:
        input_file: Path to the input text file
        output_dir: Directory to save output files (created if doesn't exist)
        sentences_per_file: Number of sentences per output file
        prefix: Prefix for output filenames
        
    Returns:
        Number of files created
    """
    # Read input file
    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Split into sentences
    sentences = split_into_sentences(text)
    
    if not sentences:
        print("No sentences found in the input file.")
        return 0
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Group sentences and write to files
    file_count = 0
    for i in range(0, len(sentences), sentences_per_file):
        # Get N sentences for this file
        sentence_group = sentences[i:i + sentences_per_file]
        
        # Create filename with zero-padded number
        file_count += 1
        filename = f"{prefix}_{file_count:04d}.txt"
        filepath = output_path / filename
        
        # Join sentences with period and write to file
        content = ". ".join(sentence_group) + "."
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Created: {filepath}")
    
    return file_count


def main():
    """Main function with example usage."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Split text file into multiple files with N sentences each."
    )
    parser.add_argument(
        "input_file",
        help="Path to the input text file"
    )
    parser.add_argument(
        "-n", "--sentences",
        type=int,
        default=1,
        help="Number of sentences per output file (default: 1)"
    )
    parser.add_argument(
        "-o", "--output-dir",
        default="extracted",
        help="Output directory (default: extracted)"
    )
    parser.add_argument(
        "-p", "--prefix",
        default="sentence",
        help="Prefix for output filenames (default: sentence)"
    )
    
    args = parser.parse_args()
    
    print(f"Processing: {args.input_file}")
    print(f"Sentences per file: {args.sentences}")
    print(f"Output directory: {args.output_dir}")
    print("-" * 40)
    
    try:
        count = split_sentences_to_files(
            input_file=args.input_file,
            output_dir=args.output_dir,
            sentences_per_file=args.sentences,
            prefix=args.prefix
        )
        print("-" * 40)
        print(f"Successfully created {count} files.")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
