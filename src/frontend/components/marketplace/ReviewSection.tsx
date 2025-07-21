'use client';

import React, { useState } from 'react';
import { Star, ThumbsUp, ThumbsDown, Flag, MessageSquare, Filter, ChevronDown } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useTheme } from 'next-themes';

interface Review {
  id: string;
  user: string;
  rating: number;
  date: string;
  title: string;
  content: string;
  helpful: number;
  unhelpful: number;
  verified: boolean;
  tradingExperience: string;
  pros: string[];
  cons: string[];
}

interface ReviewSectionProps {
  strategyId: string;
  rating: number;
  reviewCount: number;
}

// Mock reviews data
const mockReviews: Review[] = [
  {
    id: '1',
    user: 'TradingPro2024',
    rating: 5,
    date: '2024-01-10',
    title: 'Outstanding performance in volatile markets',
    content: 'I\'ve been using this strategy for 6 months now and it has consistently outperformed my other strategies. The risk management is excellent and the drawdowns are manageable. Highly recommended for intermediate to advanced traders.',
    helpful: 23,
    unhelpful: 2,
    verified: true,
    tradingExperience: 'Advanced',
    pros: ['Excellent risk management', 'Consistent returns', 'Great documentation'],
    cons: ['Requires significant capital', 'Complex setup process']
  },
  {
    id: '2',
    user: 'CryptoWhale88',
    rating: 4,
    date: '2024-01-08',
    title: 'Good strategy but needs some tweaking',
    content: 'The strategy works well overall but I had to adjust some parameters for my portfolio size. The developer was helpful in providing guidance. Performance has been solid since implementation.',
    helpful: 18,
    unhelpful: 4,
    verified: true,
    tradingExperience: 'Intermediate',
    pros: ['Good performance', 'Responsive developer', 'Flexible parameters'],
    cons: ['Setup complexity', 'Documentation could be clearer']
  },
  {
    id: '3',
    user: 'AlgoTrader123',
    rating: 5,
    date: '2024-01-05',
    title: 'Best momentum strategy I\'ve used',
    content: 'After trying dozens of strategies, this one stands out. The quantum-inspired algorithms really make a difference in signal quality. My Sharpe ratio improved significantly.',
    helpful: 31,
    unhelpful: 1,
    verified: true,
    tradingExperience: 'Expert',
    pros: ['Superior signal quality', 'Low correlation with market', 'Excellent Sharpe ratio'],
    cons: ['Premium pricing']
  },
  {
    id: '4',
    user: 'NewbieTrader',
    rating: 3,
    date: '2024-01-03',
    title: 'Works but steep learning curve',
    content: 'The strategy performs as advertised but it took me weeks to understand all the parameters. Not suitable for beginners despite what I thought initially.',
    helpful: 12,
    unhelpful: 8,
    verified: false,
    tradingExperience: 'Beginner',
    pros: ['Good performance once configured'],
    cons: ['Complex for beginners', 'Steep learning curve', 'Expensive']
  }
];

const ratingDistribution = [
  { stars: 5, count: 162, percentage: 65.6 },
  { stars: 4, count: 58, percentage: 23.5 },
  { stars: 3, count: 18, percentage: 7.3 },
  { stars: 2, count: 6, percentage: 2.4 },
  { stars: 1, count: 3, percentage: 1.2 }
];

