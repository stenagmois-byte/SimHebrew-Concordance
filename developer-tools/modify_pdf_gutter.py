import pypdf

def mirror_book_margins(input_pdf, output_pdf):
    """
    Shifts a fixed Calibre PDF (72pt Left, 38pt Right) into an alternating
    print layout: 0.75" (54pt) inside margins and >0.25" outside margins.
    """
    reader = pypdf.PdfReader(input_pdf)
    writer = pypdf.PdfWriter()
    
    # 8.5 x 11 inches in PostScript points
    PAGE_WIDTH = 612.0
    PAGE_HEIGHT = 792.0

    for idx, page in enumerate(reader.pages):
        page_num = idx + 1  # 1-based page indexing
        
        # Create a brand new blank 8.5x11 page canvas
        transformed_page = writer.add_blank_page(width=PAGE_WIDTH, height=PAGE_HEIGHT)
        
        if page_num % 2 != 0:
            # --- ODD PAGE (Right Hand) ---
            # Target Gutter (Left): 54pt. Calibre Left: 72pt.
            # We must shift the entire text block LEFT by 18 points.
            shift_x = -18.0
        else:
            # --- EVEN PAGE (Left Hand) ---
            # Target Gutter (Right): 54pt. Calibre Right: 38pt.
            # We must shift the entire text block LEFT by 16 points.
            shift_x = -16.0

        # Merge the original page contents onto the new page with the exact shift
        transformed_page.merge_translated_page(page, tx=shift_x, ty=0)

    # Save the polished, print-ready file
    with open(output_pdf, "wb") as out_file:
        writer.write(out_file)
    print(f"Success! Print-ready PDF saved as: {output_pdf}")

# Run the script on your files
# Target the file directly inside your computer's Calibre Library folder
input_path = "C:/Users/Bob/Calibre Library/D. Robert MacDonald/The Psalms (117)/The Psalms - D. Robert MacDonald.pdf"
output_path = "C:/Users/YourName/Desktop/The_Psalms_Amazon_KDP.pdf"

mirror_book_margins(input_path, output_path)
