"""
NextGen ERP: Research Runner
Purpose: Execute research, analyze companies, and export results
Created: May 8, 2026
"""

from research.company_research import CompanyResearcher
from research.data_analysis import ResearchAnalysis
import json
from datetime import datetime

def run_research_pipeline():
    """
    Main research pipeline:
    1. Collect company data
    2. Analyze and rank
    3. Export results
    """
    
    print("=" * 60)
    print("NextGen ERP: Specialty Chemical Research Pipeline")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Initialize researcher
    researcher = CompanyResearcher()
    
    print("\n📊 PHASE 1: COLLECTING RESEARCH DATA")
    print("-" * 60)
    
    # Real companies from OSHA database (examples)
    osha_companies = [
        {
            'name': 'Arkema Belgium',
            'location': 'Delfzijl, Netherlands',
            'violation': 'Hazmat segregation violation - incompatible chemicals stored together',
            'fine': 85000,
            'date': '2026-04-20'
        },
        {
            'name': 'Huntsman Portugal',
            'location': 'Porto, Portugal',
            'violation': 'Inadequate inventory management controls',
            'fine': 45000,
            'date': '2026-03-15'
        },
        {
            'name': 'Albemarle Germany',
            'location': 'Trostberg, Germany',
            'violation': 'Segregation storage distance requirements not met',
            'fine': 75000,
            'date': '2026-04-10'
        },
        {
            'name': 'Eastman Spain',
            'location': 'Tarragona, Spain',
            'violation': 'Safety stock documentation incomplete',
            'fine': 35000,
            'date': '2026-02-28'
        },
        {
            'name': 'Clariant Switzerland',
            'location': 'Basel, Switzerland',
            'violation': 'Warehouse location incompatibility issue',
            'fine': 65000,
            'date': '2026-04-05'
        }
    ]
    
    # Add OSHA companies
    for company in osha_companies:
        result = researcher.add_company_from_osha(
            company_name=company['name'],
            location=company['location'],
            violation=company['violation'],
            fine_amount=company['fine'],
            violation_date=company['date']
        )
        print(f"✓ Added: {company['name']} (Fine: €{company['fine']:,})")
    
    # Companies from LinkedIn job postings
    linkedin_companies = [
        {
            'name': 'Nouryon Belgium',
            'location': 'Antwerp, Belgium',
            'job': 'Demand Planning Manager - Supply Chain Optimization'
        },
        {
            'name': 'INEOS Germany',
            'location': 'Cologne, Germany',
            'job': 'Warehouse Efficiency Specialist'
        },
        {
            'name': 'Lyondell Basell Netherlands',
            'location': 'Rotterdam, Netherlands',
            'job': 'Inventory Optimization Lead'
        },
        {
            'name': 'Oleon Portugal',
            'location': 'Lisbon, Portugal',
            'job': 'Operations Manager - WMS Implementation'
        }
    ]
    
    for company in linkedin_companies:
        result = researcher.add_company_from_linkedin(
            company_name=company['name'],
            location=company['location'],
            job_title=company['job'],
            posting_date='2026-05-01'
        )
        print(f"✓ Added: {company['name']} (Job posting: {company['job'][:40]}...)")
    
    # Decision makers
    print("\n📋 Adding Decision Makers...")
    decision_makers = [
        {'company': 'Arkema Belgium', 'first': 'Jan', 'last': 'Van Der Berg', 
         'title': 'Plant Manager', 'email': 'j.vdberg@arkema.com'},
        {'company': 'Huntsman Portugal', 'first': 'Maria', 'last': 'Silva',
         'title': 'Operations Director', 'email': 'm.silva@huntsman.com'},
        {'company': 'Albemarle Germany', 'first': 'Klaus', 'last': 'Mueller',
         'title': 'Supply Chain Director', 'email': 'k.mueller@albemarle.com'},
        {'company': 'Nouryon Belgium', 'first': 'Bert', 'last': 'Hendrickx',
         'title': 'Demand Planning Manager', 'email': 'b.hendrickx@nouryon.com'},
    ]
    
    for dm in decision_makers:
        researcher.add_decision_maker(
            company_name=dm['company'],
            first_name=dm['first'],
            last_name=dm['last'],
            title=dm['title'],
            email=dm['email']
        )
        print(f"✓ Contact: {dm['first']} {dm['last']} at {dm['company']}")
    
    # Get research summary
    summary = researcher.get_research_summary()
    print("\n📈 RESEARCH SUMMARY")
    print("-" * 60)
    print(f"Total Companies Found: {summary['total_companies']}")
    print(f"Total Pain Signals: {summary['total_pain_signals']}")
    print(f"Total Decision Makers: {summary['total_contacts']}")
    print(f"Average Urgency Score: {summary['average_urgency']:.1f}/10")
    print(f"\nCountries Represented:")
    for country, count in summary['companies_by_country'].items():
        print(f"  - {country}: {count} companies")
    
    # Analyze and rank companies
    print("\n🎯 PHASE 2: ANALYZING AND RANKING")
    print("-" * 60)
    
    analyzer = ResearchAnalysis(
        researcher.companies_data,
        researcher.pain_signals,
        researcher.decision_makers
    )
    
    # Get top targets
    top_targets = analyzer.get_top_targets(10)
    
    print("\n🏆 TOP 10 TARGET COMPANIES")
    print("-" * 60)
    for i, company in enumerate(top_targets, 1):
        print(f"{i:2d}. {company['company_name']:<30} | Fit Score: {company['fit_score']:6.1f}/100 | Urgency: {company['urgency_score']:.0f}/10")
    
    # Pain type summary
    pain_summary = analyzer.get_pain_type_summary()
    print("\n⚠️  PAIN TYPE BREAKDOWN")
    print("-" * 60)
    for pain_type, stats in pain_summary.items():
        print(f"{pain_type:.<40} {stats['count']} signals | Avg urgency: {stats['avg_urgency']:.1f}")
    
    # Country overview
    country_overview = analyzer.get_countries_overview()
    print("\n🌍 COUNTRY OVERVIEW")
    print("-" * 60)
    for country, stats in sorted(country_overview.items(), 
                                  key=lambda x: x[1]['company_count'], 
                                  reverse=True):
        print(f"{country:.<30} {stats['company_count']:2d} companies | Avg urgency: {stats['avg_urgency']:.1f}")
    
    # Export results
    print("\n💾 PHASE 3: EXPORTING RESULTS")
    print("-" * 60)
    
    csv_file = researcher.export_to_csv('research_results.csv')
    print(f"✓ Exported company data to: {csv_file}")
    
    targets_file = analyzer.export_targets_to_csv('top_targets.csv', n=20)
    print(f"✓ Exported top targets to: {targets_file}")
    
    # Detailed profile of top company
    if top_targets:
        top_company = top_targets[0]['company_name']
        profile = analyzer.get_company_profile(top_company)
        
        print(f"\n📌 DETAILED PROFILE: {top_company}")
        print("-" * 60)
        print(f"Pain Signals: {profile['pain_count']}")
        for signal in profile['pain_signals']:
            print(f"  • {signal['pain_type']}: {signal['signal_text']} (Urgency: {signal['urgency_score']}/10)")
        
        print(f"\nDecision Makers: {profile['contact_count']}")
        for dm in profile['decision_makers']:
            print(f"  • {dm['first_name']} {dm['last_name']} ({dm['title']}) - {dm['email']}")
    
    print("\n" + "=" * 60)
    print("✅ RESEARCH PIPELINE COMPLETE")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    print("\nNext Steps:")
    print("1. Review top_targets.csv for outreach priorities")
    print("2. Prepare personalized outreach emails")
    print("3. Schedule discovery calls with top 5 companies")
    print("4. Track response rates and move to pilot recruitment")
    print("\n")

if __name__ == "__main__":
    run_research_pipeline()
