"""
NextGen ERP: Specialty Chemical Company Research
Purpose: Find and analyze specialty chemical companies with operational pain signals
Created: May 8, 2026
"""

import pandas as pd
import requests
from datetime import datetime
import json
from typing import List, Dict

class CompanyResearcher:
    """Main research automation class"""
    
    def __init__(self, database_url: str = None):
        """
        Initialize the researcher
        
        Args:
            database_url: PostgreSQL connection string
        """
        self.database_url = database_url
        self.companies_data = []
        self.pain_signals = []
        self.decision_makers = []
        
    def add_company_from_osha(self, company_name: str, location: str, violation: str, 
                              fine_amount: float, violation_date: str) -> Dict:
        """
        Add company found via OSHA violation
        
        Args:
            company_name: Name of company
            location: Company location
            violation: Type of violation (segregation, inventory, storage, etc.)
            fine_amount: Fine amount in EUR
            violation_date: Date of violation
            
        Returns:
            Dictionary with company info and pain signal
        """
        company = {
            'company_name': company_name,
            'location': location,
            'country': self._extract_country(location),
            'source': 'OSHA',
            'created_at': datetime.now().isoformat()
        }
        
        pain_signal = {
            'company_name': company_name,
            'pain_type': 'osha_violation',
            'signal_text': f"OSHA violation: {violation}. Fine: €{fine_amount}",
            'evidence_source': 'OSHA',
            'signal_date': violation_date,
            'urgency_score': self._calculate_urgency_osha(fine_amount, violation),
        }
        
        self.companies_data.append(company)
        self.pain_signals.append(pain_signal)
        
        return {'company': company, 'pain_signal': pain_signal}
    
    def add_company_from_linkedin(self, company_name: str, location: str, 
                                  job_title: str, posting_date: str) -> Dict:
        """
        Add company found via LinkedIn job posting
        
        Args:
            company_name: Name of company
            location: Location
            job_title: Job title posted (e.g., 'Demand Planning Manager')
            posting_date: Date job was posted
            
        Returns:
            Dictionary with company info and pain signal
        """
        company = {
            'company_name': company_name,
            'location': location,
            'country': self._extract_country(location),
            'source': 'LinkedIn',
            'created_at': datetime.now().isoformat()
        }
        
        pain_signal = {
            'company_name': company_name,
            'pain_type': 'hiring_for_optimization',
            'signal_text': f"Hiring for: {job_title}. Indicates operational challenges.",
            'evidence_source': 'LinkedIn',
            'signal_date': posting_date,
            'urgency_score': self._calculate_urgency_linkedin(job_title),
        }
        
        self.companies_data.append(company)
        self.pain_signals.append(pain_signal)
        
        return {'company': company, 'pain_signal': pain_signal}
    
    def add_company_from_earnings(self, company_name: str, location: str, 
                                  mention: str, mention_date: str) -> Dict:
        """
        Add company found in earnings call mention
        
        Args:
            company_name: Name of company
            location: Location
            mention: What was mentioned (inventory costs up, demand issues, etc.)
            mention_date: Date of earnings call
            
        Returns:
            Dictionary with company info and pain signal
        """
        company = {
            'company_name': company_name,
            'location': location,
            'country': self._extract_country(location),
            'source': 'Earnings Call',
            'created_at': datetime.now().isoformat()
        }
        
        pain_signal = {
            'company_name': company_name,
            'pain_type': 'earnings_mention',
            'signal_text': f"Earnings call mention: {mention}",
            'evidence_source': 'Earnings Call',
            'signal_date': mention_date,
            'urgency_score': 6,  # Moderate urgency
        }
        
        self.companies_data.append(company)
        self.pain_signals.append(pain_signal)
        
        return {'company': company, 'pain_signal': pain_signal}
    
    def add_decision_maker(self, company_name: str, first_name: str, last_name: str,
                          title: str, email: str = None, linkedin_url: str = None) -> Dict:
        """
        Add decision maker contact for a company
        
        Args:
            company_name: Company name
            first_name: Contact first name
            last_name: Contact last name
            title: Job title
            email: Email address (optional)
            linkedin_url: LinkedIn profile URL (optional)
            
        Returns:
            Dictionary with decision maker info
        """
        decision_maker = {
            'company_name': company_name,
            'first_name': first_name,
            'last_name': last_name,
            'title': title,
            'email': email,
            'linkedin_url': linkedin_url,
            'contacted': False,
            'created_at': datetime.now().isoformat()
        }
        
        self.decision_makers.append(decision_maker)
        return decision_maker
    
    def get_top_companies(self, limit: int = 10) -> List[Dict]:
        """
        Get companies ranked by urgency
        
        Returns:
            List of companies sorted by urgency (highest first)
        """
        # Create DataFrame and merge data
        companies_df = pd.DataFrame(self.companies_data)
        signals_df = pd.DataFrame(self.pain_signals)
        
        # Group by company and get max urgency score
        if len(signals_df) > 0:
            urgency_by_company = signals_df.groupby('company_name')['urgency_score'].max().reset_index()
            urgency_by_company.columns = ['company_name', 'max_urgency']
            
            # Merge and sort
            ranked = companies_df.merge(urgency_by_company, on='company_name')
            ranked = ranked.sort_values('max_urgency', ascending=False)
            
            return ranked.head(limit).to_dict('records')
        
        return []
    
    def get_research_summary(self) -> Dict:
        """
        Get summary statistics of research
        
        Returns:
            Dictionary with research statistics
        """
        return {
            'total_companies': len(self.companies_data),
            'total_pain_signals': len(self.pain_signals),
            'total_contacts': len(self.decision_makers),
            'pain_types': list(set([p['pain_type'] for p in self.pain_signals])),
            'evidence_sources': list(set([p['evidence_source'] for p in self.pain_signals])),
            'average_urgency': sum([p['urgency_score'] for p in self.pain_signals]) / max(len(self.pain_signals), 1),
            'companies_by_country': self._get_country_distribution()
        }
    
    def export_to_csv(self, filename: str = 'research_results.csv') -> str:
        """
        Export research data to CSV
        
        Args:
            filename: Output CSV filename
            
        Returns:
            Path to exported file
        """
        df = pd.DataFrame(self.companies_data)
        df.to_csv(filename, index=False)
        return filename
    
    def _calculate_urgency_osha(self, fine_amount: float, violation_type: str) -> int:
        """
        Calculate urgency score based on OSHA violation
        
        Args:
            fine_amount: Fine in EUR
            violation_type: Type of violation
            
        Returns:
            Urgency score 1-10
        """
        score = 5
        
        # High-value violations get higher urgency
        if fine_amount > 50000:
            score = 10
        elif fine_amount > 25000:
            score = 9
        elif fine_amount > 10000:
            score = 8
        
        # Segregation violations are critical
        if 'segregation' in violation_type.lower():
            score = min(10, score + 2)
        
        return min(10, score)
    
    def _calculate_urgency_linkedin(self, job_title: str) -> int:
        """
        Calculate urgency based on job title
        
        Args:
            job_title: Job title posted
            
        Returns:
            Urgency score 1-10
        """
        score = 5
        
        critical_titles = [
            'optimization', 'improvement', 'efficiency', 'consolidation',
            'demand planning', 'inventory', 'wms', 'supply chain'
        ]
        
        for title_keyword in critical_titles:
            if title_keyword.lower() in job_title.lower():
                score = 7
                break
        
        return score
    
    def _extract_country(self, location: str) -> str:
        """
        Extract country from location string
        
        Args:
            location: Location string (e.g., "Berlin, Germany")
            
        Returns:
            Country name
        """
        if location:
            parts = location.split(',')
            return parts[-1].strip() if len(parts) > 1 else location
        return 'Unknown'
    
    def _get_country_distribution(self) -> Dict:
        """
        Get distribution of companies by country
        
        Returns:
            Dictionary with country counts
        """
        if self.companies_data:
            df = pd.DataFrame(self.companies_data)
            return df['country'].value_counts().to_dict()
        return {}


