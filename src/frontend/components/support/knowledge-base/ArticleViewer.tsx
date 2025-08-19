'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { 
  ArrowLeft, 
  BookOpen, 
  Clock, 
  Eye, 
  ThumbsUp, 
  ThumbsDown, 
  Share2, 
  Bookmark, 
  Download,
  Edit,
  MoreVertical,
  Star,
  User,
  Calendar,
  Tag,
  FileText,
  Video,
  ExternalLink,
  Copy,
  Check
} from 'lucide-react';
import { formatDistanceToNow, format } from 'date-fns';
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
  videoUrl?: string;
  relatedArticles?: string[];
}

interface ArticleViewerProps {
  article: KnowledgeBaseArticle;
  onBack: () => void;
  onEdit?: () => void;
  isAgentView?: boolean;
  className?: string;
}

// Mock related articles
const mockRelatedArticles = [
  {
    id: '101',
    title: 'Advanced Strategy Optimization Techniques',
    excerpt: 'Learn how to fine-tune your trading strategies for maximum performance.',
    type: 'Article',
    estimatedReadTime: 6
  },
  {
    id: '102',
    title: 'Common Trading Pitfalls to Avoid',
    excerpt: 'Discover the most common mistakes traders make and how to avoid them.',
    type: 'Tutorial',
    estimatedReadTime: 4
  },
  {
    id: '103',
    title: 'Setting Up Risk Parameters',
    excerpt: 'Configure proper risk management settings for your trading account.',
    type: 'Video',
    estimatedReadTime: 8
  }
];

