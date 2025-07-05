import json
import time
from datetime import datetime
from abc import ABC, abstractmethod
from textblob import TextBlob
import logging
from app import db
from app.models import AgentAnalysis, AgentPerformance
from config import Config

logger = logging.getLogger(__name__)

class BaseAIAgent(ABC):
    """Base class for all AI agents"""
    
    def __init__(self, agent_type):
        self.agent_type = agent_type
        self.enabled = Config.ENABLE_AI_AGENTS
        self.retry_count = Config.AI_RETRY_COUNT
        self.timeout = Config.AI_TIMEOUT
    
    @abstractmethod
    def process(self, data):
        """Process data and return results"""
        pass
    
    def _log_analysis(self, input_data, output_data, processing_time, success=True, error_message=None, token_usage=0, cost_estimate=0.0):
        """Log analysis to database"""
        analysis = AgentAnalysis(
            agent_type=self.agent_type,
            input_data=json.dumps(input_data) if isinstance(input_data, dict) else str(input_data),
            output_data=json.dumps(output_data) if isinstance(output_data, dict) else str(output_data),
            processing_time=processing_time,
            token_usage=token_usage,
            cost_estimate=cost_estimate,
            success=success,
            error_message=error_message
        )
        db.session.add(analysis)
        db.session.commit()
        return analysis
    
    def _fallback_process(self, data):
        """Fallback processing when AI APIs are unavailable"""
        if self.agent_type == 'content_quality':
            return self._fallback_quality_scoring(data)
        elif self.agent_type == 'summary':
            return self._fallback_summarization(data)
        elif self.agent_type == 'trend_synthesis':
            return self._fallback_trend_analysis(data)
        elif self.agent_type == 'alert_prioritization':
            return self._fallback_alert_prioritization(data)
        else:
            return {'error': 'No fallback available for this agent type'}
    
    def _fallback_quality_scoring(self, article_data):
        """Basic quality scoring without AI"""
        score = 0.5  # neutral score
        
        # Simple heuristics
        if len(article_data.get('title', '')) > 50:
            score += 0.1
        if len(article_data.get('content', '')) > 500:
            score += 0.2
        if article_data.get('author'):
            score += 0.1
        if article_data.get('published_date'):
            score += 0.1
        
        return {
            'quality_score': min(score, 1.0),
            'method': 'fallback_heuristic',
            'factors': ['title_length', 'content_length', 'has_author', 'has_date']
        }
    
    def _fallback_summarization(self, article_data):
        """Basic summarization without AI"""
        content = article_data.get('content', '')
        if not content:
            return {'summary': article_data.get('title', ''), 'method': 'fallback_title'}
        
        # Simple extractive summarization - first sentence
        sentences = content.split('. ')
        summary = sentences[0] if sentences else content[:200]
        
        return {
            'summary': summary,
            'method': 'fallback_extractive',
            'length': len(summary)
        }
    
    def _fallback_trend_analysis(self, trend_data):
        """Basic trend analysis without AI"""
        return {
            'analysis': f"Trend detected for '{trend_data.get('keyword', 'unknown')}' with search volume {trend_data.get('search_volume', 0)}",
            'method': 'fallback_basic',
            'significance': 'medium'
        }
    
    def _fallback_alert_prioritization(self, alert_data):
        """Basic alert prioritization without AI"""
        # Simple keyword-based prioritization
        high_priority_keywords = ['breaking', 'urgent', 'critical', 'emergency', 'alert']
        content = alert_data.get('message', '').lower()
        
        priority_score = 0.5
        for keyword in high_priority_keywords:
            if keyword in content:
                priority_score += 0.2
        
        return {
            'priority_score': min(priority_score, 1.0),
            'method': 'fallback_keyword',
            'detected_keywords': [kw for kw in high_priority_keywords if kw in content]
        }

