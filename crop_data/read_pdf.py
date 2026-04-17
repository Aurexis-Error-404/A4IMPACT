import os, sys, glob

# Fix encoding
sys.stdout.reconfigure(encoding='utf-8')

pdf_dir = os.path.join(os.path.dirname(__file__), '..', 'Project_role')
pdf_files = glob.glob(os.path.join(pdf_dir, '*.pdf'))
pdf_path = pdf_files[0]

from PyPDF2 import PdfReader
reader = PdfReader(pdf_path)
for i, page in enumerate(reader.pages):
    print(f"\n--- Page {i+1} ---")
    print(page.extract_text())
