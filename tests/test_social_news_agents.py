from trading_bot.agents.social_media import SocialMediaAgent
from trading_bot.agents.news_analyzer import NewsAnalyzerAgent


def test_social_media_agent_structure():
    agent = SocialMediaAgent()
    result = agent.analyze("TSLA")
    assert result["agent"] == "SocialMediaAgent"
    assert "score" in result


def test_news_analyzer_agent_structure():
    agent = NewsAnalyzerAgent()
    result = agent.analyze("TSLA")
    assert result["agent"] == "NewsAnalyzerAgent"
    assert "sentiment" in result