class ContentQualityAgent(BaseAIAgent):
    """Agent for scoring content quality"""
    
    def __init__(self):
        super().__init__('content_quality')
    
    def process(self, article_data):
        """Process article for quality scoring"""
        start_time = time.time()
        
        try:
            if not self.enabled:
                result = self._fallback_process(article_data)
                processing_time = time.time() - start_time
                self._log_analysis(article_data, result, processing_time, success=True)
                return result
            
            # TODO: Implement DeepSeek API call for quality scoring
            # For now, use enhanced fallback
            result = self._enhanced_quality_scoring(article_data)
            processing_time = time.time() - start_time
            self._log_analysis(article_data, result, processing_time, success=True)
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            logger.error(f"ContentQualityAgent error: {error_msg}")
            
            # Use fallback on error
            result = self._fallback_process(article_data)
            self._log_analysis(article_data, result, processing_time, success=False, error_message=error_msg)
            return result
    
    def _enhanced_quality_scoring(self, article_data):
        """Enhanced quality scoring with basic NLP"""
        score = 0.3  # base score
        factors = []
        
        title = article_data.get('title', '')
        content = article_data.get('content', '')
        
        # Title quality
        if 20 <= len(title) <= 100:
            score += 0.15
            factors.append('good_title_length')
        
        # Content quality
        if len(content) > 500:
            score += 0.2
            factors.append('sufficient_content')
        
        # Readability (simple metric)
        if content:
            sentences = content.split('. ')
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
            if 10 <= avg_sentence_length <= 25:
                score += 0.1
                factors.append('good_readability')
        
        # Sentiment analysis
        if content:
            try:
                blob = TextBlob(content)
                sentiment = blob.sentiment.polarity
                if abs(sentiment) > 0.1:  # Not neutral
                    score += 0.05
                    factors.append('clear_sentiment')
            except:
                pass
        
        # Metadata completeness
        if article_data.get('author'):
            score += 0.1
            factors.append('has_author')
        
        if article_data.get('published_date'):
            score += 0.1
            factors.append('has_date')
        
        return {
            'quality_score': min(score, 1.0),
            'method': 'enhanced_heuristic',
            'factors': factors,
            'metrics': {
                'title_length': len(title),
                'content_length': len(content),
                'estimated_read_time': len(content) // 200 if content else 0
            }
        }

class SummaryAgent(BaseAIAgent):
    """Agent for generating summaries"""
    
    def __init__(self):
        super().__init__('summary')
    
    def process(self, article_data):
        """Process article for summarization"""
        start_time = time.time()
        
        try:
            if not self.enabled:
                result = self._fallback_process(article_data)
                processing_time = time.time() - start_time
                self._log_analysis(article_data, result, processing_time, success=True)
                return result
            
            # TODO: Implement Claude API call for summarization
            # For now, use enhanced fallback
            result = self._enhanced_summarization(article_data)
            processing_time = time.time() - start_time
            self._log_analysis(article_data, result, processing_time, success=True)
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            logger.error(f"SummaryAgent error: {error_msg}")
            
            result = self._fallback_process(article_data)
            self._log_analysis(article_data, result, processing_time, success=False, error_message=error_msg)
            return result
    
    def _enhanced_summarization(self, article_data):
        """Enhanced summarization with basic NLP"""
        content = article_data.get('content', '')
        title = article_data.get('title', '')
        
        if not content:
            return {'summary': title, 'method': 'title_only'}
        
        # Simple extractive summarization
        sentences = content.split('. ')
        
        if len(sentences) <= 3:
            summary = content
        else:
            # Take first sentence and last sentence
            summary = sentences[0] + '. ' + sentences[-1]
        
        # Limit summary length
        if len(summary) > 300:
            summary = summary[:297] + '...'
        
        return {
            'summary': summary,
            'method': 'enhanced_extractive',
            'original_length': len(content),
            'summary_length': len(summary),
            'compression_ratio': len(summary) / len(content) if content else 0
        }

