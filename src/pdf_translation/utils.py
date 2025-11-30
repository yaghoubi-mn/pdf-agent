

import fitz


def get_or_register_font(doc: fitz.Document, page: fitz.Page, orginal_font_name, font_cache):

    if orginal_font_name in font_cache:
        return font_cache[orginal_font_name]

    font_xref = None

    clean_name = orginal_font_name.split("+")[-1]

    for f in page.get_fonts():
        xref = f[0]
        basefont = f[3]
        name = f[4]

        if orginal_font_name in basefont or orginal_font_name in name or clean_name in basefont:
            font_xref = xref
            break

    if font_xref:
        try:
            font_buffer = doc.extract_font(font_xref)
            safe_font_name = f"custom_{xref}"
            page.insert_font(fontname=safe_font_name, fontbuffer=font_buffer[-1])
            font_cache[orginal_font_name] = safe_font_name
            return safe_font_name
        except Exception as e:
            logging.warning(f"failed to extract/register font {orginal_font_name}: {e}")

    font_cache[orginal_font_name] = "helv"
    return "helv"