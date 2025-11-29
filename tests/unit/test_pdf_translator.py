import pytest
from unittest.mock import MagicMock, patch
import fitz
from src.pdf_translation.pdf_translator import PdfTranslator

# Mock the LLM translation function for isolated testing
def mock_translate_text_with_llm(text: str, target_language: str) -> str:
    """Mock translation function for testing purposes."""
    return f"Mock Translated to {target_language}: {text}"

@patch('src.pdf_translation.pdf_translator.PdfTranslator._translate_text_with_llm', side_effect=mock_translate_text_with_llm)
def test_translate_pdf_success(mock_llm_translate, tmp_path):
    """
    Test successful translation of a PDF file.
    """
    # Create a dummy PDF file
    input_pdf_path = tmp_path / "input.pdf"
    output_pdf_path = tmp_path / "output.pdf"
    
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Hello World", fontsize=12)
    page.insert_text((72, 100), "This is a test.", fontsize=10)
    doc.save(input_pdf_path)
    doc.close()

    target_language = "French"
    translator = PdfTranslator(target_language)
    translator.translate_pdf(str(input_pdf_path), str(output_pdf_path))

    # Assert that the output PDF is created
    assert output_pdf_path.exists()

    # Verify content of the translated PDF
    translated_doc = fitz.open(output_pdf_path)
    assert translated_doc.page_count == 1
    translated_page = translated_doc.load_page(0)
    
    text_blocks = translated_page.get_text("blocks")
    translated_texts = [block[4] for block in text_blocks] # block[4] contains the text
    
    expected_translation1 = "Mock Translated to French: Hello World"
    expected_translation2 = "Mock Translated to French: This is a test."

    assert expected_translation1 in translated_texts
    assert expected_translation2 in translated_texts
    
    translated_doc.close()

def test_translate_text_with_llm_success():
    """
    Test the internal _translate_text_with_llm function for successful translation.
    """
    translator = PdfTranslator(target_language="Spanish")
    text = "Hello"
    translated_text = translator._translate_text_with_llm(text)
    assert "T Hello" in translated_text