"""
GST Invoice Extractor
Extracts: Supplier Name, Supplier GSTIN, Invoice No., Date, Total Amount
from GST Tax Invoice PDFs using pdfplumber + regex.
"""

import re
import pdfplumber
from pathlib import Path


# ── Regex patterns ────────────────────────────────────────────────────────────

PATTERNS = {
    "supplier_name": [
        r"Supplier\s+Name\s*[:\-]?\s*(.+?)(?:\s{2,}|\t|Invoice\s+No|$)",
        r"Supplier\s*Name\s*[:\-]\s*(.+)",
    ],
    "supplier_gstin": [
        r"Supplier\s+GSTIN\s*[:\-]?\s*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})",
        r"Supplier\s*GSTIN\s*[:\-]\s*([A-Z0-9]{15})",
    ],
    "invoice_no": [
        r"Invoice\s+No\s*[:\-]?\s*(INV[-/]?\w+)",
        r"Invoice\s*No\s*[:\-]\s*(\S+)",
    ],
    "date": [
        r"Date\s*[:\-]?\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",
        r"Date\s*[:\-]\s*(\d{2}-\d{2}-\d{4})",
    ],
    "total": [
        # Match the last numeric value on a line containing "Total" in the item table
        r"(?:Total|TOTAL)\s+([\d,]+(?:\.\d{1,2})?)\s*$",
        # Fallback: rightmost number in a row that has known GST items
        r"\bTotal\b.*?([\d,]+)\s*$",
    ],
}

GSTIN_RE = re.compile(
    r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b"
)


def _find(text: str, field: str) -> str | None:
    """Try each regex pattern for a field; return first match or None."""
    for pat in PATTERNS[field]:
        m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
        if m:
            return m.group(1).strip()
    return None


def _extract_total_from_lines(lines: list[str]) -> str | None:
    """
    Walk lines bottom-up; find the last purely numeric token that looks like
    an invoice total (>= 2 digits, no header context).
    Strategy: collect all standalone numbers on lines that contain 'Total'
    or GST-related keywords, take the last/largest.
    """
    candidates = []
    for line in lines:
        # Skip header rows
        if re.search(r"\b(Item|HSN|Qty|Rate|Taxable)\b", line, re.I):
            continue
        if re.search(r"\bTotal\b", line, re.I):
            nums = re.findall(r"[\d,]+(?:\.\d{1,2})?", line)
            if nums:
                # Last number on the line is typically the total
                candidates.append(nums[-1].replace(",", ""))
    return candidates[-1] if candidates else None


def _extract_total_fallback(lines: list[str]) -> str | None:
    """
    Last resort: find the rightmost number that appears after a GST% column.
    Works for structured tables where total is the last column.
    """
    for line in reversed(lines):
        # Must have at least 4 numbers (qty, rate, taxable, total columns area)
        nums = re.findall(r"[\d,]+(?:\.\d{1,2})?", line)
        if len(nums) >= 4:
            return nums[-1].replace(",", "")
    return None


def extract_from_text(text: str) -> dict:
    """Extract all 5 fields from raw page text."""
    lines = text.splitlines()

    supplier_name = _find(text, "supplier_name")
    supplier_gstin = _find(text, "supplier_gstin")
    invoice_no = _find(text, "invoice_no")
    date = _find(text, "date")

    # Total: try patterns first, then heuristic line scan
    total = _find(text, "total")
    if not total:
        total = _extract_total_from_lines(lines)
    if not total:
        total = _extract_total_fallback(lines)

    # Clean supplier name: strip trailing garbage that bleeds from the table
    if supplier_name:
        # Remove anything after the first tab or 3+ spaces
        supplier_name = re.split(r"\t|\s{3,}", supplier_name)[0].strip()

    return {
        "Supplier Name": supplier_name or "—",
        "Supplier GSTIN": supplier_gstin or "—",
        "Invoice No.": invoice_no or "—",
        "Date": date or "—",
        "Total Amount (₹)": total or "—",
    }


def extract_from_pdf(pdf_path: str | Path) -> list[dict]:
    """
    Extract invoice data from every page of a PDF.
    Each page is treated as one invoice.
    Returns a list of dicts, one per page.
    """
    results = []
    pdf_path = Path(pdf_path)

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text(layout=True) or ""
            if not text.strip():
                continue

            # Only process pages that look like GST invoices
            if not re.search(r"(TAX INVOICE|GSTIN|Invoice\s*No)", text, re.I):
                continue

            data = extract_from_text(text)
            data["Source File"] = pdf_path.name
            data["Page"] = page_num
            results.append(data)

    return results


def extract_from_multiple_pdfs(pdf_paths: list) -> list[dict]:
    """Extract from a list of PDF file paths."""
    all_records = []
    for path in pdf_paths:
        records = extract_from_pdf(path)
        all_records.extend(records)
    return all_records
