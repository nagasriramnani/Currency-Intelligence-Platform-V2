"""
Alternative: Get financial data from Companies House filing descriptions
For large companies with image PDFs, we can still get some info from filing descriptions and annual reports
"""
import os
import requests
from dotenv import load_dotenv
import re

load_dotenv()

API_KEY = os.getenv('COMPANIES_HOUSE_API_KEY')
COMPANY = "08804411"  # Revolut

CH_API = "https://api.company-information.service.gov.uk"

def main():
    print(f"Getting data for Revolut ({COMPANY}) from CH Profile API...")
    
    # 1. Company profile
    print("\n1. Company Profile...")
    response = requests.get(
        f"{CH_API}/company/{COMPANY}",
        auth=(API_KEY, '')
    )
    profile = response.json()
    print(f"   Company: {profile.get('company_name')}")
    print(f"   Status: {profile.get('company_status')}")
    print(f"   Type: {profile.get('type')}")
    print(f"   Accounts info: {profile.get('accounts', {})}")
    print(f"   Annual return: {profile.get('annual_return', {})}")
    print(f"   Confirmation statement: {profile.get('confirmation_statement', {})}")
    
    # 2. Get filing history with descriptions
    print("\n2. Filing History (looking for financial info in descriptions)...")
    response = requests.get(
        f"{CH_API}/company/{COMPANY}/filing-history",
        auth=(API_KEY, ''),
        params={"items_per_page": 20}
    )
    filings = response.json()
    
    financial_info = []
    for item in filings.get('items', []):
        desc = item.get('description', '')
        desc_values = item.get('description_values', {})
        
        # Look for capital statements or annual returns with data
        if 'capital' in desc.lower() or 'share' in desc.lower():
            print(f"   {item.get('date')}: {desc}")
            print(f"      Values: {desc_values}")
            financial_info.append({
                'date': item.get('date'),
                'type': item.get('type'),
                'description': desc,
                'values': desc_values
            })
    
    # 3. Check annual return/confirmation statement
    print("\n3. Officers...")
    response = requests.get(
        f"{CH_API}/company/{COMPANY}/officers",
        auth=(API_KEY, ''),
        params={"items_per_page": 50}
    )
    officers = response.json()
    active_officers = [o for o in officers.get('items', []) if not o.get('resigned_on')]
    print(f"   Total officers: {len(officers.get('items', []))}")
    print(f"   Active: {len(active_officers)}")
    
    # 4. Get older accounts that might have iXBRL
    print("\n4. Checking older accounts filings for iXBRL...")
    response = requests.get(
        f"{CH_API}/company/{COMPANY}/filing-history",
        auth=(API_KEY, ''),
        params={"category": "accounts", "items_per_page": 10}
    )
    accounts_filings = response.json()
    
    for item in accounts_filings.get('items', []):
        doc_meta = item.get('links', {}).get('document_metadata')
        if doc_meta:
            # Get metadata to check format
            if doc_meta.startswith('http'):
                meta_url = doc_meta
            else:
                meta_url = f"{CH_API}{doc_meta}"
            
            meta_resp = requests.get(meta_url, auth=(API_KEY, ''), headers={'Accept': 'application/json'})
            if meta_resp.status_code == 200:
                meta = meta_resp.json()
                resources = list(meta.get('resources', {}).keys())
                has_xhtml = any('xhtml' in r.lower() or 'html' in r.lower() for r in resources)
                print(f"   {item.get('date')}: {resources} {'✓ Has XHTML!' if has_xhtml else '(PDF only)'}")

if __name__ == "__main__":
    main()
