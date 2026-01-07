import streamlit as st
import os
import re
from datetime import datetime
from collections import Counter
from io import BytesIO

# PubMed
from Bio import Entrez

# Word Cloud
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# Ollama
from ollama import Client

# ========================================
# Page Config
# ========================================
st.set_page_config(
    page_title="PubMed Research Trend Analyzer",
    page_icon="🔬",
    layout="wide"
)

# Common English stopwords + medical common terms
STOPWORDS = {
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
    'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
    'this', 'that', 'these', 'those', 'it', 'its', 'we', 'our', 'their',
    'them', 'they', 'he', 'she', 'his', 'her', 'i', 'you', 'your', 'my',
    'which', 'who', 'whom', 'what', 'where', 'when', 'why', 'how',
    'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other',
    'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
    'than', 'too', 'very', 'just', 'also', 'now', 'here', 'there',
    # Medical common terms (often too generic)
    'study', 'studies', 'patients', 'patient', 'results', 'conclusion',
    'methods', 'method', 'objective', 'objectives', 'background',
    'data', 'analysis', 'using', 'used', 'use', 'based', 'associated',
    'between', 'among', 'after', 'before', 'during', 'within', 'without',
    'however', 'including', 'included', 'include', 'found', 'showed',
    'significantly', 'significant', 'compared', 'compared', 'increased',
    'decreased', 'higher', 'lower', 'effect', 'effects', 'group', 'groups'
}

def get_secret(key: str, default: str = "") -> str:
    """Get secret from Streamlit secrets or environment."""
    try:
        return st.secrets.get(key, os.getenv(key, default))
    except Exception:
        return os.getenv(key, default)

def search_pubmed(query: str, max_results: int = 100, email: str = "user@example.com"):
    """Search PubMed and return paper details."""
    Entrez.email = email
    
    try:
        # Search
        handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results, sort="relevance")
        record = Entrez.read(handle)
        handle.close()
        
        id_list = record.get("IdList", [])
        if not id_list:
            return []
        
        # Fetch details
        handle = Entrez.efetch(db="pubmed", id=id_list, retmode="xml")
        papers = Entrez.read(handle)
        handle.close()
        
        results = []
        if 'PubmedArticle' in papers:
            for article in papers['PubmedArticle']:
                try:
                    medline = article['MedlineCitation']
                    title = str(medline['Article']['ArticleTitle'])
                    
                    abstract = ""
                    if 'Abstract' in medline['Article']:
                        ab = medline['Article']['Abstract']['AbstractText']
                        if isinstance(ab, list):
                            abstract = " ".join([str(a) for a in ab])
                        else:
                            abstract = str(ab)
                    
                    results.append({
                        "title": title,
                        "abstract": abstract,
                        "pmid": str(medline['PMID'])
                    })
                except Exception:
                    continue
        
        return results
    except Exception as e:
        st.error(f"PubMed search failed: {e}")
        return []

def extract_keywords(papers: list) -> Counter:
    """Extract and count keywords from titles and abstracts."""
    all_text = ""
    for paper in papers:
        all_text += " " + paper['title'] + " " + paper['abstract']
    
    # Clean and tokenize
    words = re.findall(r'\b[a-zA-Z]{3,}\b', all_text.lower())
    
    # Remove stopwords
    filtered_words = [w for w in words if w not in STOPWORDS]
    
    return Counter(filtered_words)

def extract_bigrams(papers: list) -> Counter:
    """Extract bigrams (2-word phrases) from text."""
    all_text = ""
    for paper in papers:
        all_text += " " + paper['title'] + " " + paper['abstract']
    
    # Clean and tokenize
    words = re.findall(r'\b[a-zA-Z]{3,}\b', all_text.lower())
    filtered_words = [w for w in words if w not in STOPWORDS]
    
    # Create bigrams
    bigrams = [f"{filtered_words[i]} {filtered_words[i+1]}" 
               for i in range(len(filtered_words)-1)]
    
    return Counter(bigrams)

def generate_wordcloud(word_counts: Counter, title: str = "Word Cloud"):
    """Generate word cloud image."""
    if not word_counts:
        return None
    
    wc = WordCloud(
        width=800,
        height=400,
        background_color='white',
        colormap='viridis',
        max_words=100,
        min_font_size=10
    ).generate_from_frequencies(dict(word_counts.most_common(100)))
    
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.imshow(wc, interpolation='bilinear')
    ax.axis('off')
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    return fig

def analyze_with_ollama(papers: list, keyword: str, word_counts: Counter, 
                        ollama_client, model: str) -> str:
    """Use Ollama to analyze research trends."""
    
    top_terms = ", ".join([f"{word}({count})" for word, count in word_counts.most_common(20)])
    
    sample_titles = "\n".join([f"- {p['title']}" for p in papers[:10]])
    
    prompt = f"""
You are a research analyst. Analyze the following PubMed search results for "{keyword}".

**Top 20 Most Frequent Terms:**
{top_terms}

**Sample Paper Titles (10 of {len(papers)}):**
{sample_titles}

Based on this data, provide:

1. **Main Research Areas** (3-5 key areas where most research is concentrated)
2. **Emerging Topics** (any newer or trending subtopics you notice)
3. **Research Gaps** (areas that seem underrepresented)
4. **Summary** (2-3 sentences overview of the research landscape)

Be specific and use the actual terms from the data.
"""
    
    try:
        response = ollama_client.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            stream=False
        )
        return response['message']['content']
    except Exception as e:
        return f"⚠️ AI Analysis failed: {str(e)}"

