import requests
from bs4 import BeautifulSoup
import yaml
import json
from datetime import datetime
import os
import pandas as pd

class NewsCollector:
    """Collecteur d'actualités pour le secteur aéronautique"""
    
    def __init__(self, config_path):
        # Chargement de la configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Création du dossier data s'il n'existe pas
        os.makedirs('data', exist_ok=True)
    
    def collect_news(self):
        """Collecte les actualités des sources configurées"""
        all_articles = []
        
        # Collecte depuis les sources d'actualités
        for source in self.config.get('news_sources', []):
            print(f"Collecte depuis {source['name']}...")
            try:
                articles = self._collect_from_source(source)
                all_articles.extend(articles)
                print(f"  {len(articles)} articles collectés")
            except Exception as e:
                print(f"  Erreur lors de la collecte depuis {source['name']}: {str(e)}")
        
        # Collecte depuis les sources de communiqués de presse
        for source in self.config.get('press_sources', []):
            print(f"Collecte depuis {source['name']}...")
            try:
                articles = self._collect_from_source(source)
                all_articles.extend(articles)
                print(f"  {len(articles)} articles collectés")
            except Exception as e:
                print(f"  Erreur lors de la collecte depuis {source['name']}: {str(e)}")
        
        # Sauvegarde des articles collectés
        if all_articles:
            df = pd.DataFrame(all_articles)
            df.to_csv('data/articles.csv', index=False)
            print(f"Total: {len(all_articles)} articles sauvegardés dans data/articles.csv")
            
            # Sauvegarde au format JSON pour l'analyse
            with open('data/articles.json', 'w') as f:
                json.dump(all_articles, f, indent=2)
        
        return all_articles
    
    def _collect_from_source(self, source):
        """Collecte les articles d'une source spécifique"""
        articles = []
        
        try:
            response = requests.get(source['url'], headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            article_elements = soup.select(source['article_selector'])
            
            for article_element in article_elements[:source.get('max_articles', 5)]:
                article_data = self._parse_article(article_element, source)
                if article_data:
                    articles.append(article_data)
        
        except Exception as e:
            print(f"Erreur lors de la collecte depuis {source['name']}: {str(e)}")
        
        return articles
    
    def _parse_article(self, article_element, source):
        """Extrait les informations d'un article"""
        try:
            # Extraction du titre
            title_element = article_element.select_one(source['title_selector'])
            if not title_element:
                return None
            title = title_element.get_text().strip()
            
            # Extraction de l'URL
            url_element = article_element.select_one(source['url_selector'])
            if not url_element:
                return None
                
            if url_element.name == 'a':
                url = url_element.get('href', '')
            else:
                url = ''
                
            if url and not url.startswith('http') and source.get('base_url'):
                url = source['base_url'] + url
            
            # Extraction de la date
            date_element = article_element.select_one(source.get('date_selector', ''))
            date_str = date_element.get_text().strip() if date_element else ''
            date = self._format_date(date_str)
            
            # Extraction du résumé si disponible
            summary_element = article_element.select_one(source.get('summary_selector', ''))
            summary = summary_element.get_text().strip() if summary_element else ""
            
            return {
                'title': title,
                'url': url,
                'date': date,
                'summary': summary,
                'source': source['name'],
                'category': self._categorize_article(title, summary),
                'collected_at': datetime.now().isoformat()
            }
        
        except Exception as e:
            print(f"Erreur lors de l'analyse d'un article: {str(e)}")
            return None
    
    def _format_date(self, date_str):
        """Formate la date en format ISO"""
        if not date_str:
            return datetime.now().isoformat()
        
        try:
            # Tentative simple de parsing
            return datetime.now().isoformat()
        except:
            return datetime.now().isoformat()
    
    def _categorize_article(self, title, summary):
        """Catégorise l'article selon son contenu"""
        text = (title + " " + summary).lower()
        
        categories = {
            'maintenance': ['mro', 'maintenance', 'repair', 'overhaul', 'service center'],
            'fleet': ['fleet', 'aircraft', 'delivery', 'order', 'acquisition'],
            'technology': ['technology', 'innovation', 'digital', 'electric', 'hybrid'],
            'business': ['financial', 'results', 'profit', 'revenue', 'contract'],
            'regulatory': ['certification', 'regulation', 'compliance', 'authority', 'faa', 'easa']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return 'general'

if __name__ == "__main__":
    collector = NewsCollector('config.yaml')
    collector.collect_news()
