'use client';

import { Suspense, useState, useEffect } from 'react';
import { useSearchParams } from 'next/navigation';

// Disable static generation for this page as it uses searchParams
export const dynamic = 'force-dynamic';
import KnowledgeBaseSearch from '@/components/support/knowledge-base/KnowledgeBaseSearch';
import ArticleViewer from '@/components/support/knowledge-base/ArticleViewer';

interface KnowledgeBaseArticle {
  id: string;
  title: string;
  content: string;
  excerpt: string;
  category: string;
  tags: string[];
  author: string;
  createdAt: string;
  updatedAt: string;
  viewCount: number;
  helpfulVotes: number;
  notHelpfulVotes: number;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  estimatedReadTime: number;
  type: 'Article' | 'Video' | 'Tutorial' | 'FAQ' | 'Troubleshooting';
  isPublished: boolean;
  attachments?: string[];
}

function KnowledgeBaseContent() {
  const searchParams = useSearchParams();
  const [selectedArticle, setSelectedArticle] = useState<KnowledgeBaseArticle | null>(null);
  const [mounted, setMounted] = useState(false);

  const articleId = searchParams?.get('article');
  const searchQuery = searchParams?.get('q') || '';

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (articleId && mounted) {
      // In real implementation, fetch article by ID
      loadArticle(articleId);
    }
  }, [articleId, mounted]);

  const loadArticle = async (id: string) => {
    try {
      // Mock article loading - in real implementation, this would call the API
      const mockArticle: KnowledgeBaseArticle = {
        id,
        title: 'Getting Started with Algorithmic Trading on Alphintra',
        content: `# Getting Started with Algorithmic Trading on Alphintra

Welcome to Alphintra! This comprehensive guide will help you get started with algorithmic trading on our platform.

## What is Algorithmic Trading?

Algorithmic trading involves using computer programs to execute trading strategies automatically based on predefined rules and conditions. This approach offers several advantages:

- **Speed**: Execute trades faster than manual trading
- **Consistency**: Remove emotional decision-making
- **Backtesting**: Test strategies on historical data
- **24/7 Monitoring**: Monitor markets continuously

## Setting Up Your Account

Before you can start trading, you'll need to:

1. **Complete Account Verification**: Ensure your account is fully verified with KYC documents
2. **Connect Your Broker**: Link your brokerage account for live trading
3. **Fund Your Account**: Deposit funds for trading capital
4. **Set Risk Parameters**: Configure your risk management settings

## Creating Your First Strategy

Our visual strategy builder makes it easy to create trading algorithms:

### Step 1: Define Your Market
Choose which markets and instruments you want to trade:
- Stocks (NYSE, NASDAQ)
- Forex pairs
- Cryptocurrencies
- Commodities

### Step 2: Set Entry Conditions
Define when your algorithm should enter trades:
- Technical indicators (RSI, MACD, Moving Averages)
- Price patterns
- Volume conditions
- News sentiment

### Step 3: Configure Exit Rules
Determine when to close positions:
- Take profit levels
- Stop loss settings
- Trailing stops
- Time-based exits

### Step 4: Risk Management
Implement proper risk controls:
- Position sizing
- Maximum drawdown limits
- Daily loss limits
- Correlation limits

## Backtesting Your Strategy

Before going live, thoroughly test your strategy:

1. **Select Historical Data**: Choose appropriate time periods and market conditions
2. **Run Backtests**: Execute your strategy on historical data
3. **Analyze Results**: Review performance metrics and statistics
4. **Optimize Parameters**: Fine-tune your strategy based on results
5. **Validate on Out-of-Sample Data**: Test on unseen data to avoid overfitting

## Paper Trading

Practice with virtual money before risking real capital:

- Test your strategy in real market conditions
- Monitor performance without financial risk
- Gain confidence in your approach
- Identify any technical issues

## Going Live

When you're ready for live trading:

1. **Start Small**: Begin with smaller position sizes
2. **Monitor Closely**: Watch your strategy's performance
3. **Be Prepared to Stop**: Have a plan for stopping the strategy if needed
4. **Keep Learning**: Continuously improve and adapt

## Best Practices

### Risk Management
- Never risk more than you can afford to lose
- Diversify across multiple strategies and markets
- Use appropriate position sizing
- Implement stop losses and take profits

### Strategy Development
- Keep strategies simple and understandable
- Avoid overfitting to historical data
- Consider transaction costs and slippage
- Regular performance review and optimization

### Technical Considerations
- Ensure stable internet connection
- Have backup systems in place
- Monitor for technical failures
- Keep software updated

## Common Pitfalls to Avoid

1. **Over-optimization**: Creating strategies that work perfectly on historical data but fail in live markets
2. **Insufficient Testing**: Not testing thoroughly across different market conditions
3. **Ignoring Transaction Costs**: Forgetting to account for spreads, commissions, and slippage
4. **Emotional Interference**: Manually overriding the algorithm based on emotions
5. **Poor Risk Management**: Not implementing proper position sizing and risk controls

## Getting Help

If you need assistance:

- **Knowledge Base**: Search our comprehensive documentation
- **Video Tutorials**: Watch step-by-step guides
- **Community Forum**: Connect with other traders
- **Support Team**: Contact our expert support agents
- **Strategy Consultation**: Book a session with our trading experts

## Next Steps

Now that you understand the basics:

1. Explore our strategy templates
2. Join our community forum
3. Attend our weekly webinars
4. Start with paper trading
5. Gradually transition to live trading

Remember, successful algorithmic trading requires patience, discipline, and continuous learning. Start small, test thoroughly, and always prioritize risk management.

Good luck with your algorithmic trading journey!`,
        excerpt: 'Learn how to create your first automated trading strategy with our step-by-step guide.',
        category: 'Getting Started',
        tags: ['beginner', 'trading', 'setup', 'tutorial'],
        author: 'Support Team',
        createdAt: '2024-01-15T10:00:00Z',
        updatedAt: '2024-01-20T14:30:00Z',
        viewCount: 1250,
        helpfulVotes: 45,
        notHelpfulVotes: 3,
        difficulty: 'Beginner',
        estimatedReadTime: 8,
        type: 'Tutorial',
        isPublished: true,
        attachments: ['trading-guide.pdf', 'strategy-templates.zip']
      };
      
      setSelectedArticle(mockArticle);
    } catch (error) {
      console.error('Failed to load article:', error);
    }
  };

  const handleArticleSelect = (article: KnowledgeBaseArticle) => {
    setSelectedArticle(article);
    // Update URL without page reload
    const url = new URL(window.location.href);
    url.searchParams.set('article', article.id);
    window.history.pushState({}, '', url.toString());
  };

  const handleBack = () => {
    setSelectedArticle(null);
    // Remove article parameter from URL
    const url = new URL(window.location.href);
    url.searchParams.delete('article');
    window.history.pushState({}, '', url.toString());
  };

  if (!mounted) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {selectedArticle ? (
          <ArticleViewer
            article={selectedArticle}
            onBack={handleBack}
            isAgentView={false}
          />
        ) : (
          <KnowledgeBaseSearch
            onArticleSelect={handleArticleSelect}
            isAgentView={false}
            searchQuery={searchQuery}
          />
        )}
      </div>
    </div>
  );
};

export default function KnowledgeBasePage() {
  return (
    <Suspense
      fallback={
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
        </div>
      }
    >
      <KnowledgeBaseContent />
    </Suspense>
  );
}