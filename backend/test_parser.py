"""Direct test of iXBRL parser with OCR for Revolut"""
import os
import sys
os.environ['PATH'] = r'C:\Program Files (x86)\poppler-24.08.0\Library\bin;' + os.environ.get('PATH', '')

# Add backend to path
sys.path.insert(0, 'F:/test/backend')

from dotenv import load_dotenv
load_dotenv()

# Now import the parser
from data.ixbrl_parser import IXBRLParser

def main():
    api_key = os.getenv('COMPANIES_HOUSE_API_KEY')
    if not api_key:
        print("ERROR: No API key")
        return
    
    print("=" * 60)
    print("Testing IXBRLParser.get_financial_data for Revolut")
    print("=" * 60)
    
    parser = IXBRLParser(api_key)
    
    print("\nCalling get_financial_data('08804411')...")
    print("This may take 30-60 seconds for OCR...")
    
    result = parser.get_financial_data('08804411')
    
    print("\n" + "=" * 60)
    print("RESULT:")
    print("=" * 60)
    
    # Print key fields
    print(f"parse_success: {result.get('parse_success')}")
    print(f"data_available: {result.get('data_available')}")
    print(f"source: {result.get('source')}")
    print(f"turnover: {result.get('turnover')}")
    print(f"total_assets: {result.get('total_assets')}")
    print(f"net_assets: {result.get('net_assets')}")
    print(f"employees: {result.get('employees')}")
    print(f"profit: {result.get('profit')}")
    print(f"eis_checks: {result.get('eis_checks')}")
    
    print("\nNotes:")
    for note in result.get('notes', []):
        print(f"  - {note}")

if __name__ == "__main__":
    main()
