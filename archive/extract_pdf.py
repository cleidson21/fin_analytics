from pypdf import PdfReader
import sys

reader = PdfReader(r"C:\Users\Cleidson\Pictures\fin_analytics_v2\FinAnalytics V2 - localhost_8000_docs.pdf")
text = ""
for i in range(min(5, len(reader.pages))):
    text += reader.pages[i].extract_text() + "\n"

with open(r"C:\Users\Cleidson\Pictures\fin_analytics_v2\archive\pdf_extract.txt", "w", encoding="utf-8") as f:
    f.write(text)