def main():
    st.title("🔬 PubMed Research Trend Analyzer")
    st.markdown("Analyze research trends by keyword using PubMed and AI")

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # NCBI Email (required)
        email = get_secret("ENTREZ_EMAIL", "")
        if not email:
            email = st.text_input("Your Email (for NCBI)", placeholder="required@example.com")
        else:
            st.success("✅ NCBI Email configured")
        
        st.divider()
        
        # Ollama settings
        ollama_api_key = get_secret("OLLAMA_API_KEY", "")
        model = get_secret("OLLAMA_MODEL", "llama3")
        
        if ollama_api_key:
            st.success("✅ Ollama API Key configured")
        else:
            st.warning("⚠️ Ollama API Key missing")
            st.caption("AI analysis will be disabled")
        
        model = st.text_input("Ollama Model", value=model)
        
        st.divider()
        
        # Search settings
        max_results = st.slider("Max Papers", 50, 500, 200, step=50)
        
        st.divider()
        st.caption("📚 **About**")
        st.caption("This app searches PubMed, extracts keywords, generates word clouds, and uses AI to analyze research trends.")

    # Main content
    keyword = st.text_input("🔍 Enter Research Keyword", placeholder="e.g., GLP-1 agonist cardiovascular")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        analyze_btn = st.button("🚀 Analyze", type="primary", use_container_width=True)
    
    if analyze_btn:
        if not keyword:
            st.error("Please enter a search keyword")
            st.stop()
        
        if not email:
            st.error("Please enter your email for NCBI PubMed access")
            st.stop()
        
        # Search PubMed
        with st.status("Analyzing research trends...", expanded=True) as status:
            status.write(f"🔍 Searching PubMed for '{keyword}'...")
            papers = search_pubmed(keyword, max_results, email)
            
            if not papers:
                status.update(label="No results found", state="error")
                st.error("No papers found. Try a different keyword.")
                st.stop()
            
            status.write(f"✅ Found {len(papers)} papers")
            
            # Extract keywords
            status.write("📊 Extracting keywords...")
            word_counts = extract_keywords(papers)
            bigram_counts = extract_bigrams(papers)
            
            status.update(label="Analysis complete!", state="complete", expanded=False)
        
        # Display results
        st.success(f"📊 Analyzed {len(papers)} papers for '{keyword}'")
        
        # Tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["☁️ Word Cloud", "📊 Top Terms", "🤖 AI Analysis", "📋 Papers"])
        
        with tab1:
            st.subheader("Word Cloud - Single Words")
            fig1 = generate_wordcloud(word_counts, f"Research Terms: {keyword}")
            if fig1:
                st.pyplot(fig1)
                
                # Download word cloud
                buf = BytesIO()
                fig1.savefig(buf, format='png', dpi=150, bbox_inches='tight')
                buf.seek(0)
                st.download_button(
                    "📥 Download Word Cloud",
                    data=buf,
                    file_name=f"wordcloud_{keyword.replace(' ', '_')}.png",
                    mime="image/png"
                )
            
            st.divider()
            
            st.subheader("Word Cloud - Bigrams (2-word phrases)")
            fig2 = generate_wordcloud(bigram_counts, f"Research Phrases: {keyword}")
            if fig2:
                st.pyplot(fig2)
        
        with tab2:
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.subheader("🔤 Top 30 Single Words")
                for i, (word, count) in enumerate(word_counts.most_common(30), 1):
                    st.text(f"{i:2}. {word}: {count}")
            
            with col_b:
                st.subheader("🔤 Top 30 Bigrams")
                for i, (bigram, count) in enumerate(bigram_counts.most_common(30), 1):
                    st.text(f"{i:2}. {bigram}: {count}")
        
        with tab3:
            if ollama_api_key:
                st.subheader("🤖 AI-Powered Trend Analysis")
                
                with st.spinner("Generating AI analysis..."):
                    try:
                        ollama_client = Client(
                            host='https://ollama.com',
                            headers={'Authorization': f'Bearer {ollama_api_key}'}
                        )
                        
                        analysis = analyze_with_ollama(
                            papers, keyword, word_counts, 
                            ollama_client, model
                        )
                        
                        st.markdown(analysis)
                        
                        # Download analysis
                        st.download_button(
                            "📥 Download Analysis",
                            data=analysis,
                            file_name=f"analysis_{keyword.replace(' ', '_')}.md",
                            mime="text/markdown"
                        )
                    except Exception as e:
                        st.error(f"AI Analysis failed: {e}")
            else:
                st.warning("⚠️ Ollama API Key not configured. Add `OLLAMA_API_KEY` to Streamlit Secrets for AI analysis.")
        
        with tab4:
            st.subheader(f"📋 Paper List ({len(papers)} papers)")
            
            for i, paper in enumerate(papers[:50], 1):  # Show first 50
                with st.expander(f"{i}. {paper['title'][:80]}...", expanded=False):
                    st.markdown(f"**Title:** {paper['title']}")
                    st.markdown(f"**PMID:** [{paper['pmid']}](https://pubmed.ncbi.nlm.nih.gov/{paper['pmid']}/)")
                    if paper['abstract']:
                        st.markdown(f"**Abstract:** {paper['abstract'][:500]}...")
            
            if len(papers) > 50:
                st.info(f"Showing first 50 of {len(papers)} papers")
        
        # Store in session
        st.session_state['last_keyword'] = keyword
        st.session_state['last_papers'] = papers
        st.session_state['last_word_counts'] = word_counts

if __name__ == "__main__":
    main()
