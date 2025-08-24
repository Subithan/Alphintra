'use client';

import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Bot, 
  Send, 
  Lightbulb, 
  MessageSquare, 
  Search, 
  Copy, 
  ThumbsUp, 
  ThumbsDown,
  RefreshCw,
  Zap,
  BookOpen,
  Users,
  TrendingUp,
  Settings,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Brain,
  Target
} from 'lucide-react';
import { 
  customerSupportApi,
  Ticket,
  Communication,
  TicketCategory,
  TicketPriority
} from '@/lib/api/customer-support-api';
import { formatDistanceToNow } from 'date-fns';
import { toast } from 'react-hot-toast';

interface AIAssistantPanelProps {
  currentTicket?: Ticket;
  agentId: string;
  onSuggestionApply?: (suggestion: string) => void;
  className?: string;
}

interface AISuggestion {
  id: string;
  type: 'response' | 'solution' | 'escalation' | 'knowledge' | 'priority';
  title: string;
  content: string;
  confidence: number;
  reasoning: string;
  sources?: string[];
  tags?: string[];
}

interface AIConversation {
  id: string;
  message: string;
  response: string;
  timestamp: string;
  isHelpful?: boolean;
}

// Mock AI suggestions based on ticket context
const generateMockSuggestions = (ticket?: Ticket): AISuggestion[] => {
  if (!ticket) {
    return [
      {
        id: '1',
        type: 'knowledge',
        title: 'Getting Started Guide',
        content: 'New users often benefit from our comprehensive getting started guide. Consider sharing this resource.',
        confidence: 85,
        reasoning: 'High success rate for onboarding-related questions',
        sources: ['KB-001', 'Tutorial-basics']
      }
    ];
  }

  const suggestions: AISuggestion[] = [];

  // Response suggestions based on ticket category
  if (ticket.category === TicketCategory.TECHNICAL) {
    suggestions.push({
      id: '1',
      type: 'response',
      title: 'Technical Troubleshooting Response',
      content: `Thank you for reporting this technical issue. I understand you're experiencing ${ticket.title.toLowerCase()}. Let me help you resolve this step by step.

First, could you please try the following:
1. Clear your browser cache and cookies
2. Disable any browser extensions temporarily
3. Try accessing the platform in an incognito/private window

If the issue persists, please share:
- Your browser version and operating system
- Any error messages you're seeing
- Screenshots if possible

I'll monitor this closely and ensure we get this resolved quickly for you.`,
      confidence: 92,
      reasoning: 'Standard technical troubleshooting approach with high success rate',
      tags: ['technical', 'troubleshooting', 'systematic']
    });

    suggestions.push({
      id: '2',
      type: 'solution',
      title: 'Common Browser Issues Solution',
      content: 'This appears to be a browser compatibility issue. Our data shows 87% of similar cases are resolved by updating to the latest browser version or switching to Chrome/Firefox.',
      confidence: 87,
      reasoning: 'Pattern recognition from similar resolved tickets',
      sources: ['KB-tech-001', 'Resolution-stats']
    });
  }

  if (ticket.category === TicketCategory.STRATEGY_DEVELOPMENT) {
    suggestions.push({
      id: '3',
      type: 'response',
      title: 'Strategy Development Guidance',
      content: `I'd be happy to help you with your strategy development question. Based on your inquiry about ${ticket.title.toLowerCase()}, here are some recommendations:

1. Start with our Strategy Builder tutorial in the knowledge base
2. Consider using our backtesting environment to validate your approach
3. Review risk management settings before going live

Would you like me to schedule a one-on-one strategy consultation session? Our experts can provide personalized guidance for your specific use case.`,
      confidence: 89,
      reasoning: 'Structured approach for strategy-related inquiries',
      tags: ['strategy', 'guidance', 'educational']
    });

    suggestions.push({
      id: '4',
      type: 'knowledge',
      title: 'Strategy Development Resources',
      content: 'Recommend sharing the "Advanced Strategy Patterns" guide and "Risk Management Best Practices" articles.',
      confidence: 94,
      reasoning: 'High relevance for strategy development questions',
      sources: ['KB-strategy-001', 'KB-risk-001']
    });
  }

  // Priority suggestions
  if (ticket.title.toLowerCase().includes('urgent') || ticket.title.toLowerCase().includes('critical')) {
    suggestions.push({
      id: '5',
      type: 'priority',
      title: 'Priority Escalation Recommendation',
      content: 'This ticket contains urgent language and may require priority handling or escalation to L2 support.',
      confidence: 78,
      reasoning: 'Keyword analysis indicates urgency',
      tags: ['escalation', 'priority']
    });
  }

  // Escalation suggestions based on complexity
  if (ticket.description.length > 500 || ticket.escalationLevel > 0) {
    suggestions.push({
      id: '6',
      type: 'escalation',
      title: 'Consider L3 Specialist Escalation',
      content: 'This appears to be a complex technical issue that may benefit from specialist expertise. Consider escalating to L3 for faster resolution.',
      confidence: 83,
      reasoning: 'Complexity indicators suggest specialist involvement needed',
      tags: ['escalation', 'specialist']
    });
  }

  return suggestions;
};

