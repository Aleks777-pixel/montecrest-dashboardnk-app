import streamlit as st
import pandas as pd
import plotly.express as px
import json
import os
from datetime import datetime, timedelta
import yaml

# Configuration de la page
st.set_page_config(
    page_title="MonteCrest Aero Intelligence",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Fonction pour charger les données
def load_data():
    # Vérifier si le fichier existe
    if os.path.exists('data/articles.csv'):
        df = pd.read_csv('data/articles.csv')
        if not df.empty:
            # Convertir les dates
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df['collected_at'] = pd.to_datetime(df['collected_at'], errors='coerce')
            return df
    
    # Retourner un DataFrame vide si pas de données
    return pd.DataFrame(columns=['title', 'url', 'date', 'summary', 'source', 'category', 'collected_at'])

# Fonction pour charger la configuration
def load_config():
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

# Chargement des données
df = load_data()
config = load_config()

# Titre principal
st.title("MonteCrest Aero Intelligence - Tableau de Bord")

# Sidebar pour les filtres
st.sidebar.title("Filtres")

# Filtre de date
default_start_date = datetime.now() - timedelta(days=30)
default_end_date = datetime.now()

if not df.empty and 'date' in df.columns:
    min_date = df['date'].min() if not pd.isna(df['date'].min()) else default_start_date
    max_date = df['date'].max() if not pd.isna(df['date'].max()) else default_end_date
else:
    min_date = default_start_date
    max_date = default_end_date

date_range = st.sidebar.date_input(
    "Période",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Filtre de catégorie
all_categories = ['maintenance', 'fleet', 'technology', 'business', 'regulatory', 'general']
if not df.empty and 'category' in df.columns:
    available_categories = df['category'].unique().tolist()
    all_categories = sorted(list(set(all_categories + available_categories)))

selected_categories = st.sidebar.multiselect(
    "Catégories",
    all_categories,
    default=all_categories[:3] if all_categories else []
)

# Filtre de source
if not df.empty and 'source' in df.columns:
    available_sources = df['source'].unique().tolist()
    selected_sources = st.sidebar.multiselect(
        "Sources",
        available_sources,
        default=available_sources
    )
else:
    selected_sources = []

# Appliquer les filtres
filtered_df = df.copy()

if not df.empty:
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df['date'] >= pd.Timestamp(start_date)) & 
            (filtered_df['date'] <= pd.Timestamp(end_date))
        ]
    
    if selected_categories:
        filtered_df = filtered_df[filtered_df['category'].isin(selected_categories)]
    
    if selected_sources:
        filtered_df = filtered_df[filtered_df['source'].isin(selected_sources)]

# Affichage des statistiques
st.header("Statistiques")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Articles collectés", 
        len(df) if not df.empty else 0,
        delta=None
    )

with col2:
    if not df.empty and 'category' in df.columns:
        category_counts = df['category'].value_counts()
        top_category = category_counts.index[0] if not category_counts.empty else "N/A"
        st.metric(
            "Catégorie principale",
            top_category,
            delta=None
        )
    else:
        st.metric("Catégorie principale", "N/A", delta=None)

with col3:
    if not df.empty and 'source' in df.columns:
        source_counts = df['source'].value_counts()
        top_source = source_counts.index[0] if not source_counts.empty else "N/A"
        st.metric(
            "Source principale",
            top_source,
            delta=None
        )
    else:
        st.metric("Source principale", "N/A", delta=None)

with col4:
    latest_date = df['collected_at'].max() if not df.empty and 'collected_at' in df.columns else None
    if latest_date:
        st.metric(
            "Dernière mise à jour",
            latest_date.strftime("%d/%m/%Y %H:%M") if not pd.isna(latest_date) else "N/A",
            delta=None
        )
    else:
        st.metric("Dernière mise à jour", "N/A", delta=None)

# Graphique de répartition par catégorie
st.header("Répartition par catégorie")

if not filtered_df.empty and 'category' in filtered_df.columns:
    category_counts = filtered_df['category'].value_counts().reset_index()
    category_counts.columns = ['category', 'count']
    
    fig = px.pie(
        category_counts, 
        values='count', 
        names='category',
        title="Répartition des articles par catégorie",
        color_discrete_sequence=px.colors.qualitative.Plotly
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Aucune donnée disponible pour afficher la répartition par catégorie.")

# Graphique d'évolution temporelle
st.header("Évolution temporelle")

if not filtered_df.empty and 'date' in filtered_df.columns and not filtered_df['date'].isna().all():
    # Grouper par date et catégorie
    time_data = filtered_df.groupby([pd.Grouper(key='date', freq='D'), 'category']).size().reset_index(name='count')
    
    fig = px.line(
        time_data,
        x='date',
        y='count',
        color='category',
        title="Évolution du nombre d'articles par catégorie",
        labels={'date': 'Date', 'count': 'Nombre d\'articles', 'category': 'Catégorie'}
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Aucune donnée temporelle disponible pour afficher l'évolution.")

# Liste des derniers articles
st.header("Derniers articles")

if not filtered_df.empty:
    # Trier par date de collecte (du plus récent au plus ancien)
    sorted_df = filtered_df.sort_values(by='collected_at', ascending=False)
    
    for _, row in sorted_df.head(10).iterrows():
        with st.expander(f"{row['title']} ({row['source']})"):
            st.write(f"**Date:** {row['date'].strftime('%d/%m/%Y') if not pd.isna(row['date']) else 'N/A'}")
            st.write(f"**Catégorie:** {row['category']}")
            st.write(f"**Résumé:** {row['summary']}")
            if row['url']:
                st.write(f"[Lien vers l'article]({row['url']})")
else:
    st.info("Aucun article disponible. Veuillez lancer la collecte de données.")

# Section d'aide
with st.sidebar.expander("Aide"):
    st.write("""
    **Comment utiliser ce tableau de bord:**
    
    1. Utilisez les filtres dans la barre latérale pour affiner les données affichées
    2. Explorez les graphiques pour identifier les tendances
    3. Consultez les derniers articles pour obtenir des informations détaillées
    
    Pour collecter de nouvelles données, contactez l'administrateur du système.
    """)

# Affichage des entités configurées
with st.sidebar.expander("Entités configurées"):
    if 'entities' in config:
        for entity_type, entities in config['entities'].items():
            st.write(f"**{entity_type.capitalize()}:**")
            st.write(", ".join(entities[:5]) + ("..." if len(entities) > 5 else ""))

# Pied de page
st.markdown("---")
st.markdown("**MonteCrest Aero Intelligence** - Développé pour MonteCrest Group")
