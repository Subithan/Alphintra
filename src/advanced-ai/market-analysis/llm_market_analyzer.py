"""
LLM Market Analysis Engine
Alphintra Trading Platform - Phase 5

Advanced market analysis using Large Language Models for news sentiment, 
economic indicator analysis, and real-time market regime detection.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import time
import uuid
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import re
import feedparser
import yfinance as yf

# AI/ML libraries
import openai
import anthropic
import google.generativeai as genai
from transformers import pipeline, AutoTokenizer, AutoModel
import torch
from sentence_transformers import SentenceTransformer
import spacy

# Data sources
import aiohttp
import aioredis
import asyncpg
from alpha_vantage.timeseries import TimeSeries
import quandl

# Monitoring
from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)


class MarketSentiment(Enum):
    """Market sentiment classification"""
    EXTREMELY_BULLISH = "extremely_bullish"
    BULLISH = "bullish"
    MODERATELY_BULLISH = "moderately_bullish"
    NEUTRAL = "neutral"
    MODERATELY_BEARISH = "moderately_bearish"
    BEARISH = "bearish"
    EXTREMELY_BEARISH = "extremely_bearish"


class NewsCategory(Enum):
    """News category classification"""
    EARNINGS = "earnings"
    MACROECONOMIC = "macroeconomic"
    GEOPOLITICAL = "geopolitical"
    REGULATORY = "regulatory"
    COMPANY_SPECIFIC = "company_specific"
    SECTOR_ANALYSIS = "sector_analysis"
    TECHNICAL_ANALYSIS = "technical_analysis"
    MARKET_STRUCTURE = "market_structure"


class EconomicIndicator(Enum):
    """Economic indicator types"""
    GDP = "gdp"
    INFLATION = "inflation"
    UNEMPLOYMENT = "unemployment"
    INTEREST_RATES = "interest_rates"
    CONSUMER_CONFIDENCE = "consumer_confidence"
    PMI = "pmi"
    RETAIL_SALES = "retail_sales"
    HOUSING_DATA = "housing_data"
    TRADE_BALANCE = "trade_balance"
    CURRENCY_STRENGTH = "currency_strength"


@dataclass
class NewsArticle:
    """News article data structure"""
    article_id: str
    title: str
    content: str
    source: str
    author: Optional[str]
    published_at: datetime
    url: str
    category: NewsCategory
    sentiment_score: Optional[float]
    relevance_score: Optional[float]
    mentioned_tickers: List[str]
    key_phrases: List[str]
    language: str


@dataclass
class MarketAnalysis:
    """Comprehensive market analysis result"""
    analysis_id: str
    timestamp: datetime
    overall_sentiment: MarketSentiment
    sentiment_confidence: float
    key_themes: List[str]
    market_drivers: List[str]
    risk_factors: List[str]
    opportunities: List[str]
    sector_outlook: Dict[str, float]
    currency_impact: Dict[str, float]
    volatility_forecast: float
    market_regime_prediction: str
    llm_reasoning: str
    supporting_evidence: List[Dict[str, Any]]


@dataclass
class EconomicAnalysis:
    """Economic indicator analysis"""
    indicator: EconomicIndicator
    current_value: float
    previous_value: float
    market_expectation: float
    surprise_factor: float
    impact_assessment: str
    market_reaction_prediction: str
    historical_context: str
    llm_interpretation: str


class LLMMarketAnalyzer:
    """Advanced market analysis using Large Language Models"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # LLM clients
        self.openai_client = openai.AsyncOpenAI(api_key=config['openai_api_key'])
        self.anthropic_client = anthropic.AsyncAnthropic(api_key=config['anthropic_api_key'])
        genai.configure(api_key=config['google_api_key'])
        
        # Specialized models
        self.sentiment_model = pipeline(
            "sentiment-analysis", 
            model="ProsusAI/finbert",
            device=0 if torch.cuda.is_available() else -1
        )
        
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.nlp = spacy.load("en_core_web_sm")
        
        # Data connections
        self.redis_client = None
        self.db_pool = None
        
        # News sources
        self.news_sources = {
            'reuters': 'http://feeds.reuters.com/reuters/businessNews',
            'bloomberg': 'https://feeds.bloomberg.com/markets/news.rss',
            'cnbc': 'https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664',
            'marketwatch': 'http://feeds.marketwatch.com/marketwatch/marketpulse/',
            'wsj': 'https://feeds.a.dj.com/rss/RSSMarketsMain.xml',
            'ft': 'https://www.ft.com/rss/markets'
        }
        
        # Economic data sources
        self.alpha_vantage = TimeSeries(key=config['alpha_vantage_key'])
        quandl.ApiConfig.api_key = config['quandl_api_key']
        
        # Metrics
        self.analysis_counter = Counter('llm_market_analyses_total', 'Total market analyses performed')
        self.sentiment_gauge = Gauge('market_sentiment_score', 'Current market sentiment score')
        self.analysis_duration = Histogram('llm_analysis_duration_seconds', 'Time spent on market analysis')
        
    async def initialize(self):
        """Initialize connections and resources"""
        self.redis_client = await aioredis.from_url(
            self.config['redis_url'],
            encoding='utf-8',
            decode_responses=True
        )
        
        self.db_pool = await asyncpg.create_pool(
            self.config['database_url'],
            min_size=5,
            max_size=20
        )
        
        logger.info("LLM Market Analyzer initialized successfully")
    
    async def collect_news_data(self) -> List[NewsArticle]:
        """Collect news data from multiple sources"""
        news_articles = []
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            for source, url in self.news_sources.items():
                tasks.append(self._fetch_news_from_source(session, source, url))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    news_articles.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"Error fetching news: {result}")
        
        # Filter and deduplicate
        filtered_articles = await self._filter_and_deduplicate_news(news_articles)
        
        logger.info(f"Collected {len(filtered_articles)} unique news articles")
        return filtered_articles
    
    async def _fetch_news_from_source(self, session: aiohttp.ClientSession, 
                                     source: str, url: str) -> List[NewsArticle]:
        """Fetch news from a specific source"""
        try:
            async with session.get(url, timeout=30) as response:
                content = await response.text()
                
            # Parse RSS feed
            feed = feedparser.parse(content)
            articles = []
            
            for entry in feed.entries[:20]:  # Limit to 20 articles per source
                article = NewsArticle(
                    article_id=str(uuid.uuid4()),
                    title=entry.get('title', ''),
                    content=entry.get('summary', ''),
                    source=source,
                    author=entry.get('author'),
                    published_at=datetime.fromtimestamp(
                        time.mktime(entry.published_parsed)
                    ) if hasattr(entry, 'published_parsed') and entry.published_parsed else datetime.now(),
                    url=entry.get('link', ''),
                    category=NewsCategory.COMPANY_SPECIFIC,  # Will be classified later
                    sentiment_score=None,
                    relevance_score=None,
                    mentioned_tickers=[],
                    key_phrases=[],
                    language='en'
                )
                articles.append(article)
            
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching news from {source}: {e}")
            return []
    
    async def _filter_and_deduplicate_news(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Filter and deduplicate news articles"""
        # Remove duplicates based on title similarity
        unique_articles = []
        seen_titles = set()
        
        for article in articles:
            # Simple deduplication based on first 50 characters of title
            title_key = article.title[:50].lower()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_articles.append(article)
        
        # Filter by relevance (only keep financial market related news)
        relevant_articles = []
        for article in unique_articles:
            if await self._is_market_relevant(article):
                relevant_articles.append(article)
        
        return relevant_articles
    
    async def _is_market_relevant(self, article: NewsArticle) -> bool:
        """Determine if an article is relevant to financial markets"""
        market_keywords = [
            'stock', 'market', 'trading', 'investment', 'earnings', 'revenue',
            'profit', 'loss', 'economic', 'federal reserve', 'interest rate',
            'inflation', 'gdp', 'unemployment', 'nasdaq', 'dow', 's&p',
            'commodity', 'currency', 'forex', 'bond', 'yield'
        ]
        
        text = (article.title + ' ' + article.content).lower()
        return any(keyword in text for keyword in market_keywords)
    
    async def analyze_news_sentiment(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Analyze sentiment of news articles using multiple approaches"""
        for article in articles:
            # Financial sentiment analysis using FinBERT
            finbert_result = self.sentiment_model(article.title + '. ' + article.content[:500])
            
            # Convert FinBERT output to numerical score
            sentiment_map = {'positive': 1.0, 'negative': -1.0, 'neutral': 0.0}
            article.sentiment_score = sentiment_map.get(
                finbert_result[0]['label'].lower(), 0.0
            ) * finbert_result[0]['score']
            
            # Extract key phrases and mentioned tickers
            article.key_phrases = await self._extract_key_phrases(article.content)
            article.mentioned_tickers = await self._extract_tickers(article.content)
            
            # Classify news category
            article.category = await self._classify_news_category(article)
        
        return articles
    
    async def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text using NLP"""
        doc = self.nlp(text)
        
        # Extract noun phrases and named entities
        key_phrases = []
        
        # Noun phrases
        for chunk in doc.noun_chunks:
            if len(chunk.text.split()) <= 4:  # Limit to 4 words
                key_phrases.append(chunk.text.strip())
        
        # Named entities (organizations, people, etc.)
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'PERSON', 'GPE', 'MONEY', 'PERCENT']:
                key_phrases.append(ent.text.strip())
        
        # Remove duplicates and sort by frequency
        return list(set(key_phrases))[:10]  # Top 10 key phrases
    
    async def _extract_tickers(self, text: str) -> List[str]:
        """Extract stock tickers from text"""
        # Simple regex for ticker symbols (1-5 uppercase letters)
        ticker_pattern = r'\b[A-Z]{1,5}\b'
        potential_tickers = re.findall(ticker_pattern, text)
        
        # Filter out common false positives
        false_positives = {'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HAS', 'HER', 'WAS', 'ONE', 'OUR', 'HAD', 'BY', 'WORD', 'BUT', 'WHAT', 'SOME', 'WE', 'CAN', 'OUT', 'OTHER', 'WERE', 'WHICH', 'DO', 'THEIR', 'TIME', 'IF', 'WILL', 'HOW', 'SAID', 'AN', 'EACH', 'ALSO', 'TWO', 'MORE', 'VERY', 'TO', 'OF', 'AND', 'A', 'IN', 'IS', 'IT', 'WITH', 'AS', 'HIS', 'ON', 'BE', 'AT', 'BY', 'THIS', 'HAVE', 'FROM', 'OR', 'ONE', 'HAD', 'WORDS', 'BUT', 'NOT', 'WHAT', 'ALL', 'WERE', 'THEY', 'WE', 'WHEN', 'YOUR', 'CAN', 'SAID', 'THERE', 'EACH', 'WHICH', 'SHE', 'DO', 'HOW', 'THEIR', 'IF', 'WILL', 'UP', 'OTHER', 'ABOUT', 'OUT', 'MANY', 'THEN', 'THEM', 'THESE', 'SO', 'SOME', 'HER', 'WOULD', 'MAKE', 'LIKE', 'INTO', 'HIM', 'HAS', 'TWO', 'MORE', 'GO', 'NO', 'WAY', 'COULD', 'MY', 'THAN', 'FIRST', 'BEEN', 'CALL', 'WHO', 'OIL', 'ITS', 'NOW', 'FIND', 'LONG', 'DOWN', 'DAY', 'DID', 'GET', 'COME', 'MADE', 'MAY', 'PART'}
        
        valid_tickers = [ticker for ticker in potential_tickers if ticker not in false_positives]
        
        return valid_tickers[:5]  # Return top 5 potential tickers
    
    async def _classify_news_category(self, article: NewsArticle) -> NewsCategory:
        """Classify news article into categories"""
        text = (article.title + ' ' + article.content).lower()
        
        category_keywords = {
            NewsCategory.EARNINGS: ['earnings', 'revenue', 'profit', 'quarterly', 'eps'],
            NewsCategory.MACROECONOMIC: ['fed', 'federal reserve', 'gdp', 'inflation', 'unemployment', 'interest rate'],
            NewsCategory.GEOPOLITICAL: ['war', 'conflict', 'election', 'trade war', 'sanctions'],
            NewsCategory.REGULATORY: ['sec', 'regulation', 'compliance', 'fine', 'lawsuit'],
            NewsCategory.SECTOR_ANALYSIS: ['sector', 'industry', 'technology', 'healthcare', 'energy'],
            NewsCategory.TECHNICAL_ANALYSIS: ['support', 'resistance', 'moving average', 'breakout']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return NewsCategory.COMPANY_SPECIFIC
    
    async def generate_comprehensive_market_analysis(self, 
                                                   articles: List[NewsArticle]) -> MarketAnalysis:
        """Generate comprehensive market analysis using LLM"""
        with self.analysis_duration.time():
            # Prepare context for LLM
            news_summary = await self._prepare_news_summary(articles)
            market_data = await self._collect_current_market_data()
            economic_indicators = await self._collect_economic_indicators()
            
            # Generate analysis using multiple LLMs and combine results
            analyses = await asyncio.gather(
                self._analyze_with_gpt4(news_summary, market_data, economic_indicators),
                self._analyze_with_claude(news_summary, market_data, economic_indicators),
                self._analyze_with_gemini(news_summary, market_data, economic_indicators)
            )
            
            # Combine and synthesize results
            final_analysis = await self._synthesize_analyses(analyses, articles)
            
            # Update metrics
            self.analysis_counter.inc()
            self.sentiment_gauge.set(self._sentiment_to_score(final_analysis.overall_sentiment))
            
            # Store analysis
            await self._store_analysis(final_analysis)
            
            return final_analysis
    
    async def _prepare_news_summary(self, articles: List[NewsArticle]) -> str:
        """Prepare a structured summary of news articles for LLM analysis"""
        # Group articles by category and sentiment
        categorized_news = {}
        for article in articles:
            category = article.category.value
            if category not in categorized_news:
                categorized_news[category] = {'positive': [], 'negative': [], 'neutral': []}
            
            sentiment_bucket = 'positive' if article.sentiment_score > 0.1 else 'negative' if article.sentiment_score < -0.1 else 'neutral'
            categorized_news[category][sentiment_bucket].append({
                'title': article.title,
                'sentiment_score': article.sentiment_score,
                'key_phrases': article.key_phrases,
                'tickers': article.mentioned_tickers,
                'source': article.source
            })
        
        # Create structured summary
        summary = "MARKET NEWS ANALYSIS SUMMARY\n"
        summary += f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        summary += f"Total Articles Analyzed: {len(articles)}\n\n"
        
        for category, sentiments in categorized_news.items():
            summary += f"{category.upper().replace('_', ' ')} NEWS:\n"
            for sentiment, articles_list in sentiments.items():
                if articles_list:
                    summary += f"  {sentiment.upper()} ({len(articles_list)} articles):\n"
                    for article in articles_list[:3]:  # Top 3 per sentiment
                        summary += f"    - {article['title'][:100]}...\n"
                        if article['tickers']:
                            summary += f"      Tickers: {', '.join(article['tickers'])}\n"
            summary += "\n"
        
        return summary
    
    async def _collect_current_market_data(self) -> Dict[str, Any]:
        """Collect current market data for context"""
        market_data = {}
        
        try:
            # Major indices
            indices = ['SPY', 'QQQ', 'IWM', 'VIX']
            for symbol in indices:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                hist = ticker.history(period='5d')
                
                market_data[symbol] = {
                    'current_price': info.get('regularMarketPrice', hist['Close'].iloc[-1]),
                    'change_5d': ((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100,
                    'volume': hist['Volume'].iloc[-1],
                    'avg_volume': hist['Volume'].mean()
                }
        
        except Exception as e:
            logger.error(f"Error collecting market data: {e}")
            market_data = {}
        
        return market_data
    
    async def _collect_economic_indicators(self) -> Dict[str, Any]:
        """Collect recent economic indicators"""
        indicators = {}
        
        try:
            # Federal funds rate
            indicators['fed_funds_rate'] = {
                'description': 'Current Federal Funds Rate',
                'value': 'Check latest FOMC decision',
                'trend': 'Analyze recent Fed communications'
            }
            
            # Additional indicators would be collected from various APIs
            # This is a simplified version
            
        except Exception as e:
            logger.error(f"Error collecting economic indicators: {e}")
        
        return indicators
    
    async def _analyze_with_gpt4(self, news_summary: str, market_data: Dict, 
                                economic_indicators: Dict) -> Dict[str, Any]:
        """Analyze using GPT-4"""
        prompt = f"""
        As an expert financial analyst with 20+ years of experience, provide a comprehensive market analysis based on the following data:

        NEWS SUMMARY:
        {news_summary}

        CURRENT MARKET DATA:
        {json.dumps(market_data, indent=2)}

        ECONOMIC INDICATORS:
        {json.dumps(economic_indicators, indent=2)}

        Please provide your analysis in the following JSON format:
        {{
            "overall_sentiment": "extremely_bullish|bullish|moderately_bullish|neutral|moderately_bearish|bearish|extremely_bearish",
            "sentiment_confidence": 0.0-1.0,
            "key_themes": ["theme1", "theme2", ...],
            "market_drivers": ["driver1", "driver2", ...],
            "risk_factors": ["risk1", "risk2", ...],
            "opportunities": ["opportunity1", "opportunity2", ...],
            "sector_outlook": {{"technology": 0.7, "healthcare": 0.3, ...}},
            "volatility_forecast": 0.0-1.0,
            "market_regime_prediction": "bull_market|bear_market|sideways|high_volatility|low_volatility",
            "reasoning": "Detailed explanation of your analysis and conclusions"
        }}

        Focus on actionable insights and be specific about timeframes and confidence levels.
        """

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": "You are a world-class financial analyst known for accurate market predictions and comprehensive analysis."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            # Extract JSON from response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            json_content = content[json_start:json_end]
            
            return json.loads(json_content)
            
        except Exception as e:
            logger.error(f"Error in GPT-4 analysis: {e}")
            return self._get_fallback_analysis()
    
    async def _analyze_with_claude(self, news_summary: str, market_data: Dict, 
                                  economic_indicators: Dict) -> Dict[str, Any]:
        """Analyze using Claude"""
        prompt = f"""
        You are a senior quantitative analyst at a top-tier investment bank. Analyze the current market situation based on this data:

        {news_summary}

        Market Data: {json.dumps(market_data, indent=2)}
        Economic Context: {json.dumps(economic_indicators, indent=2)}

        Provide a JSON response with your market assessment including overall sentiment, key themes, risks, opportunities, and sector outlook. Focus on quantitative insights and probability-weighted scenarios.
        """

        try:
            response = await self.anthropic_client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=2000,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            # Extract JSON from response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_content = content[json_start:json_end]
                return json.loads(json_content)
            else:
                return self._get_fallback_analysis()
                
        except Exception as e:
            logger.error(f"Error in Claude analysis: {e}")
            return self._get_fallback_analysis()
    
    async def _analyze_with_gemini(self, news_summary: str, market_data: Dict, 
                                  economic_indicators: Dict) -> Dict[str, Any]:
        """Analyze using Gemini"""
        try:
            model = genai.GenerativeModel('gemini-pro')
            
            prompt = f"""
            As a market strategist, analyze this comprehensive market data and provide insights:
            
            {news_summary}
            
            Current Market State: {json.dumps(market_data, indent=2)}
            
            Provide your analysis as a structured JSON response focusing on market sentiment, key drivers, and strategic recommendations.
            """
            
            response = await asyncio.to_thread(model.generate_content, prompt)
            content = response.text
            
            # Extract JSON from response
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start != -1 and json_end != -1:
                json_content = content[json_start:json_end]
                return json.loads(json_content)
            else:
                return self._get_fallback_analysis()
                
        except Exception as e:
            logger.error(f"Error in Gemini analysis: {e}")
            return self._get_fallback_analysis()
    
    def _get_fallback_analysis(self) -> Dict[str, Any]:
        """Provide fallback analysis if LLM calls fail"""
        return {
            "overall_sentiment": "neutral",
            "sentiment_confidence": 0.5,
            "key_themes": ["mixed_signals", "uncertainty"],
            "market_drivers": ["earnings_season", "economic_data"],
            "risk_factors": ["volatility", "geopolitical_tensions"],
            "opportunities": ["selective_positioning", "diversification"],
            "sector_outlook": {"technology": 0.5, "healthcare": 0.5, "financials": 0.5},
            "volatility_forecast": 0.6,
            "market_regime_prediction": "sideways",
            "reasoning": "Analysis unavailable due to technical issues. Using conservative baseline assessment."
        }
    
    async def _synthesize_analyses(self, analyses: List[Dict[str, Any]], 
                                  articles: List[NewsArticle]) -> MarketAnalysis:
        """Synthesize multiple LLM analyses into final result"""
        # Combine sentiment scores
        sentiment_scores = []
        for analysis in analyses:
            if 'overall_sentiment' in analysis:
                sentiment_scores.append(self._sentiment_to_score(analysis['overall_sentiment']))
        
        avg_sentiment_score = np.mean(sentiment_scores) if sentiment_scores else 0.0
        overall_sentiment = self._score_to_sentiment(avg_sentiment_score)
        
        # Aggregate confidence
        confidences = [analysis.get('sentiment_confidence', 0.5) for analysis in analyses]
        avg_confidence = np.mean(confidences)
        
        # Combine themes and drivers
        all_themes = []
        all_drivers = []
        all_risks = []
        all_opportunities = []
        
        for analysis in analyses:
            all_themes.extend(analysis.get('key_themes', []))
            all_drivers.extend(analysis.get('market_drivers', []))
            all_risks.extend(analysis.get('risk_factors', []))
            all_opportunities.extend(analysis.get('opportunities', []))
        
        # Remove duplicates and get top items
        key_themes = list(set(all_themes))[:5]
        market_drivers = list(set(all_drivers))[:5]
        risk_factors = list(set(all_risks))[:5]
        opportunities = list(set(all_opportunities))[:5]
        
        # Average sector outlooks
        sector_outlook = {}
        all_sectors = set()
        for analysis in analyses:
            if 'sector_outlook' in analysis:
                all_sectors.update(analysis['sector_outlook'].keys())
        
        for sector in all_sectors:
            scores = [analysis.get('sector_outlook', {}).get(sector, 0.5) for analysis in analyses]
            sector_outlook[sector] = np.mean(scores)
        
        # Average volatility forecast
        volatility_scores = [analysis.get('volatility_forecast', 0.5) for analysis in analyses]
        volatility_forecast = np.mean(volatility_scores)
        
        # Determine market regime
        regimes = [analysis.get('market_regime_prediction', 'sideways') for analysis in analyses]
        market_regime = max(set(regimes), key=regimes.count)  # Most common prediction
        
        # Combine reasoning
        llm_reasoning = "SYNTHESIZED ANALYSIS:\n"
        for i, analysis in enumerate(analyses, 1):
            llm_reasoning += f"LLM {i}: {analysis.get('reasoning', 'No reasoning provided.')}\n\n"
        
        # Create supporting evidence
        supporting_evidence = []
        sentiment_distribution = {}
        for article in articles:
            sentiment_key = self._score_to_sentiment(article.sentiment_score).value
            sentiment_distribution[sentiment_key] = sentiment_distribution.get(sentiment_key, 0) + 1
        
        supporting_evidence.append({
            'type': 'sentiment_distribution',
            'data': sentiment_distribution
        })
        
        supporting_evidence.append({
            'type': 'article_count_by_source',
            'data': {article.source: 1 for article in articles}
        })
        
        return MarketAnalysis(
            analysis_id=str(uuid.uuid4()),
            timestamp=datetime.now(),
            overall_sentiment=overall_sentiment,
            sentiment_confidence=avg_confidence,
            key_themes=key_themes,
            market_drivers=market_drivers,
            risk_factors=risk_factors,
            opportunities=opportunities,
            sector_outlook=sector_outlook,
            currency_impact={},  # Would be populated with FX analysis
            volatility_forecast=volatility_forecast,
            market_regime_prediction=market_regime,
            llm_reasoning=llm_reasoning,
            supporting_evidence=supporting_evidence
        )
    
    def _sentiment_to_score(self, sentiment: Union[str, MarketSentiment]) -> float:
        """Convert sentiment enum to numerical score"""
        if isinstance(sentiment, str):
            sentiment = MarketSentiment(sentiment)
        
        sentiment_map = {
            MarketSentiment.EXTREMELY_BEARISH: -1.0,
            MarketSentiment.BEARISH: -0.7,
            MarketSentiment.MODERATELY_BEARISH: -0.3,
            MarketSentiment.NEUTRAL: 0.0,
            MarketSentiment.MODERATELY_BULLISH: 0.3,
            MarketSentiment.BULLISH: 0.7,
            MarketSentiment.EXTREMELY_BULLISH: 1.0
        }
        
        return sentiment_map.get(sentiment, 0.0)
    
    def _score_to_sentiment(self, score: float) -> MarketSentiment:
        """Convert numerical score to sentiment enum"""
        if score >= 0.8:
            return MarketSentiment.EXTREMELY_BULLISH
        elif score >= 0.5:
            return MarketSentiment.BULLISH
        elif score >= 0.2:
            return MarketSentiment.MODERATELY_BULLISH
        elif score >= -0.2:
            return MarketSentiment.NEUTRAL
        elif score >= -0.5:
            return MarketSentiment.MODERATELY_BEARISH
        elif score >= -0.8:
            return MarketSentiment.BEARISH
        else:
            return MarketSentiment.EXTREMELY_BEARISH
    
    async def _store_analysis(self, analysis: MarketAnalysis):
        """Store analysis results in database"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    INSERT INTO market_analyses 
                    (analysis_id, timestamp, overall_sentiment, sentiment_confidence, 
                     key_themes, market_drivers, risk_factors, opportunities, 
                     sector_outlook, volatility_forecast, market_regime_prediction, 
                     llm_reasoning, supporting_evidence)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
                """, 
                    analysis.analysis_id,
                    analysis.timestamp,
                    analysis.overall_sentiment.value,
                    analysis.sentiment_confidence,
                    json.dumps(analysis.key_themes),
                    json.dumps(analysis.market_drivers),
                    json.dumps(analysis.risk_factors),
                    json.dumps(analysis.opportunities),
                    json.dumps(analysis.sector_outlook),
                    analysis.volatility_forecast,
                    analysis.market_regime_prediction,
                    analysis.llm_reasoning,
                    json.dumps(analysis.supporting_evidence)
                )
                
        except Exception as e:
            logger.error(f"Error storing analysis: {e}")
    
    async def run_continuous_analysis(self, interval_minutes: int = 30):
        """Run continuous market analysis"""
        logger.info(f"Starting continuous market analysis with {interval_minutes}-minute intervals")
        
        while True:
            try:
                # Collect and analyze news
                articles = await self.collect_news_data()
                articles_with_sentiment = await self.analyze_news_sentiment(articles)
                
                # Generate comprehensive analysis
                analysis = await self.generate_comprehensive_market_analysis(articles_with_sentiment)
                
                logger.info(f"Market Analysis Complete - Sentiment: {analysis.overall_sentiment.value}, "
                           f"Confidence: {analysis.sentiment_confidence:.2f}")
                
                # Cache latest analysis
                await self.redis_client.setex(
                    'latest_market_analysis',
                    3600,  # 1 hour TTL
                    json.dumps(asdict(analysis), default=str)
                )
                
            except Exception as e:
                logger.error(f"Error in continuous analysis: {e}")
            
            # Wait for next analysis cycle
            await asyncio.sleep(interval_minutes * 60)
    
    async def get_latest_analysis(self) -> Optional[MarketAnalysis]:
        """Get the latest market analysis"""
        try:
            cached_analysis = await self.redis_client.get('latest_market_analysis')
            if cached_analysis:
                data = json.loads(cached_analysis)
                # Convert back to MarketAnalysis object
                data['overall_sentiment'] = MarketSentiment(data['overall_sentiment'])
                data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                return MarketAnalysis(**data)
        except Exception as e:
            logger.error(f"Error retrieving latest analysis: {e}")
        
        return None
    
    async def cleanup(self):
        """Clean up resources"""
        if self.redis_client:
            await self.redis_client.close()
        if self.db_pool:
            await self.db_pool.close()
        
        logger.info("LLM Market Analyzer cleanup completed")


# Example usage and integration
async def main():
    """Example usage of LLM Market Analyzer"""
    config = {
        'openai_api_key': 'your-openai-key',
        'anthropic_api_key': 'your-anthropic-key',
        'google_api_key': 'your-google-key',
        'alpha_vantage_key': 'your-alpha-vantage-key',
        'quandl_api_key': 'your-quandl-key',
        'redis_url': 'redis://localhost:6379',
        'database_url': 'postgresql://user:pass@localhost/alphintra'
    }
    
    analyzer = LLMMarketAnalyzer(config)
    await analyzer.initialize()
    
    try:
        # Run continuous analysis
        await analyzer.run_continuous_analysis(interval_minutes=30)
    except KeyboardInterrupt:
        logger.info("Shutting down market analyzer...")
    finally:
        await analyzer.cleanup()


if __name__ == "__main__":
    asyncio.run(main())