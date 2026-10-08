import os
import re
import html
from bs4 import BeautifulSoup

# Global Mapping based on Decimal HTML / Unicode values
HEBREW_DECIMAL_GEMATRIA = {
    1488: 1, 1489: 2, 1490: 3, 1491: 4, 1492: 5, 1493: 6, 1494: 7, 1495: 8, 1496: 9,
    1497: 10, 1499: 20, 1500: 30, 1502: 40, 1504: 50, 1505: 60, 1506: 70, 1508: 80,
    1510: 90, 1511: 100, 1512: 200, 1513: 300, 1514: 400,
    # Final Letters (Otiot Sofiyot)
    1498: 20, 1501: 40, 1503: 50, 1507: 80, 1509: 90
}

def calculate_gematria_from_html(raw_html_text):
    unescaped_text = html.unescape(raw_html_text)
    total = 0
    for char in unescaped_text:
        char_code = ord(char)
        if char_code in HEBREW_DECIMAL_GEMATRIA:
            total += HEBREW_DECIMAL_GEMATRIA[char_code]
    return total

def get_color_class(val):
    if val < 50:
        return "gem-low"
    elif val < 200:
        return "gem-mid-low"
    elif val < 400:
        return "gem-mid"
    elif val < 600:
        return "gem-mid-high"
    else:
        return "gem-high"

def inject_gematria_to_files(directory_path):
    if not os.path.exists(directory_path):
        return

    for filename in os.listdir(directory_path):
        if filename.endswith(".html"):
            # Clean length check using index [0] to extract just the text name
            base_name = os.path.splitext(filename)[0]
            if len(base_name) == 0 or len(base_name) > 2:
                continue
                
            file_path = os.path.join(directory_path, filename)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read()
                
            soup = BeautifulSoup(raw_content, 'html.parser')
            modified = False
            
            # 1. Update Layout Headers
            ref_header = soup.find('td', class_='tdch9')
            if ref_header and ref_header.get('colspan') == '2':
                ref_header['colspan'] = '1'
                gem_header = soup.new_tag('td', attrs={'class': 'tdch10'})
                gem_header.string = "Gem"
                ref_header.insert_after(gem_header)
                modified = True
            
            # 2. Update All Multi-Line Concordance Rows
            data_blocks = soup.find_all('div', class_='level2')
            for block in data_blocks:
                hebrew_cells = block.find_all('div', class_='tdcl6')
                ref_cells = block.find_all('div', class_='tdcl9')
                
                for i, ref_cell in enumerate(ref_cells):
                    next_sibling = ref_cell.find_next_sibling('div')
                    if next_sibling and 'tdcl_gem' in next_sibling.get('class', []):
                        continue 
                    
                    if i < len(hebrew_cells):
                        raw_cell_str = "".join(str(item) for item in hebrew_cells[i].contents)
                        gematria_val = calculate_gematria_from_html(raw_cell_str)
                        
                        if gematria_val > 0:
                            color_class = get_color_class(gematria_val)
                            new_cell = soup.new_tag('div', attrs={'class': f'tdcl_gem {color_class}'})
                            new_cell.string = str(gematria_val)
                            ref_cell.insert_after(new_cell)
                            modified = True
            
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    # FIXED LINE: We use standard HTML rules but encode as 'ascii'.
                    # This forces Python to safely turn Hebrew letters back into codes like &#1492;
                    output_bytes = soup.encode(formatter="html", encoding="ascii")
                    f.write(output_bytes.decode('ascii'))
                print(f"Processed entity-safe file: {filename}")

if __name__ == "__main__":
    inject_gematria_to_files(".")