class TrendSynthesisAgent(BaseAIAgent):
    """Agent for synthesizing trends"""
    
    def __init__(self):
        super().__init__('trend_synthesis')
    
    def process(self, trends_data):
        """Process multiple trends for synthesis"""
        start_time = time.time()
        
        try:
            if not self.enabled:
                result = self._fallback_process(trends_data)
                processing_time = time.time() - start_time
                self._log_analysis(trends_data, result, processing_time, success=True)
                return result
            
            # TODO: Implement Claude API call for trend synthesis
            result = self._enhanced_trend_synthesis(trends_data)
            processing_time = time.time() - start_time
            self._log_analysis(trends_data, result, processing_time, success=True)
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            logger.error(f"TrendSynthesisAgent error: {error_msg}")
            
            result = self._fallback_process(trends_data)
            self._log_analysis(trends_data, result, processing_time, success=False, error_message=error_msg)
            return result
    
    def _enhanced_trend_synthesis(self, trends_data):
        """Enhanced trend synthesis"""
        if not isinstance(trends_data, list):
            trends_data = [trends_data]
        
        # Analyze patterns
        categories = {}
        for trend in trends_data:
            category = trend.get('category', 'unknown')
            if category not in categories:
                categories[category] = []
            categories[category].append(trend)
        
        synthesis = {
            'method': 'enhanced_synthesis',
            'categories_analyzed': list(categories.keys()),
            'total_trends': len(trends_data),
            'insights': []
        }
        
        for category, cat_trends in categories.items():
            if len(cat_trends) > 1:
                synthesis['insights'].append(f"Multiple trends detected in {category} category")
            
            # Find highest volume trend in category
            if cat_trends:
                highest = max(cat_trends, key=lambda x: x.get('search_volume', 0))
                synthesis['insights'].append(f"Top trend in {category}: {highest.get('keyword', 'unknown')}")
        
        return synthesis

class AlertPrioritizationAgent(BaseAIAgent):
    """Agent for prioritizing alerts"""
    
    def __init__(self):
        super().__init__('alert_prioritization')
    
    def process(self, alert_data):
        """Process alert for prioritization"""
        start_time = time.time()
        
        try:
            if not self.enabled:
                result = self._fallback_process(alert_data)
                processing_time = time.time() - start_time
                self._log_analysis(alert_data, result, processing_time, success=True)
                return result
            
            # TODO: Implement Claude API call for alert prioritization
            result = self._enhanced_alert_prioritization(alert_data)
            processing_time = time.time() - start_time
            self._log_analysis(alert_data, result, processing_time, success=True)
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            logger.error(f"AlertPrioritizationAgent error: {error_msg}")
            
            result = self._fallback_process(alert_data)
            self._log_analysis(alert_data, result, processing_time, success=False, error_message=error_msg)
            return result
    
    def _enhanced_alert_prioritization(self, alert_data):
        """Enhanced alert prioritization"""
        message = alert_data.get('message', '').lower()
        title = alert_data.get('title', '').lower()
        alert_type = alert_data.get('alert_type', '')
        
        priority_score = 0.3  # base score
        factors = []
        
        # Critical keywords
        critical_keywords = ['breaking', 'urgent', 'critical', 'emergency', 'alert', 'warning']
        for keyword in critical_keywords:
            if keyword in message or keyword in title:
                priority_score += 0.2
                factors.append(f'critical_keyword_{keyword}')
        
        # Alert type priority
        type_priorities = {
            'breaking_news': 0.8,
            'trend_spike': 0.6,
            'system_error': 0.4
        }
        
        if alert_type in type_priorities:
            priority_score += type_priorities[alert_type]
            factors.append(f'alert_type_{alert_type}')
        
        # Time sensitivity
        now = datetime.utcnow()
        created_at = alert_data.get('created_at', now)
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except:
                created_at = now
        
        time_diff = (now - created_at).total_seconds() / 3600  # hours
        if time_diff < 1:  # Less than 1 hour old
            priority_score += 0.1
            factors.append('time_sensitive')
        
        return {
            'priority_score': min(priority_score, 1.0),
            'method': 'enhanced_prioritization',
            'factors': factors,
            'recommended_priority': 'high' if priority_score > 0.7 else 'medium' if priority_score > 0.4 else 'low'
        }