# Example usage / Demo
if __name__ == "__main__":
    # Create researcher
    researcher = CompanyResearcher()
    
    # Example: Add a company from OSHA violation
    researcher.add_company_from_osha(
        company_name="ChemCorp Belgium",
        location="Antwerp, Belgium",
        violation="Hazmat segregation violation - incompatible chemicals stored together",
        fine_amount=50000,
        violation_date="2026-04-15"
    )
    
    # Example: Add another company from LinkedIn
    researcher.add_company_from_linkedin(
        company_name="SpecialChem Germany",
        location="Cologne, Germany",
        job_title="Demand Planning Manager - Inventory Optimization",
        posting_date="2026-05-01"
    )
    
    # Example: Add decision maker
    researcher.add_decision_maker(
        company_name="ChemCorp Belgium",
        first_name="Hans",
        last_name="Mueller",
        title="Plant Manager",
        email="hans.mueller@chemcorp.be"
    )
    
    # Get summary
    summary = researcher.get_research_summary()
    print("Research Summary:")
    print(json.dumps(summary, indent=2))
    
    # Get top companies
    top = researcher.get_top_companies(5)
    print("\nTop Companies by Urgency:")
    for company in top:
        print(f"  - {company['company_name']}: Urgency {company['max_urgency']}/10")
