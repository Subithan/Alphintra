export interface Strategy {
  id: string;
  name: string;
  creatorId: string;
  creatorName: string;
  description: string;
  category: string;
  assetType: string;
  tradingPairs: string[];
  price: number | 'free';
  pricingModel: 'SUBSCRIPTION' | 'REVENUE_SHARE' | 'FREE' | 'ONE_TIME';
  revenueSharePercentage?: number;
  riskLevel: 'low' | 'medium' | 'high';
  verificationStatus: 'PENDING' | 'APPROVED' | 'REJECTED';
  performance: {
    totalReturn: number;
    annualizedReturn: number;
    maxDrawdown: number;
    sharpeRatio: number;
    winRate: number;
  };
  rating: number;
  reviewCount: number;
  subscriberCount: number;
  lastUpdated: string;
  isVerified: boolean;
  thumbnail: string;
  gradientColors: string[];
}