const mockConversations: AIConversation[] = [
  {
    id: '1',
    message: 'How should I handle a customer who is frustrated about trading losses?',
    response: 'When dealing with frustrated customers about trading losses, focus on empathy and education. Acknowledge their feelings, remind them that all trading involves risk, and offer resources for risk management education. Consider scheduling a consultation with our trading experts if appropriate.',
    timestamp: '2024-01-17T10:30:00Z',
    isHelpful: true
  },
  {
    id: '2',
    message: 'What are the best practices for handling API integration issues?',
    response: 'For API integration issues: 1) First verify API credentials and permissions, 2) Check rate limiting, 3) Review error logs for specific error codes, 4) Test with our sandbox environment, 5) Share our API documentation and SDK examples. Escalate to technical team if the issue persists after basic troubleshooting.',
    timestamp: '2024-01-17T09:15:00Z'
  }
];

export default function AIAssistantPanel({ 
  currentTicket, 
  agentId, 
  onSuggestionApply,
  className = ''
}: AIAssistantPanelProps) {
  const [suggestions, setSuggestions] = useState<AISuggestion[]>([]);
  const [conversations, setConversations] = useState<AIConversation[]>(mockConversations);
  const [currentMessage, setCurrentMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [expandedSuggestion, setExpandedSuggestion] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState('suggestions');
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (currentTicket) {
      generateSuggestions();
    }
  }, [currentTicket]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [conversations]);

  const generateSuggestions = async () => {
    setIsLoading(true);
    try {
      // In real implementation, this would call the AI service
      const newSuggestions = generateMockSuggestions(currentTicket);
      setSuggestions(newSuggestions);
    } catch (error) {
      console.error('Failed to generate AI suggestions:', error);
      toast.error('Failed to generate AI suggestions');
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async () => {
    if (!currentMessage.trim()) return;

    const message = currentMessage.trim();
    setCurrentMessage('');
    setIsLoading(true);

    try {
      // Add user message to conversation
      const newConversation: AIConversation = {
        id: Date.now().toString(),
        message,
        response: '', // Will be filled by AI response
        timestamp: new Date().toISOString()
      };

      // Simulate AI processing time
      setTimeout(() => {
        const aiResponse = generateAIResponse(message);
        newConversation.response = aiResponse;
        setConversations(prev => [...prev, newConversation]);
        setIsLoading(false);
      }, 2000);
    } catch (error) {
      console.error('Failed to get AI response:', error);
      toast.error('Failed to get AI response');
      setIsLoading(false);
    }
  };

  const generateAIResponse = (message: string): string => {
    // Simple mock AI response logic
    const lowerMessage = message.toLowerCase();
    
    if (lowerMessage.includes('frustrated') || lowerMessage.includes('angry')) {
      return 'When dealing with frustrated customers, use the HEART method: Hear them out, Empathize, Apologize if appropriate, Respond with solutions, and Take ownership. Always validate their feelings first before moving to problem-solving.';
    }
    
    if (lowerMessage.includes('technical') || lowerMessage.includes('api')) {
      return 'For technical issues, follow our structured troubleshooting approach: 1) Gather specific error details, 2) Check our known issues database, 3) Reproduce the issue if possible, 4) Apply standard solutions, 5) Escalate if needed. Always keep the customer informed of your progress.';
    }
    
    if (lowerMessage.includes('escalate') || lowerMessage.includes('escalation')) {
      return 'Escalate tickets when: 1) The issue is beyond your expertise level, 2) Customer requests a manager, 3) SLA is at risk, 4) Issue affects multiple customers, or 5) Security concerns arise. Always provide context and attempted solutions when escalating.';
    }
    
    return 'I understand your question. Based on our best practices and customer success data, I recommend taking a systematic approach. Focus on understanding the root cause, communicating clearly with the customer, and following our established procedures. Would you like me to provide more specific guidance for this situation?';
  };

  const applySuggestion = (suggestion: AISuggestion) => {
    if (onSuggestionApply) {
      onSuggestionApply(suggestion.content);
      toast.success('Suggestion applied to response');
    }
  };

  const copySuggestion = async (content: string) => {
    try {
      await navigator.clipboard.writeText(content);
      toast.success('Copied to clipboard');
    } catch (error) {
      toast.error('Failed to copy');
    }
  };

  const rateSuggestion = async (suggestionId: string, isHelpful: boolean) => {
    try {
      // In real implementation, this would send feedback to the AI service
      toast.success(isHelpful ? 'Thank you for the feedback!' : 'Feedback recorded');
    } catch (error) {
      toast.error('Failed to record feedback');
    }
  };

  const rateConversation = async (conversationId: string, isHelpful: boolean) => {
    setConversations(prev => prev.map(conv => 
      conv.id === conversationId 
        ? { ...conv, isHelpful }
        : conv
    ));
    toast.success('Feedback recorded');
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 90) return 'text-green-600 bg-green-50';
    if (confidence >= 75) return 'text-blue-600 bg-blue-50';
    if (confidence >= 60) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  const getSuggestionIcon = (type: string) => {
    switch (type) {
      case 'response':
        return <MessageSquare className="w-4 h-4" />;
      case 'solution':
        return <Lightbulb className="w-4 h-4" />;
      case 'escalation':
        return <TrendingUp className="w-4 h-4" />;
      case 'knowledge':
        return <BookOpen className="w-4 h-4" />;
      case 'priority':
        return <Target className="w-4 h-4" />;
      default:
        return <Brain className="w-4 h-4" />;
    }
  };

  return (
    <Card className={`h-full flex flex-col ${className}`}>
      <CardHeader className="flex-shrink-0">
        <CardTitle className="flex items-center gap-2">
          <Bot className="w-5 h-5 text-blue-500" />
          AI Assistant
          <Sparkles className="w-4 h-4 text-yellow-500" />
        </CardTitle>
        {currentTicket && (
          <p className="text-sm text-gray-600">
            Analyzing ticket #{currentTicket.ticketId} - {currentTicket.category}
          </p>
        )}
      </CardHeader>

      <CardContent className="flex-1 flex flex-col p-0">
        <Tabs value={selectedTab} onValueChange={setSelectedTab} className="flex-1 flex flex-col">
          <TabsList className="mx-4 mb-4">
            <TabsTrigger value="suggestions" className="flex items-center gap-2">
              <Lightbulb className="w-3 h-3" />
              Smart Suggestions
            </TabsTrigger>
            <TabsTrigger value="chat" className="flex items-center gap-2">
              <MessageSquare className="w-3 h-3" />
              AI Chat
            </TabsTrigger>
            <TabsTrigger value="insights" className="flex items-center gap-2">
              <TrendingUp className="w-3 h-3" />
              Insights
            </TabsTrigger>
          </TabsList>

          <TabsContent value="suggestions" className="flex-1 mx-4 mb-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-medium">Smart Suggestions</h3>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={generateSuggestions}
                disabled={isLoading}
              >
                <RefreshCw className={`w-3 h-3 mr-1 ${isLoading ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
            </div>

            <ScrollArea className="h-[500px]">
              {isLoading ? (
                <div className="space-y-4">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="animate-pulse border rounded-lg p-4">
                      <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                      <div className="h-3 bg-gray-200 rounded w-1/2 mb-2"></div>
                      <div className="h-16 bg-gray-200 rounded"></div>
                    </div>
                  ))}
                </div>
              ) : suggestions.length === 0 ? (
                <div className="text-center py-8 text-gray-500">
                  <Bot className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                  <p>No suggestions available</p>
                  <p className="text-sm">Select a ticket to get AI-powered suggestions</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {suggestions.map((suggestion) => (
                    <div key={suggestion.id} className="border rounded-lg">
                      <div className="p-4">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-2">
                            {getSuggestionIcon(suggestion.type)}
                            <h4 className="font-medium text-sm">{suggestion.title}</h4>
                          </div>
                          
                          <div className="flex items-center gap-2">
                            <Badge className={`text-xs ${getConfidenceColor(suggestion.confidence)}`}>
                              {suggestion.confidence}% confident
                            </Badge>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => setExpandedSuggestion(
                                expandedSuggestion === suggestion.id ? null : suggestion.id
                              )}
                            >
                              {expandedSuggestion === suggestion.id ? 
                                <ChevronUp className="w-3 h-3" /> : 
                                <ChevronDown className="w-3 h-3" />
                              }
                            </Button>
                          </div>
                        </div>

                        <p className="text-sm text-gray-600 mb-3 line-clamp-2">
                          {suggestion.content.substring(0, 150)}...
                        </p>

                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            {suggestion.tags?.map(tag => (
                              <Badge key={tag} variant="secondary" className="text-xs">
                                {tag}
                              </Badge>
                            ))}
                          </div>
                          
                          <div className="flex items-center gap-1">
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => copySuggestion(suggestion.content)}
                            >
                              <Copy className="w-3 h-3" />
                            </Button>
                            
                            {onSuggestionApply && suggestion.type === 'response' && (
                              <Button
                                size="sm"
                                onClick={() => applySuggestion(suggestion)}
                              >
                                <Zap className="w-3 h-3 mr-1" />
                                Apply
                              </Button>
                            )}
                          </div>
                        </div>

                        {expandedSuggestion === suggestion.id && (
                          <div className="mt-4 pt-4 border-t">
                            <div className="space-y-3">
                              <div>
                                <h5 className="text-sm font-medium mb-1">Full Content:</h5>
                                <p className="text-sm text-gray-700 whitespace-pre-wrap">
                                  {suggestion.content}
                                </p>
                              </div>
                              
                              <div>
                                <h5 className="text-sm font-medium mb-1">AI Reasoning:</h5>
                                <p className="text-sm text-gray-600">{suggestion.reasoning}</p>
                              </div>

                              {suggestion.sources && (
                                <div>
                                  <h5 className="text-sm font-medium mb-1">Sources:</h5>
                                  <div className="flex flex-wrap gap-1">
                                    {suggestion.sources.map(source => (
                                      <Badge key={source} variant="outline" className="text-xs">
                                        {source}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              )}

                              <div className="flex items-center gap-2 pt-2">
                                <span className="text-xs text-gray-500">Was this helpful?</span>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => rateSuggestion(suggestion.id, true)}
                                >
                                  <ThumbsUp className="w-3 h-3" />
                                </Button>
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => rateSuggestion(suggestion.id, false)}
                                >
                                  <ThumbsDown className="w-3 h-3" />
                                </Button>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </TabsContent>

          <TabsContent value="chat" className="flex-1 mx-4 mb-4 flex flex-col">
            <ScrollArea className="flex-1 h-[400px] mb-4">
              <div className="space-y-4">
                {conversations.map((conversation) => (
                  <div key={conversation.id} className="space-y-3">
                    {/* User Message */}
                    <div className="flex justify-end">
                      <div className="bg-blue-500 text-white rounded-lg p-3 max-w-[80%]">
                        <p className="text-sm">{conversation.message}</p>
                      </div>
                    </div>

                    {/* AI Response */}
                    <div className="flex justify-start">
                      <div className="bg-gray-100 rounded-lg p-3 max-w-[80%]">
                        <div className="flex items-center gap-2 mb-2">
                          <Bot className="w-4 h-4 text-blue-500" />
                          <span className="text-xs text-gray-600">AI Assistant</span>
                        </div>
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">
                          {conversation.response}
                        </p>
                        
                        <div className="flex items-center justify-between mt-3">
                          <span className="text-xs text-gray-500">
                            {formatDistanceToNow(new Date(conversation.timestamp), { addSuffix: true })}
                          </span>
                          
                          <div className="flex items-center gap-1">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => rateConversation(conversation.id, true)}
                              className={conversation.isHelpful === true ? 'text-green-600' : ''}
                            >
                              <ThumbsUp className="w-3 h-3" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => rateConversation(conversation.id, false)}
                              className={conversation.isHelpful === false ? 'text-red-600' : ''}
                            >
                              <ThumbsDown className="w-3 h-3" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                
                {isLoading && (
                  <div className="flex justify-start">
                    <div className="bg-gray-100 rounded-lg p-3">
                      <div className="flex items-center gap-2">
                        <Bot className="w-4 h-4 text-blue-500" />
                        <div className="flex space-x-1">
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={chatEndRef} />
              </div>
            </ScrollArea>

            {/* Chat Input */}
            <div className="flex gap-2">
              <Input
                value={currentMessage}
                onChange={(e) => setCurrentMessage(e.target.value)}
                placeholder="Ask AI for support guidance..."
                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                disabled={isLoading}
              />
              <Button onClick={sendMessage} disabled={isLoading || !currentMessage.trim()}>
                <Send className="w-4 h-4" />
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="insights" className="flex-1 mx-4 mb-4">
            <ScrollArea className="h-[500px]">
              <div className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Performance Insights</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Your avg response time:</span>
                        <span className="font-medium">2.3 min</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Team average:</span>
                        <span className="font-medium">3.1 min</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Customer satisfaction:</span>
                        <span className="font-medium text-green-600">4.7/5</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Knowledge Recommendations</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <button className="text-left text-blue-600 hover:text-blue-800 block">
                        • Review: API Rate Limiting Guide
                      </button>
                      <button className="text-left text-blue-600 hover:text-blue-800 block">
                        • Study: Customer Escalation Procedures
                      </button>
                      <button className="text-left text-blue-600 hover:text-blue-800 block">
                        • Update: New Trading Features FAQ
                      </button>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm">Recent Patterns</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm text-gray-600">
                      <p>• 23% increase in API integration questions this week</p>
                      <p>• Browser compatibility issues trending up</p>
                      <p>• Strategy development requests peak on Mondays</p>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}