export default function ArticleViewer({ 
  article, 
  onBack, 
  onEdit, 
  isAgentView = false,
  className = ''
}: ArticleViewerProps) {
  const [hasVoted, setHasVoted] = useState<'helpful' | 'not-helpful' | null>(null);
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [showTableOfContents, setShowTableOfContents] = useState(false);
  const [copied, setCopied] = useState(false);
  const [currentVotes, setCurrentVotes] = useState({
    helpful: article.helpfulVotes,
    notHelpful: article.notHelpfulVotes
  });

  useEffect(() => {
    // Track article view
    trackArticleView();
    
    // Check if user has already voted or bookmarked
    checkUserInteractions();
  }, [article.id]);

  const trackArticleView = async () => {
    try {
      // In real implementation, this would call the API to increment view count
      console.log(`Tracking view for article ${article.id}`);
    } catch (error) {
      console.error('Failed to track article view:', error);
    }
  };

  const checkUserInteractions = async () => {
    try {
      // In real implementation, check if user has voted/bookmarked
      // This would come from user preferences or session storage
    } catch (error) {
      console.error('Failed to check user interactions:', error);
    }
  };

  const handleVote = async (isHelpful: boolean) => {
    if (hasVoted) {
      toast.error('You have already voted on this article');
      return;
    }

    try {
      // In real implementation, this would call the API
      const newVoteType = isHelpful ? 'helpful' : 'not-helpful';
      setHasVoted(newVoteType);
      
      if (isHelpful) {
        setCurrentVotes(prev => ({ ...prev, helpful: prev.helpful + 1 }));
      } else {
        setCurrentVotes(prev => ({ ...prev, notHelpful: prev.notHelpful + 1 }));
      }
      
      toast.success(isHelpful ? 'Thank you for your feedback!' : 'Feedback recorded');
    } catch (error) {
      console.error('Failed to vote:', error);
      toast.error('Failed to record your vote');
    }
  };

  const handleBookmark = async () => {
    try {
      setIsBookmarked(!isBookmarked);
      toast.success(isBookmarked ? 'Removed from bookmarks' : 'Added to bookmarks');
    } catch (error) {
      console.error('Failed to bookmark:', error);
      toast.error('Failed to update bookmark');
    }
  };

  const handleShare = async () => {
    try {
      if (navigator.share) {
        await navigator.share({
          title: article.title,
          text: article.excerpt,
          url: window.location.href
        });
      } else {
        await navigator.clipboard.writeText(window.location.href);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
        toast.success('Link copied to clipboard');
      }
    } catch (error) {
      console.error('Failed to share:', error);
      toast.error('Failed to share article');
    }
  };

  const handleDownloadAttachment = (filename: string) => {
    // In real implementation, this would download the file
    toast.success(`Downloading ${filename}...`);
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

  const formatArticleContent = (content: string) => {
    // In real implementation, this would be proper markdown rendering
    return content.split('\n').map((paragraph, index) => (
      <p key={index} className="mb-4 text-gray-700 leading-relaxed">
        {paragraph}
      </p>
    ));
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <Button variant="outline" onClick={onBack}>
          <ArrowLeft className="w-4 h-4 mr-2" />
          Back to Knowledge Base
        </Button>
        
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={handleShare}>
            {copied ? <Check className="w-4 h-4" /> : <Share2 className="w-4 h-4" />}
          </Button>
          
          <Button 
            variant={isBookmarked ? "default" : "outline"} 
            size="sm" 
            onClick={handleBookmark}
          >
            <Bookmark className="w-4 h-4" />
          </Button>
          
          {isAgentView && onEdit && (
            <Button variant="outline" size="sm" onClick={onEdit}>
              <Edit className="w-4 h-4 mr-2" />
              Edit
            </Button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-3">
          <Card>
            <CardHeader>
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-2">
                  {getTypeIcon(article.type)}
                  <Badge variant="outline" className="text-xs">
                    {article.type}
                  </Badge>
                  <Badge className={`text-xs ${getDifficultyColor(article.difficulty)}`}>
                    {article.difficulty}
                  </Badge>
                  <span className="text-sm text-gray-500 flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {article.estimatedReadTime} min read
                  </span>
                </div>
                
                <Badge variant="secondary" className="text-xs">
                  {article.category}
                </Badge>
              </div>

              <CardTitle className="text-3xl font-bold text-gray-900 leading-tight">
                {article.title}
              </CardTitle>

              {/* Article Meta */}
              <div className="flex items-center gap-6 text-sm text-gray-500 mt-4">
                <div className="flex items-center gap-1">
                  <User className="w-4 h-4" />
                  <span>By {article.author}</span>
                </div>
                
                <div className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  <span>Updated {formatDistanceToNow(new Date(article.updatedAt), { addSuffix: true })}</span>
                </div>
                
                <div className="flex items-center gap-1">
                  <Eye className="w-4 h-4" />
                  <span>{article.viewCount} views</span>
                </div>
              </div>

              {/* Tags */}
              {article.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-4">
                  {article.tags.map(tag => (
                    <Badge key={tag} variant="outline" className="text-xs">
                      <Tag className="w-2 h-2 mr-1" />
                      {tag}
                    </Badge>
                  ))}
                </div>
              )}
            </CardHeader>

            <CardContent>
              {/* Video Player for Video Articles */}
              {article.type === 'Video' && article.videoUrl && (
                <div className="mb-6">
                  <div className="aspect-video bg-gray-900 rounded-lg flex items-center justify-center">
                    <div className="text-center text-white">
                      <Video className="w-16 h-16 mx-auto mb-4" />
                      <p>Video Player</p>
                      <p className="text-sm text-gray-300 mt-2">
                        In a real implementation, this would be an embedded video player
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Article Content */}
              <div className="prose prose-lg max-w-none">
                {formatArticleContent(article.content)}
                
                {/* Mock additional content for demonstration */}
                <h2 className="text-2xl font-bold text-gray-900 mt-8 mb-4">Overview</h2>
                <p className="mb-4 text-gray-700 leading-relaxed">
                  This comprehensive guide will walk you through the essential steps needed to get started 
                  with algorithmic trading on the Alphintra platform. Whether you're a complete beginner 
                  or have some trading experience, this tutorial covers everything you need to know.
                </p>
                
                <h3 className="text-xl font-semibold text-gray-900 mt-6 mb-3">Key Topics Covered</h3>
                <ul className="list-disc list-inside mb-6 text-gray-700 space-y-2">
                  <li>Setting up your trading account and preferences</li>
                  <li>Understanding the Alphintra interface and tools</li>
                  <li>Creating your first algorithmic trading strategy</li>
                  <li>Backtesting and optimizing your strategy</li>
                  <li>Going live with paper trading</li>
                  <li>Risk management best practices</li>
                </ul>

                <h3 className="text-xl font-semibold text-gray-900 mt-6 mb-3">Prerequisites</h3>
                <p className="mb-4 text-gray-700 leading-relaxed">
                  Before starting this tutorial, ensure you have:
                </p>
                <ul className="list-disc list-inside mb-6 text-gray-700 space-y-2">
                  <li>A verified Alphintra account</li>
                  <li>Basic understanding of financial markets</li>
                  <li>Completed the platform onboarding process</li>
                </ul>
              </div>

              {/* Attachments */}
              {article.attachments && article.attachments.length > 0 && (
                <div className="mt-8 p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-900 mb-3 flex items-center gap-2">
                    <Download className="w-4 h-4" />
                    Downloads & Resources
                  </h4>
                  <div className="space-y-2">
                    {article.attachments.map(filename => (
                      <div key={filename} className="flex items-center justify-between p-2 bg-white rounded border">
                        <div className="flex items-center gap-2">
                          <FileText className="w-4 h-4 text-gray-500" />
                          <span className="text-sm">{filename}</span>
                        </div>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleDownloadAttachment(filename)}
                        >
                          <Download className="w-3 h-3 mr-1" />
                          Download
                        </Button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <Separator className="my-8" />

              {/* Article Feedback */}
              <div className="text-center py-6">
                <h4 className="text-lg font-medium text-gray-900 mb-4">Was this article helpful?</h4>
                <div className="flex items-center justify-center gap-4">
                  <Button
                    variant={hasVoted === 'helpful' ? "default" : "outline"}
                    onClick={() => handleVote(true)}
                    disabled={hasVoted !== null}
                    className="flex items-center gap-2"
                  >
                    <ThumbsUp className="w-4 h-4" />
                    Yes ({currentVotes.helpful})
                  </Button>
                  
                  <Button
                    variant={hasVoted === 'not-helpful' ? "destructive" : "outline"}
                    onClick={() => handleVote(false)}
                    disabled={hasVoted !== null}
                    className="flex items-center gap-2"
                  >
                    <ThumbsDown className="w-4 h-4" />
                    No ({currentVotes.notHelpful})
                  </Button>
                </div>
                
                {hasVoted && (
                  <p className="text-sm text-gray-600 mt-3">
                    Thank you for your feedback!
                  </p>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Table of Contents */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Table of Contents</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-2 text-sm">
                <button className="text-left text-blue-600 hover:text-blue-800 block">
                  Overview
                </button>
                <button className="text-left text-gray-600 hover:text-blue-600 block pl-2">
                  Key Topics Covered
                </button>
                <button className="text-left text-gray-600 hover:text-blue-600 block pl-2">
                  Prerequisites
                </button>
                <button className="text-left text-blue-600 hover:text-blue-800 block">
                  Step-by-Step Guide
                </button>
                <button className="text-left text-blue-600 hover:text-blue-800 block">
                  Best Practices
                </button>
                <button className="text-left text-blue-600 hover:text-blue-800 block">
                  Troubleshooting
                </button>
              </div>
            </CardContent>
          </Card>

          {/* Article Info */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Article Information</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-3 text-sm">
                <div>
                  <span className="text-gray-500">Created:</span>
                  <div className="font-medium">
                    {format(new Date(article.createdAt), 'MMM d, yyyy')}
                  </div>
                </div>
                
                <div>
                  <span className="text-gray-500">Last Updated:</span>
                  <div className="font-medium">
                    {format(new Date(article.updatedAt), 'MMM d, yyyy')}
                  </div>
                </div>
                
                <div>
                  <span className="text-gray-500">Category:</span>
                  <div className="font-medium">{article.category}</div>
                </div>
                
                <div>
                  <span className="text-gray-500">Difficulty:</span>
                  <Badge className={`text-xs mt-1 ${getDifficultyColor(article.difficulty)}`}>
                    {article.difficulty}
                  </Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Related Articles */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Related Articles</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-3">
                {mockRelatedArticles.map(relatedArticle => (
                  <button
                    key={relatedArticle.id}
                    className="w-full text-left p-3 rounded-lg border hover:bg-gray-50 transition-colors"
                  >
                    <div className="flex items-start gap-2">
                      {getTypeIcon(relatedArticle.type)}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 mb-1">
                          {relatedArticle.title}
                        </p>
                        <p className="text-xs text-gray-600 mb-2">
                          {relatedArticle.excerpt}
                        </p>
                        <div className="flex items-center gap-2 text-xs text-gray-500">
                          <Badge variant="outline" className="text-xs">
                            {relatedArticle.type}
                          </Badge>
                          <span>{relatedArticle.estimatedReadTime} min</span>
                        </div>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Quick Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-2">
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <ExternalLink className="w-3 h-3 mr-2" />
                  Open in New Tab
                </Button>
                
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <Copy className="w-3 h-3 mr-2" />
                  Copy Link
                </Button>
                
                <Button variant="outline" size="sm" className="w-full justify-start">
                  <Star className="w-3 h-3 mr-2" />
                  Rate Article
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}