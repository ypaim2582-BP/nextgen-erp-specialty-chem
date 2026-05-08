"""
NextGen ERP: Research Data Analysis
Purpose: Analyze and rank companies for sales targeting
Created: May 8, 2026
"""

import pandas as pd
from typing import List, Dict
import json

class ResearchAnalysis:
    """Analyze research data to identify best targets"""
    
    def __init__(self, companies_data: List[Dict], pain_signals: List[Dict], 
                 decision_makers: List[Dict]):
        """
        Initialize analysis
        
        Args:
            companies_data: List of company dictionaries
            pain_signals: List of pain signal dictionaries
            decision_makers: List of decision maker dictionaries
        """
        self.companies_df = pd.DataFrame(companies_data) if companies_data else pd.DataFrame()
        self.signals_df = pd.DataFrame(pain_signals) if pain_signals else pd.DataFrame()
        self.contacts_df = pd.DataFrame(decision_makers) if decision_makers else pd.DataFrame()
    
    def rank_companies_by_fit(self) -> List[Dict]:
        """
        Rank companies by fit for NextGen ERP solution
        
        Returns:
            List of companies with ranking scores
        """
        if self.companies_df.empty:
            return []
        
        # Start with all companies
        ranked = self.companies_df.copy()
        
        # Add urgency score (from pain signals)
        if not self.signals_df.empty:
            urgency = self.signals_df.groupby('company_name')['urgency_score'].max()
            ranked['urgency_score'] = ranked['company_name'].map(urgency).fillna(5)
        else:
            ranked['urgency_score'] = 5
        
        # Add contact availability
        if not self.contacts_df.empty:
            contact_count = self.contacts_df.groupby('company_name').size()
            ranked['has_contacts'] = ranked['company_name'].isin(contact_count.index)
        else:
            ranked['has_contacts'] = False
        
        # Calculate overall fit score (1-100)
        ranked['fit_score'] = (
            (ranked['urgency_score'] / 10 * 60) +  # 60% weight on urgency
            (ranked['has_contacts'].astype(int) * 40)  # 40% weight on having contacts
        )
        
        # Sort by fit score
        ranked = ranked.sort_values('fit_score', ascending=False)
        
        return ranked.to_dict('records')
    
    def get_top_targets(self, n: int = 10) -> List[Dict]:
        """
        Get top N companies to target for sales
        
        Args:
            n: Number of companies to return
            
        Returns:
            List of top target companies
        """
        ranked = self.rank_companies_by_fit()
        return ranked[:n]
    
    def get_company_profile(self, company_name: str) -> Dict:
        """
        Get detailed profile for one company
        
        Args:
            company_name: Name of company
            
        Returns:
            Dictionary with company details, pain signals, and contacts
        """
        company = self.companies_df[self.companies_df['company_name'] == company_name]
        signals = self.signals_df[self.signals_df['company_name'] == company_name]
        contacts = self.contacts_df[self.contacts_df['company_name'] == company_name]
        
        return {
            'company': company.to_dict('records')[0] if len(company) > 0 else None,
            'pain_signals': signals.to_dict('records') if len(signals) > 0 else [],
            'decision_makers': contacts.to_dict('records') if len(contacts) > 0 else [],
            'pain_count': len(signals),
            'contact_count': len(contacts),
            'max_urgency': signals['urgency_score'].max() if len(signals) > 0 else 0
        }
    
    def get_countries_overview(self) -> Dict:
        """
        Get overview of companies by country
        
        Returns:
            Dictionary with country statistics
        """
        if self.companies_df.empty:
            return {}
        
        country_data = {}
        for country in self.companies_df['country'].unique():
            companies_in_country = self.companies_df[self.companies_df['country'] == country]
            signals_in_country = self.signals_df[
                self.signals_df['company_name'].isin(companies_in_country['company_name'])
            ]
            
            country_data[country] = {
                'company_count': len(companies_in_country),
                'pain_signal_count': len(signals_in_country),
                'avg_urgency': signals_in_country['urgency_score'].mean() if len(signals_in_country) > 0 else 0
            }
        
        return country_data
    
    def get_pain_type_summary(self) -> Dict:
        """
        Summarize pain types across all companies
        
        Returns:
            Dictionary with pain type breakdown
        """
        if self.signals_df.empty:
            return {}
        
        summary = {}
        for pain_type in self.signals_df['pain_type'].unique():
            signals = self.signals_df[self.signals_df['pain_type'] == pain_type]
            summary[pain_type] = {
                'count': len(signals),
                'avg_urgency': signals['urgency_score'].mean(),
                'companies_affected': signals['company_name'].nunique()
            }
        
        return summary
    
    def export_targets_to_csv(self, filename: str = 'top_targets.csv', n: int = 50) -> str:
        """
        Export top target companies to CSV
        
        Args:
            filename: Output CSV filename
            n: Number of companies to export
            
        Returns:
            Path to exported file
        """
        top_companies = self.get_top_targets(n)
        df = pd.DataFrame(top_companies)
        df.to_csv(filename, index=False)
        return filename


# Example usage / Demo
if __name__ == "__main__":
    # Sample data (replace with real data from researcher)
    companies = [
        {'company_name': 'ChemCorp Belgium', 'location': 'Antwerp, Belgium', 'country': 'Belgium'},
        {'company_name': 'SpecialChem Germany', 'location': 'Cologne, Germany', 'country': 'Germany'},
    ]
    
    pain_signals = [
        {'company_name': 'ChemCorp Belgium', 'pain_type': 'segregation_violation', 'urgency_score': 10},
        {'company_name': 'SpecialChem Germany', 'pain_type': 'hiring_for_optimization', 'urgency_score': 7},
    ]
    
    decision_makers = [
        {'company_name': 'ChemCorp Belgium', 'first_name': 'Hans', 'last_name': 'Mueller', 'title': 'Plant Manager'},
    ]
    
    # Create analyzer
    analyzer = ResearchAnalysis(companies, pain_signals, decision_makers)
    
    # Get top targets
    print("Top Target Companies:")
    for target in analyzer.get_top_targets(5):
        print(f"  - {target['company_name']}: Fit Score {target['fit_score']:.1f}/100")
    
    # Get country overview
    print("\nCountry Overview:")
    for country, stats in analyzer.get_countries_overview().items():
        print(f"  {country}: {stats['company_count']} companies, {stats['pain_signal_count']} pain signals")
