#!/usr/bin/env python3
"""
Convert Markdown report to PDF using weasyprint.
"""

import markdown
from weasyprint import HTML
from pathlib import Path
import re

def markdown_to_pdf(md_file, pdf_file):
    """Convert markdown file to PDF."""
    # Read markdown content
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Remove image references (they won't render properly in simple conversion)
    # We'll note that figures are attached separately
    md_content = re.sub(r'!\[.*?\]\(.*?\)', '', md_content)
    
    # Convert markdown to HTML
    html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
    
    # Add basic CSS styling for professional look
    styled_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: Letter;
                margin: 1in;
            }}
            body {{
                font-family: 'Helvetica', 'Arial', sans-serif;
                font-size: 11pt;
                line-height: 1.5;
                color: #333;
            }}
            h1 {{
                color: #2c3e50;
                font-size: 20pt;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                margin-top: 20px;
                page-break-before: avoid;
            }}
            h2 {{
                color: #2c3e50;
                font-size: 16pt;
                border-bottom: 2px solid #95a5a6;
                padding-bottom: 5px;
                margin-top: 15px;
                page-break-after: avoid;
            }}
            h3 {{
                color: #34495e;
                font-size: 13pt;
                margin-top: 12px;
                page-break-after: avoid;
            }}
            p {{
                margin: 8px 0;
                text-align: justify;
            }}
            ul, ol {{
                margin: 8px 0;
                padding-left: 25px;
            }}
            li {{
                margin: 4px 0;
            }}
            strong {{
                color: #2c3e50;
            }}
            code {{
                background-color: #f4f4f4;
                padding: 2px 5px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
                font-size: 10pt;
            }}
            pre {{
                background-color: #f4f4f4;
                padding: 10px;
                border-left: 3px solid #3498db;
                overflow-x: auto;
                font-size: 9pt;
                page-break-inside: avoid;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 10px 0;
                font-size: 10pt;
                page-break-inside: avoid;
            }}
            th {{
                background-color: #3498db;
                color: white;
                padding: 8px;
                text-align: left;
                font-weight: bold;
            }}
            td {{
                padding: 6px 8px;
                border-bottom: 1px solid #ddd;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            hr {{
                border: none;
                border-top: 2px solid #3498db;
                margin: 15px 0;
            }}
            .page-break {{
                page-break-after: always;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """
    
    # Convert HTML to PDF
    HTML(string=styled_html).write_pdf(pdf_file)
    print(f"✓ Created PDF: {pdf_file}")

def main():
    """Convert the health DQA report to PDF."""
    md_file = Path('health-dqa-report.md')
    pdf_file = Path('health-dqa-report.pdf')
    
    if not md_file.exists():
        print(f"Error: {md_file} not found")
        return
    
    print("Converting Markdown to PDF...")
    markdown_to_pdf(md_file, pdf_file)
    print("\n✓ PDF conversion complete!")
    print(f"  Output: {pdf_file}")
    print("\nNote: Figures are saved separately in figures/ directory.")
    print("      Attach dqa-score-by-state.png and dqa-score-trend.png with the PDF.")

if __name__ == '__main__':
    main()
