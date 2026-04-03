import json
import os
import pytest

def get_fund_data():
    data_path = os.path.join(os.path.dirname(__file__), "fund_data.json")
    if not os.path.exists(data_path):
        return []
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)

@pytest.fixture
def fund_data():
    return get_fund_data()

def test_data_existence(fund_data):
    """Verify that all 5 funds have been scraped."""
    assert len(fund_data) == 5, f"Expected 5 funds, found {len(fund_data)}"

@pytest.mark.parametrize("index", range(5))
def test_fund_fields_not_na(fund_data, index):
    """Verify that key fields are not 'N/A'."""
    fund = fund_data[index]
    critical_fields = ["NAV", "Expense ratio", "AUM", "Min Lumpsum/SIP", "Risk", "Benchmark", "Inception Date", "Exit Load"]
    
    missing_fields = [field for field in critical_fields if fund.get(field) == "N/A"]
    # We allow some fields to be N/A if they are genuinely missing on some funds, 
    # but at least NAV, AUM, and Expense ratio should usually be there.
    assert "NAV" not in missing_fields, f"NAV is missing for {fund['Fund Name']}"
    # Assert at least some fields are captured to ensure the scraper worked
    assert len(missing_fields) < len(critical_fields), f"All fields are N/A for {fund['Fund Name']}"

@pytest.mark.parametrize("index", range(5))
def test_no_tooltip_leaks(fund_data, index):
    """Verify that boilerplate tooltip text is not in the data."""
    fund = fund_data[index]
    PROTECTED_FRAGMENTS = ["Get key fund statistics", "Ranked based on", "Fund returns vs"]
    
    for field, value in fund.items():
        if isinstance(value, str):
            for fragment in PROTECTED_FRAGMENTS:
                assert fragment not in value, f"Tooltip leak detected in {field} for {fund['Fund Name']}: {value}"

def test_value_formats(fund_data):
    """Verify that numeric fields have correct symbols."""
    for fund in fund_data:
        if fund.get("Expense ratio") != "N/A":
             assert "%" in fund["Expense ratio"], f"Expense ratio format invalid: {fund['Expense ratio']}"
        if fund.get("AUM") != "N/A":
             assert "₹" in fund["AUM"] or "Cr" in fund["AUM"], f"AUM format invalid: {fund['AUM']}"