const ReviewSection: React.FC<ReviewSectionProps> = ({ strategyId, rating, reviewCount }) => {
  const { theme } = useTheme();
  const [sortBy, setSortBy] = useState('helpful');
  const [filterBy, setFilterBy] = useState('all');
  const [showWriteReview, setShowWriteReview] = useState(false);

  const renderStars = (rating: number, size: 'sm' | 'md' | 'lg' = 'md') => {
    const sizeClass = size === 'sm' ? 'h-3 w-3' : size === 'lg' ? 'h-5 w-5' : 'h-4 w-4';
    return (
      <div className="flex gap-0.5">
        {[1, 2, 3, 4, 5].map((star) => (
          <Star
            key={star}
            className={`${sizeClass} ${
              star <= rating 
                ? 'text-yellow-500 fill-current' 
                : theme === 'dark' ? 'text-gray-600' : 'text-gray-300'
            }`}
          />
        ))}
      </div>
    );
  };

  const filteredReviews = mockReviews.filter(review => {
    if (filterBy === 'all') return true;
    if (filterBy === 'verified') return review.verified;
    if (filterBy === 'rating-5') return review.rating === 5;
    if (filterBy === 'rating-4') return review.rating === 4;
    if (filterBy === 'rating-3') return review.rating <= 3;
    return true;
  }).sort((a, b) => {
    if (sortBy === 'helpful') return b.helpful - a.helpful;
    if (sortBy === 'recent') return new Date(b.date).getTime() - new Date(a.date).getTime();
    if (sortBy === 'rating') return b.rating - a.rating;
    return 0;
  });

  return (
    <div className="space-y-6">
      {/* Rating Overview */}
      <Card className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Customer Reviews</span>
            <Button 
              onClick={() => setShowWriteReview(true)}
              className="bg-gradient-to-r from-yellow-400 to-amber-500 hover:from-yellow-500 hover:to-amber-600 text-black font-semibold"
              size="sm"
            >
              Write Review
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Overall Rating */}
            <div className="text-center">
              <div className={`text-4xl font-bold mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                {rating.toFixed(1)}
              </div>
              <div className="mb-2">
                {renderStars(rating, 'lg')}
              </div>
              <p className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                Based on {reviewCount.toLocaleString()} reviews
              </p>
            </div>

            {/* Rating Distribution */}
            <div className="space-y-2">
              {ratingDistribution.map((dist) => (
                <div key={dist.stars} className="flex items-center gap-3">
                  <div className="flex items-center gap-1 w-12">
                    <span className={`text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                      {dist.stars}
                    </span>
                    <Star className="h-3 w-3 text-yellow-500 fill-current" />
                  </div>
                  <div className="flex-1">
                    <Progress 
                      value={dist.percentage} 
                      className="h-2"
                    />
                  </div>
                  <span className={`text-sm w-12 text-right ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                    {dist.count}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Filter and Sort Controls */}
      <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
        <div className="flex gap-3">
          <Select value={sortBy} onValueChange={setSortBy}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="helpful">Most Helpful</SelectItem>
              <SelectItem value="recent">Most Recent</SelectItem>
              <SelectItem value="rating">Highest Rating</SelectItem>
            </SelectContent>
          </Select>

          <Select value={filterBy} onValueChange={setFilterBy}>
            <SelectTrigger className="w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Reviews</SelectItem>
              <SelectItem value="verified">Verified Only</SelectItem>
              <SelectItem value="rating-5">5 Stars</SelectItem>
              <SelectItem value="rating-4">4 Stars</SelectItem>
              <SelectItem value="rating-3">3 Stars & Below</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <span className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
          Showing {filteredReviews.length} of {mockReviews.length} reviews
        </span>
      </div>

      {/* Reviews List */}
      <div className="space-y-4">
        {filteredReviews.map((review) => (
          <Card key={review.id} className={`${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'}`}>
            <CardContent className="p-6">
              {/* Review Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-sm">
                    {review.user.substring(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`font-semibold ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                        {review.user}
                      </span>
                      {review.verified && (
                        <Badge variant="outline" className="text-xs">
                          ✓ Verified
                        </Badge>
                      )}
                      <Badge variant="secondary" className="text-xs">
                        {review.tradingExperience}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      {renderStars(review.rating, 'sm')}
                      <span className={`text-xs ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                        {new Date(review.date).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>
                <Button variant="ghost" size="sm">
                  <Flag className="h-4 w-4" />
                </Button>
              </div>

              {/* Review Content */}
              <div className="mb-4">
                <h4 className={`font-semibold mb-2 ${theme === 'dark' ? 'text-white' : 'text-gray-900'}`}>
                  {review.title}
                </h4>
                <p className={`${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'} leading-relaxed`}>
                  {review.content}
                </p>
              </div>

              {/* Pros and Cons */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                {review.pros.length > 0 && (
                  <div>
                    <h5 className={`text-sm font-semibold mb-2 text-green-600 dark:text-green-400`}>
                      Pros:
                    </h5>
                    <ul className="space-y-1">
                      {review.pros.map((pro, index) => (
                        <li key={index} className={`text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                          • {pro}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {review.cons.length > 0 && (
                  <div>
                    <h5 className={`text-sm font-semibold mb-2 text-red-600 dark:text-red-400`}>
                      Cons:
                    </h5>
                    <ul className="space-y-1">
                      {review.cons.map((con, index) => (
                        <li key={index} className={`text-sm ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                          • {con}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Review Actions */}
              <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
                <div className="flex items-center gap-4">
                  <span className={`text-sm ${theme === 'dark' ? 'text-gray-400' : 'text-gray-600'}`}>
                    Was this helpful?
                  </span>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" className="flex items-center gap-1">
                      <ThumbsUp className="h-3 w-3" />
                      {review.helpful}
                    </Button>
                    <Button variant="outline" size="sm" className="flex items-center gap-1">
                      <ThumbsDown className="h-3 w-3" />
                      {review.unhelpful}
                    </Button>
                  </div>
                </div>
                <Button variant="ghost" size="sm" className="flex items-center gap-1">
                  <MessageSquare className="h-4 w-4" />
                  Reply
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Load More Button */}
      <div className="text-center">
        <Button variant="outline" className="flex items-center gap-2">
          Load More Reviews
          <ChevronDown className="h-4 w-4" />
        </Button>
      </div>

      {/* Write Review Modal would go here */}
      {showWriteReview && (
        <Card className={`fixed inset-4 md:inset-auto md:top-1/2 md:left-1/2 md:-translate-x-1/2 md:-translate-y-1/2 md:w-full md:max-w-2xl z-50 ${theme === 'dark' ? 'bg-gray-800 border-gray-700' : 'bg-white border-gray-200'} shadow-2xl`}>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>Write a Review</CardTitle>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setShowWriteReview(false)}
              >
                ×
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className={`block text-sm font-medium mb-2 ${theme === 'dark' ? 'text-gray-300' : 'text-gray-700'}`}>
                  Your Rating
                </label>
                <div className="flex gap-1">
                  {[1, 2, 3, 4, 5].map((star) => (
                    <button key={star} className="p-1">
                      <Star className="h-6 w-6 text-gray-300 hover:text-yellow-500 transition-colors" />
                    </button>
                  ))}
                </div>
              </div>
              {/* Additional form fields would go here */}
              <div className="flex justify-end gap-2 pt-4">
                <Button variant="outline" onClick={() => setShowWriteReview(false)}>
                  Cancel
                </Button>
                <Button className="bg-gradient-to-r from-yellow-400 to-amber-500 hover:from-yellow-500 hover:to-amber-600 text-black font-semibold">
                  Submit Review
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default ReviewSection;