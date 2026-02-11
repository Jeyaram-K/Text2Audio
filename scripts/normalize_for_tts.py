"""
TTS Text Normalization Script
Cleans input.txt for text-to-speech processing
"""

import re
from pathlib import Path

def normalize_for_tts(input_path: str, output_path: str):
    """
    Normalize text for TTS by:
    1. Removing page numbers (standalone numbers on lines)
    2. Removing bullet points and formatting markers
    3. Joining broken sentences across lines
    4. Removing special characters not suitable for TTS
    5. Cleaning up whitespace and empty lines
    6. Removing chapter headers and section numbers
    """
    
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Skip standalone page numbers (just digits)
        if re.match(r'^\d{1,3}$', line):
            continue
        
        # Skip table of contents style lines (Chapter X:)
        if re.match(r'^Chapter \d+:$', line):
            continue
        
        # Skip separator lines (underscores, dashes)
        if re.match(r'^[_\-=]{3,}$', line):
            continue
        
        # Remove bullet points at the start
        line = re.sub(r'^[•\-\*]\s*', '', line)
        
        # Remove numbering like "1." or "A." at the start (but keep the content)
        line = re.sub(r'^[A-Z0-9]+\.\s*', '', line)
        
        # Remove brackets like [NEW], [DELETE], [AI with Thiru], etc.
        line = re.sub(r'\[.*?\]', '', line)
        
        # Remove URLs and social media handles
        line = re.sub(r'@\w+', '', line)
        line = re.sub(r'https?://\S+', '', line)
        
        # Replace special characters
        line = line.replace('&', ' and ')
        line = line.replace('>', ' greater than ')
        line = line.replace('<', ' less than ')
        line = line.replace('->', ' leads to ')
        
        # Clean up mathematical/technical notation for speech
        line = re.sub(r'\+\s*ve', 'positive', line)
        line = re.sub(r'\-\s*ve', 'negative', line)
        
        # Remove extra whitespace
        line = re.sub(r'\s+', ' ', line).strip()
        
        # Skip lines that are now empty after cleaning
        if not line:
            continue
            
        cleaned_lines.append(line)
    
    # Join lines into paragraphs (sentences that end mid-line continue on next)
    paragraphs = []
    current_paragraph = []
    
    for line in cleaned_lines:
        current_paragraph.append(line)
        
        # Check if line ends with sentence-ending punctuation
        if re.search(r'[.!?)]$', line):
            # Join and add paragraph
            full_text = ' '.join(current_paragraph)
            paragraphs.append(full_text)
            current_paragraph = []
    
    # Don't forget leftover content
    if current_paragraph:
        paragraphs.append(' '.join(current_paragraph))
    
    # Final cleanup: merge short fragments and remove duplicates
    final_paragraphs = []
    for para in paragraphs:
        # Skip very short lines (likely artifacts)
        if len(para) < 10:
            continue
        # Skip copyright/title page content
        if 'Copyright' in para or 'All Rights Reserved' in para:
            continue
        # Remove repeated spaces
        para = re.sub(r'\s+', ' ', para).strip()
        if para:
            final_paragraphs.append(para)
    
    # Write output
    output_text = '\n\n'.join(final_paragraphs)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output_text)
    
    print(f"Normalized text written to: {output_path}")
    print(f"Original lines: {len(lines)}")
    print(f"Output paragraphs: {len(final_paragraphs)}")

if __name__ == '__main__':
    base_dir = Path(__file__).parent
    input_file = base_dir / 'raw.txt'
    output_file = base_dir / 'input.txt'
    
    normalize_for_tts(str(input_file), str(output_file))
