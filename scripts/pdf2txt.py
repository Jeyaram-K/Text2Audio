import pdfplumber

def pdf_to_txt(pdf_path, txt_path):
    """Convert a PDF file to a text file using pdfplumber."""
    with pdfplumber.open(pdf_path) as pdf:
        text = ''
        for page in pdf.pages:
            text += page.extract_text() or ''
            text += '\n'
    
    with open(txt_path, 'w', encoding='utf-8') as txt_file:
        txt_file.write(text)
    
    print(f"Converted {pdf_path} to {txt_path}")

if __name__ == "__main__":
    pdf_to_txt('raw.pdf', 'raw.txt')