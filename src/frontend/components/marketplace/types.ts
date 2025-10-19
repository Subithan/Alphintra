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
  riskLevel: 'low' | 'medium' | 'high';
  verificationStatus: 'PENDING' | 'APPROVED' | 'REJECTED';
  performance: {
    totalReturn: number;
    annualizedReturn: number;
    maxDrawdown: number;
    sharpeRatio: number;
    winRate: number; // This is correctly nested here!
  };
  rating: number;
  reviewCount: number;
  subscriberCount: number;
  lastUpdated: string;
  isVerified: boolean;
  thumbnail: string;
  gradientColors: string[];
}