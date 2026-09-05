import os
import tempfile
from pathlib import Path
import pandas as pd
from docx import Document
from PyPDF2 import PdfReader
from typing import Optional


def detect_header_row(df: pd.DataFrame) -> Optional[int]:
    """
    Detect which row contains the actual headers.
    Looks for rows with fewer empty values and more header-like text.
    """
    for idx in range(min(20, len(df))):  # Check first 20 rows
        row = df.iloc[idx]
        row_values = [val for val in row if not pd.isna(val)]
        non_null_count = len(row_values)

        # If more than 50% of columns have values, likely a header row
        if non_null_count >= len(df.columns) * 0.5:
            # Check if values look like headers (short text, no long sentences)
            if row_values and all(
                isinstance(val, str) and len(val.strip()) < 50 and val.strip() != ""
                for val in row_values
            ):
                return idx

    return None


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean dataframe by detecting proper headers and removing empty rows.
    """
    # Ensure every cell is in a safe string-compatible form
    df = df.applymap(lambda value: "" if pd.isna(value) else value)

    # Try to detect header row
    header_row = detect_header_row(df)

    if header_row is not None and header_row > 0:
        # Set proper headers
        new_headers = df.iloc[header_row].fillna('').astype(str)
        df = df.iloc[header_row + 1:].reset_index(drop=True)
        df.columns = new_headers

    # Remove completely empty rows
    df = df.dropna(how='all').reset_index(drop=True)

    # Remove columns that are completely empty
    df = df.dropna(axis=1, how='all')

    # Clean column names - remove "Unnamed" if there's a better name
    cleaned_columns = []
    for col in df.columns:
        if 'Unnamed' in str(col) or str(col).strip() == '':
            cleaned_columns.append(f"Column_{len(cleaned_columns) + 1}")
        else:
            cleaned_columns.append(str(col).strip())

    df.columns = cleaned_columns
    return df


def extract_pdf(file_path: str) -> str:
    """Extract text from a PDF file."""
    text = ""
    reader = PdfReader(file_path)
    total_pages = len(reader.pages)
    
    text += f"📄 PDF DOCUMENT: {os.path.basename(file_path)}\n"
    text += f"Total Pages: {total_pages}\n"
    text += "=" * 80 + "\n\n"

    for page_num, page in enumerate(reader.pages, start=1):
        page_text = page.extract_text()
        
        if page_text:
            text += f"--- PAGE {page_num} of {total_pages} ---\n"
            text += page_text + "\n"
            text += "-" * 80 + "\n\n"

    return text


def extract_docx(file_path: str) -> str:
    """Extract text from a DOCX file."""
    document = Document(file_path)
    text = ""
    
    text += f"📝 WORD DOCUMENT: {os.path.basename(file_path)}\n"
    text += f"Total Paragraphs: {len(document.paragraphs)}\n"
    text += "=" * 80 + "\n\n"

    for idx, para in enumerate(document.paragraphs, start=1):
        if para.text.strip():
            text += f"[Paragraph {idx}]\n"
            text += para.text + "\n\n"

    return text


def extract_txt(file_path: str) -> str:
    """Extract text from TXT file."""
    with open(file_path, "r", encoding="utf-8") as file:
        content = file.read()
    
    text = f"📋 TEXT FILE: {os.path.basename(file_path)}\n"
    text += f"Character Count: {len(content)}\n"
    text += f"Line Count: {len(content.splitlines())}\n"
    text += "=" * 80 + "\n\n"
    text += content
    
    return text


def extract_csv(file_path: str) -> str:
    """Convert CSV rows into readable format."""
    try:
        df = pd.read_csv(file_path, encoding='utf-8', dtype=str, keep_default_na=False)
    except Exception:
        df = pd.read_csv(file_path, encoding='latin-1', dtype=str, keep_default_na=False)

    # Clean the dataframe
    df = clean_dataframe(df)

    text = f"📊 CSV FILE: {os.path.basename(file_path)}\n"
    text += f"Total Rows: {len(df)}\n"
    text += f"Total Columns: {len(df.columns)}\n"
    text += "=" * 80 + "\n\n"

    text += dataframe_to_text(df)
    return text


def extract_excel(file_path: str, specific_sheet: Optional[str] = None) -> str:
    """Read Excel file and extract all sheets or a specific sheet."""
    excel_file = pd.ExcelFile(file_path)
    text = ""

    text += f"📈 EXCEL FILE: {os.path.basename(file_path)}\n"
    text += f"Total Sheets: {len(excel_file.sheet_names)}\n"
    text += f"Sheet Names: {', '.join(excel_file.sheet_names)}\n"
    text += "=" * 80 + "\n\n"

    sheets_to_process = [specific_sheet] if specific_sheet else excel_file.sheet_names

    for sheet_name in sheets_to_process:
        try:
            df = pd.read_excel(
                file_path,
                sheet_name=sheet_name,
                header=None,
                dtype=str,
                keep_default_na=False
            )

            if not isinstance(df, pd.DataFrame):
                df = pd.DataFrame(df)

            # Clean the dataframe
            df = clean_dataframe(df)

            if df.empty:
                text += f"🗂️ SHEET: {sheet_name} - [EMPTY]\n\n"
                continue

            text += f"🗂️ SHEET: {sheet_name}\n"
            text += f"Rows: {len(df)} | Columns: {len(df.columns)}\n"
            text += "-" * 80 + "\n\n"

            text += dataframe_to_text(df, sheet_name=sheet_name)
            text += "\n" + "=" * 80 + "\n\n"

        except Exception as e:
            text += f"⚠️ Error reading sheet '{sheet_name}': {str(e)}\n\n"

    return text


def extract_test_case_text_from_file_path(file_path: str) -> str:
    """Extract readable manual test case text from a saved file path."""
    suffix = Path(file_path).suffix.lower()

    if suffix == ".pdf":
        return extract_pdf(file_path)
    if suffix == ".docx":
        return extract_docx(file_path)
    if suffix == ".txt":
        return extract_txt(file_path)
    if suffix == ".csv":
        return extract_csv(file_path)
    if suffix in {".xls", ".xlsx"}:
        return extract_excel(file_path)

    raise ValueError(f"Unsupported file type: {suffix}")


def extract_test_case_text(uploaded_file) -> str:
    """Extract readable text from a file-like upload object."""
    suffix = Path(uploaded_file.name).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = tmp.name

    try:
        return extract_test_case_text_from_file_path(tmp_path)
    finally:
        try:
            os.remove(tmp_path)
        except OSError:
            pass


def dataframe_to_text(df: pd.DataFrame, sheet_name: str = None) -> str:
    """
    Convert dataframe into structured, readable text.
    Only shows rows with actual content.
    """
    final_text = ""
    
    # Show column headers
    final_text += "📋 COLUMNS:\n"
    for idx, col in enumerate(df.columns, start=1):
        final_text += f"  {idx}. {col}\n"
    final_text += "\n" + "=" * 80 + "\n\n"
    
    # Track rows with actual content
    rows_with_content = 0
    
    for index, row in df.iterrows():
        # Check if row has any meaningful content
        has_content = any(
            pd.notna(val) and str(val).strip() != '' 
            for val in row
        )
        
        if not has_content:
            continue
        
        rows_with_content += 1
        
        final_text += "┌" + "─" * 78 + "┐\n"
        final_text += f"│ {'ROW ' + str(rows_with_content):^76} │\n"
        final_text += "├" + "─" * 78 + "┤\n"
        
        for column in df.columns:
            value = row[column]
            
            # Skip if value is empty/null
            if pd.isna(value) or str(value).strip() == '':
                continue
            
            # Handle different data types
            if isinstance(value, float):
                value = f"{value:.2f}" if value % 1 else str(int(value))
            else:
                value = str(value).strip()
            
            # Format output
            final_text += f"│ 🔹 {column}:\n"
            
            # Wrap long text
            if len(value) > 70:
                words = value.split()
                line = "│     "
                for word in words:
                    if len(line) + len(word) + 1 > 76:
                        final_text += line + "\n"
                        line = "│     " + word + " "
                    else:
                        line += word + " "
                final_text += line.rstrip() + "\n"
            else:
                final_text += f"│     {value}\n"
            
            final_text += "│\n"
        
        final_text += "└" + "─" * 78 + "┘\n\n"
    
    if rows_with_content == 0:
        final_text += "⚠️ No content rows found in this dataset.\n\n"

    return final_text


def _filter_out_unwanted_sections(text: str) -> str:
    """Remove unwanted section headers from extracted text."""
    filtered_lines = []
    for line in text.splitlines():
        normalized = line.strip().lower()
        if normalized in {"aid", "document history"}:
            continue
        if normalized.startswith("aid:") or normalized.startswith("document history:"):
            continue
        filtered_lines.append(line)

    return "\n".join(filtered_lines)


def extract_text(file_path: str, 
                 preview_only: bool = False, 
                 preview_lines: int = 50,
                 excel_sheet: Optional[str] = None) -> str:
    """
    Main extraction function.
    
    Args:
        file_path: Path to the file
        preview_only: If True, return only first N lines
        preview_lines: Number of lines to preview
        excel_sheet: Specific Excel sheet name (None = all sheets)
    
    Returns:
        Extracted and formatted text
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    extension = os.path.splitext(file_path)[1].lower()
    
    # Route to appropriate extractor
    if extension == ".pdf":
        extracted_text = extract_pdf(file_path)
    elif extension == ".docx":
        extracted_text = extract_docx(file_path)
    elif extension == ".xlsx":
        extracted_text = extract_excel(file_path, specific_sheet=excel_sheet)
    elif extension == ".csv":
        extracted_text = extract_csv(file_path)
    elif extension == ".txt":
        extracted_text = extract_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: {extension}")

    extracted_text = _filter_out_unwanted_sections(extracted_text)
    
    # Return preview or full text
    if preview_only:
        lines = extracted_text.split('\n')
        preview = '\n'.join(lines[:preview_lines])
        
        if len(lines) > preview_lines:
            preview += f"\n\n... [Showing {preview_lines} of {len(lines)} lines] ..."
        
        return preview
    
    return extracted_text