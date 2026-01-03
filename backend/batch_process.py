"""
batch_process.py - Batch Process Companies from Excel
Processes all companies and saves leadership data to Excel
"""
import pandas as pd
from agent_logic_case2 import run_case2_enrichment
import json
import time
from datetime import datetime

print("="*80)
print("🚀 BATCH PROCESSING - Leadership Data Extraction")
print("="*80)

# Input file (change if needed)
INPUT_FILE = '../case1_Manufacturing_industries.xlsx'

# Try to read input file
try:
    print(f"\n📋 Reading companies from: {INPUT_FILE}")
    df = pd.read_excel(INPUT_FILE)
    print(f"✅ Found {len(df)} companies\n")
except FileNotFoundError:
    print(f"❌ File not found: {INPUT_FILE}")
    print("\n💡 Available Excel files in parent directory:")
    import os
    for f in os.listdir('..'):
        if f.endswith('.xlsx'):
            print(f"   - {f}")
    print("\n📝 Update INPUT_FILE variable in this script with correct filename")
    exit(1)
except Exception as e:
    print(f"❌ Error reading file: {e}")
    exit(1)

# Process companies
results = []
successful = 0
failed = 0

start_time = datetime.now()

for idx, row in df.iterrows():
    company = row.get('Name', row.get('name', 'Unknown'))
    website = row.get('Website', row.get('website', row.get('url', '')))
    
    # Skip if no website
    if not website or str(website).strip() == '' or str(website).lower() == 'nan':
        print(f"\n[{idx+1}/{len(df)}] ⏭️  Skipping {company} - No website")
        results.append({
            'Company': company,
            'Website': '',
            'Leadership Found': 'No',
            'Total Leaders': 0,
            'CEO Name': '',
            'CEO Role': '',
            'Leader 1': '',
            'Leader 2': '',
            'Leader 3': '',
            'Leader 4': '',
            'Leader 5': '',
        })
        continue
    
    print(f"\n{'='*80}")
    print(f"[{idx+1}/{len(df)}] Processing: {company}")
    print(f"Website: {website}")
    print(f"{'='*80}")
    
    try:
        # Run scraping with agent
        result = run_case2_enrichment(
            company_name=company,
            website_url=str(website),
            use_agent=True
        )
        
        # Extract data
        leadership_found = result.get('Leadership Found', 'No')
        leaders = result.get('case2_leaders', [])
        management = result.get('case2_management', {})
        
        # Get CEO
        ceo_data = management.get('Executive Leadership', {})
        ceo_name = ceo_data.get('name', '')
        ceo_role = ceo_data.get('designation', '')
        
        # Build result row
        row_data = {
            'Company': company,
            'Website': website,
            'Leadership Found': leadership_found,
            'Total Leaders': len(leaders),
            'CEO Name': ceo_name,
            'CEO Role': ceo_role,
        }
        
        # Add top 5 leaders
        for i in range(5):
            if i < len(leaders):
                leader = leaders[i]
                row_data[f'Leader {i+1}'] = f"{leader.get('name', '')} - {leader.get('role', '')}"
            else:
                row_data[f'Leader {i+1}'] = ''
        
        results.append(row_data)
        
        if leadership_found == 'Yes':
            successful += 1
            print(f"✅ Success! Found {len(leaders)} leaders")
        else:
            failed += 1
            print(f"⚠️ No leaders found")
        
        # Small delay between requests (be nice to servers)
        if idx < len(df) - 1:
            print("⏳ Waiting 5 seconds...")
            time.sleep(5)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        failed += 1
        
        results.append({
            'Company': company,
            'Website': website,
            'Leadership Found': 'Error',
            'Total Leaders': 0,
            'CEO Name': '',
            'CEO Role': '',
            'Leader 1': '',
            'Leader 2': '',
            'Leader 3': '',
            'Leader 4': '',
            'Leader 5': '',
        })

# Save results
print("\n" + "="*80)
print("💾 SAVING RESULTS")
print("="*80)

output_file = f'case2_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'

try:
    output_df = pd.DataFrame(results)
    output_df.to_excel(output_file, index=False)
    print(f"✅ Results saved to: {output_file}")
except Exception as e:
    print(f"❌ Error saving Excel: {e}")
    # Try saving as CSV
    csv_file = output_file.replace('.xlsx', '.csv')
    output_df.to_csv(csv_file, index=False)
    print(f"✅ Saved as CSV instead: {csv_file}")

# Print summary
end_time = datetime.now()
duration = (end_time - start_time).total_seconds()

print("\n" + "="*80)
print("📊 BATCH PROCESSING SUMMARY")
print("="*80)
print(f"Total Companies: {len(df)}")
print(f"Successful: {successful} ({successful/len(df)*100:.1f}%)")
print(f"Failed: {failed} ({failed/len(df)*100:.1f}%)")
print(f"Duration: {duration/60:.1f} minutes")
print(f"Average: {duration/len(df):.1f} seconds per company")
print("\n✅ Processing complete!")
print(f"📁 Open: {output_file}")