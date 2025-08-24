'use client';

import { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Search, 
  BookOpen, 
  Star, 
  ThumbsUp, 
  ThumbsDown, 
  ExternalLink,
  Filter,
  Clock,
  Tag,
  TrendingUp,
  Eye,
  ChevronRight,
  FileText,
  Video,
  Download
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { toast } from 'react-hot-toast';

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

interface KnowledgeBaseSearchProps {
  onArticleSelect?: (article: KnowledgeBaseArticle) => void;
  isAgentView?: boolean;
  searchQuery?: string;
}

// Mock data - in real implementation, this would come from the API
const mockArticles: KnowledgeBaseArticle[] = [
  {
    id: '1',
    title: 'Getting Started with Algorithmic Trading on Alphintra',
    content: 'Complete guide to setting up your first trading strategy...',
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
    attachments: ['trading-guide.pdf']
  },
  {
    id: '2',
    title: 'Troubleshooting Broker Connection Issues',
    content: 'Common solutions for broker connectivity problems...',
    excerpt: 'Resolve common broker connection problems and optimize your trading setup.',
    category: 'Troubleshooting',
    tags: ['broker', 'connection', 'troubleshooting', 'technical'],
    author: 'Technical Team',
    createdAt: '2024-01-10T09:15:00Z',
    updatedAt: '2024-01-18T16:45:00Z',
    viewCount: 890,
    helpfulVotes: 32,
    notHelpfulVotes: 2,
    difficulty: 'Intermediate',
    estimatedReadTime: 5,
    type: 'Troubleshooting',
    isPublished: true
  },
  {
    id: '3',
    title: 'Advanced Risk Management Strategies',
    content: 'Comprehensive guide to risk management in algorithmic trading...',
    excerpt: 'Master advanced risk management techniques to protect your trading capital.',
    category: 'Risk Management',
    tags: ['risk', 'advanced', 'portfolio', 'management'],
    author: 'Trading Expert',
    createdAt: '2024-01-05T11:30:00Z',
    updatedAt: '2024-01-12T13:20:00Z',
    viewCount: 654,
    helpfulVotes: 28,
    notHelpfulVotes: 1,
    difficulty: 'Advanced',
    estimatedReadTime: 12,
    type: 'Article',
    isPublished: true
  },
  {
    id: '4',
    title: 'How to Backtest Your Trading Strategy',
    content: 'Step-by-step guide to backtesting trading strategies...',
    excerpt: 'Learn how to validate your trading strategies using historical data.',
    category: 'Strategy Development',
    tags: ['backtesting', 'strategy', 'validation', 'data'],
    author: 'Strategy Team',
    createdAt: '2024-01-08T14:20:00Z',
    updatedAt: '2024-01-16T10:15:00Z',
    viewCount: 743,
    helpfulVotes: 35,
    notHelpfulVotes: 4,
    difficulty: 'Intermediate',
    estimatedReadTime: 10,
    type: 'Video',
    isPublished: true
  },
  {
    id: '5',
    title: 'API Integration Best Practices',
    content: 'Best practices for integrating with Alphintra API...',
    excerpt: 'Optimize your API usage with these proven best practices and examples.',
    category: 'API & SDK',
    tags: ['api', 'integration', 'best-practices', 'sdk'],
    author: 'Development Team',
    createdAt: '2024-01-12T16:00:00Z',
    updatedAt: '2024-01-19T09:30:00Z',
    viewCount: 432,
    helpfulVotes: 21,
    notHelpfulVotes: 1,
    difficulty: 'Advanced',
    estimatedReadTime: 7,
    type: 'Article',
    isPublished: true
  }
];

const categories = [
  'All Categories',
  'Getting Started',
  'Troubleshooting',
  'Risk Management',
  'Strategy Development',
  'API & SDK',
  'Account & Billing',
  'Security'
];

const articleTypes = [
  'All Types',
  'Article',
  'Video',
  'Tutorial',
  'FAQ',
  'Troubleshooting'
];

const difficulties = [
  'All Levels',
  'Beginner',
  'Intermediate',
  'Advanced'
];

export default function KnowledgeBaseSearch({ 
  onArticleSelect, 
  isAgentView = false,
  searchQuery: initialQuery = ''
}: KnowledgeBaseSearchProps) {
  const [searchQuery, setSearchQuery] = useState(initialQuery);
  const [selectedCategory, setSelectedCategory] = useState('All Categories');
  const [selectedType, setSelectedType] = useState('All Types');
  const [selectedDifficulty, setSelectedDifficulty] = useState('All Levels');
  const [sortBy, setSortBy] = useState<'relevance' | 'date' | 'popularity' | 'helpful'>('relevance');
  const [showFilters, setShowFilters] = useState(false);

  // Filter and search articles
  const filteredArticles = useMemo(() => {
    let filtered = mockArticles.filter(article => {
      // Category filter
      if (selectedCategory !== 'All Categories' && article.category !== selectedCategory) {
        return false;
      }
      
      // Type filter
      if (selectedType !== 'All Types' && article.type !== selectedType) {
        return false;
      }
      
      // Difficulty filter
      if (selectedDifficulty !== 'All Levels' && article.difficulty !== selectedDifficulty) {
        return false;
      }
      
      // Search query
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        return (
          article.title.toLowerCase().includes(query) ||
          article.excerpt.toLowerCase().includes(query) ||
          article.content.toLowerCase().includes(query) ||
          article.tags.some(tag => tag.toLowerCase().includes(query))
        );
      }
      
      return true;
    });

    // Sort articles
    switch (sortBy) {
      case 'date':
        filtered.sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());
        break;
      case 'popularity':
        filtered.sort((a, b) => b.viewCount - a.viewCount);
        break;
      case 'helpful':
        filtered.sort((a, b) => (b.helpfulVotes - b.notHelpfulVotes) - (a.helpfulVotes - a.notHelpfulVotes));
        break;
      default:
        // Relevance - could implement proper scoring
        break;
    }

    return filtered;
  }, [searchQuery, selectedCategory, selectedType, selectedDifficulty, sortBy]);

  const handleVote = async (articleId: string, isHelpful: boolean) => {
    try {
      // In real implementation, this would call the API
      toast.success(isHelpful ? 'Marked as helpful' : 'Feedback recorded');
    } catch (error) {
      toast.error('Failed to record feedback');
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'Video':
        return <Video className="w-4 h-4" />;
      case 'Tutorial':
        return <BookOpen className="w-4 h-4" />;
      case 'FAQ':
        return <FileText className="w-4 h-4" />;
      default:
        return <FileText className="w-4 h-4" />;
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'Beginner':
        return 'bg-green-100 text-green-800';
      case 'Intermediate':
        return 'bg-yellow-100 text-yellow-800';
      case 'Advanced':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const PopularArticles = () => (
    <div className="space-y-3">
      <h3 className="font-medium text-sm text-gray-700">Popular Articles</h3>
      {mockArticles
        .sort((a, b) => b.viewCount - a.viewCount)
        .slice(0, 5)
        .map(article => (
          <button
            key={article.id}
            onClick={() => onArticleSelect?.(article)}
            className="w-full text-left p-2 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-start gap-2">
              {getTypeIcon(article.type)}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {article.title}
                </p>
                <div className="flex items-center gap-2 text-xs text-gray-500 mt-1">
                  <span className="flex items-center gap-1">
                    <Eye className="w-3 h-3" />
                    {article.viewCount}
                  </span>
                  <span className="flex items-center gap-1">
                    <ThumbsUp className="w-3 h-3" />
                    {article.helpfulVotes}
                  </span>
                </div>
              </div>
            </div>
          </button>
        ))}
    </div>
  );

  const RecentArticles = () => (
    <div className="space-y-3">
      <h3 className="font-medium text-sm text-gray-700">Recently Updated</h3>
      {mockArticles
        .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime())
        .slice(0, 5)
        .map(article => (
          <button
            key={article.id}
            onClick={() => onArticleSelect?.(article)}
            className="w-full text-left p-2 rounded-lg hover:bg-gray-50 transition-colors"
          >
            <div className="flex items-start gap-2">
              {getTypeIcon(article.type)}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-900 truncate">
                  {article.title}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  Updated {formatDistanceToNow(new Date(article.updatedAt), { addSuffix: true })}
                </p>
              </div>
            </div>
          </button>
        ))}
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Search Header */}
      <div className="space-y-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Knowledge Base</h1>
          <p className="text-gray-600">
            Find answers, tutorials, and guides to help you succeed with Alphintra
          </p>
        </div>

        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <Input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search articles, tutorials, and guides..."
            className="pl-10 h-12 text-lg"
          />
        </div>

        {/* Quick Filters */}
        <div className="flex items-center gap-3 flex-wrap">
          <Button
            variant={showFilters ? "default" : "outline"}
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="w-4 h-4 mr-2" />
            Filters
          </Button>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as any)}
            className="px-3 py-1 border rounded-md text-sm"
          >
            <option value="relevance">Sort by Relevance</option>
            <option value="date">Sort by Date</option>
            <option value="popularity">Sort by Popularity</option>
            <option value="helpful">Sort by Helpful</option>
          </select>

          <Badge variant="outline">
            {filteredArticles.length} article{filteredArticles.length !== 1 ? 's' : ''} found
          </Badge>
        </div>

        {/* Advanced Filters */}
        {showFilters && (
          <Card>
            <CardContent className="pt-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-700 mb-2 block">
                    Category
                  </label>
                  <select
                    value={selectedCategory}
                    onChange={(e) => setSelectedCategory(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    {categories.map(category => (
                      <option key={category} value={category}>{category}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-700 mb-2 block">
                    Type
                  </label>
                  <select
                    value={selectedType}
                    onChange={(e) => setSelectedType(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    {articleTypes.map(type => (
                      <option key={type} value={type}>{type}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-700 mb-2 block">
                    Difficulty
                  </label>
                  <select
                    value={selectedDifficulty}
                    onChange={(e) => setSelectedDifficulty(e.target.value)}
                    className="w-full px-3 py-2 border rounded-md"
                  >
                    {difficulties.map(difficulty => (
                      <option key={difficulty} value={difficulty}>{difficulty}</option>
                    ))}
                  </select>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <div className="space-y-6">
          <Card>
            <CardContent className="pt-4">
              <PopularArticles />
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-4">
              <RecentArticles />
            </CardContent>
          </Card>

          {/* Categories */}
          <Card>
            <CardContent className="pt-4">
              <div className="space-y-3">
                <h3 className="font-medium text-sm text-gray-700">Browse by Category</h3>
                {categories.slice(1).map(category => (
                  <button
                    key={category}
                    onClick={() => setSelectedCategory(category)}
                    className={`w-full text-left p-2 rounded-lg transition-colors ${
                      selectedCategory === category 
                        ? 'bg-blue-50 text-blue-700' 
                        : 'hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm">{category}</span>
                      <ChevronRight className="w-3 h-3" />
                    </div>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Content */}
        <div className="lg:col-span-3">
          {filteredArticles.length === 0 ? (
            <Card>
              <CardContent className="pt-8">
                <div className="text-center py-12">
                  <BookOpen className="w-12 h-12 mx-auto text-gray-400 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No articles found</h3>
                  <p className="text-gray-600 mb-4">
                    Try adjusting your search terms or filters
                  </p>
                  <Button 
                    variant="outline"
                    onClick={() => {
                      setSearchQuery('');
                      setSelectedCategory('All Categories');
                      setSelectedType('All Types');
                      setSelectedDifficulty('All Levels');
                    }}
                  >
                    Clear all filters
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {filteredArticles.map(article => (
                <Card key={article.id} className="hover:shadow-md transition-shadow">
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        {getTypeIcon(article.type)}
                        <Badge variant="outline" className="text-xs">
                          {article.type}
                        </Badge>
                        <Badge className={`text-xs ${getDifficultyColor(article.difficulty)}`}>
                          {article.difficulty}
                        </Badge>
                        <span className="text-xs text-gray-500">
                          {article.estimatedReadTime} min read
                        </span>
                      </div>
                      
                      <Badge variant="secondary" className="text-xs">
                        {article.category}
                      </Badge>
                    </div>

                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      <button
                        onClick={() => onArticleSelect?.(article)}
                        className="text-left hover:text-blue-600 transition-colors"
                      >
                        {article.title}
                      </button>
                    </h3>

                    <p className="text-gray-600 mb-3 line-clamp-2">
                      {article.excerpt}
                    </p>

                    {/* Tags */}
                    {article.tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mb-3">
                        {article.tags.slice(0, 4).map(tag => (
                          <Badge key={tag} variant="outline" className="text-xs">
                            <Tag className="w-2 h-2 mr-1" />
                            {tag}
                          </Badge>
                        ))}
                        {article.tags.length > 4 && (
                          <Badge variant="outline" className="text-xs">
                            +{article.tags.length - 4} more
                          </Badge>
                        )}
                      </div>
                    )}

                    {/* Attachments */}
                    {article.attachments && article.attachments.length > 0 && (
                      <div className="flex items-center gap-2 mb-3">
                        <Download className="w-4 h-4 text-gray-400" />
                        <span className="text-sm text-gray-600">
                          {article.attachments.length} attachment{article.attachments.length !== 1 ? 's' : ''}
                        </span>
                      </div>
                    )}

                    {/* Article Stats */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        <span className="flex items-center gap-1">
                          <Eye className="w-3 h-3" />
                          {article.viewCount} views
                        </span>
                        
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {formatDistanceToNow(new Date(article.updatedAt), { addSuffix: true })}
                        </span>
                        
                        <span>By {article.author}</span>
                      </div>

                      <div className="flex items-center gap-2">
                        <div className="flex items-center gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleVote(article.id, true)}
                            className="h-8 px-2"
                          >
                            <ThumbsUp className="w-3 h-3 mr-1" />
                            {article.helpfulVotes}
                          </Button>
                          
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleVote(article.id, false)}
                            className="h-8 px-2"
                          >
                            <ThumbsDown className="w-3 h-3 mr-1" />
                            {article.notHelpfulVotes}
                          </Button>
                        </div>

                        <Button
                          onClick={() => onArticleSelect?.(article)}
                          size="sm"
                        >
                          Read More
                          <ExternalLink className="w-3 h-3 ml-2" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}