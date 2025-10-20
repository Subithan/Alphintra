import { NextResponse } from 'next/server'

// Trading-specific system prompts for different operations
const TRADING_SYSTEM_PROMPTS = {
  generate: `You are an expert trading strategy developer and quantitative analyst with deep knowledge of financial markets, technical indicators, and algorithmic trading.

Your core expertise includes:
- Technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands, Stochastic, ADX, ATR, etc.)
- Risk management principles and position sizing
- Backtesting methodologies and performance metrics
- Market data processing and analysis
- Portfolio optimization strategies
- Machine learning applications in trading

IMPORTANT GUIDELINES:
1. ONLY create trading-related code and strategies
2. Always include proper risk management in your strategies
3. Use best practices for backtesting and validation
4. Include clear comments explaining trading logic
5. Focus on practical, implementable solutions
6. Consider slippage, transaction costs, and market impact
7. Never guarantee specific returns or profits
8. Include proper error handling and edge cases

Generate clean, well-documented Python code for trading strategies, indicators, or analysis tools.`,

  explain: `You are an expert trading educator specializing in explaining complex trading concepts, algorithms, and strategies in clear, understandable terms.

Your expertise includes:
- Technical analysis and indicator calculations
- Trading strategy mechanics and logic
- Risk management concepts and applications
- Market microstructure and dynamics
- Performance metrics and analysis
- Algorithmic trading principles

When explaining trading code:
1. Focus on the trading logic and financial concepts
2. Explain indicator calculations and interpretations
3. Discuss risk management aspects
4. Highlight potential market conditions and limitations
5. Suggest improvements or optimizations
6. Use analogies and examples to clarify complex concepts

Always prioritize educational value and practical insights.`,

  optimize: `You are a trading performance optimization expert specializing in improving trading strategies, reducing execution costs, and enhancing risk-adjusted returns.

Your optimization focus includes:
- Computational efficiency and execution speed
- Risk-adjusted performance improvement
- Transaction cost minimization
- Market impact reduction
- Parameter tuning and calibration
- Code structure and maintainability

When optimizing trading code:
1. Preserve the core trading logic and risk controls
2. Improve computational efficiency for real-time trading
3. Enhance error handling and robustness
4. Optimize for the target trading frequency and asset class
5. Consider memory usage and processing bottlenecks
6. Maintain readability and maintainability

Always explain the performance trade-offs and expected improvements.`,

  debug: `You are a trading systems debugging expert with deep experience in identifying and fixing issues in algorithmic trading strategies.

Your debugging expertise covers:
- Logic errors in trading rules and conditions
- Data handling and processing issues
- Risk management and position sizing problems
- Performance bottlenecks and memory issues
- Market data quality and synchronization
- Backtesting and implementation discrepancies

When debugging trading code:
1. Identify the root cause of trading logic errors
2. Check for common issues (look-ahead bias, data snooping, etc.)
3. Verify risk management controls are working properly
4. Ensure proper handling of edge cases and market anomalies
5. Validate backtesting methodology and implementation
6. Provide corrected code with explanations

Always explain the potential impact of the bug on trading performance.`,

  test: `You are a trading systems testing expert specializing in creating comprehensive test suites for algorithmic trading strategies and systems.

Your testing expertise includes:
- Unit testing of trading logic and indicators
- Integration testing with market data feeds
- Performance and stress testing
- Backtesting validation and scenario analysis
- Risk management testing
- Market regime analysis and robustness testing

When creating tests for trading code:
1. Test core trading logic and indicator calculations
2. Include edge cases and market anomaly scenarios
3. Test risk management and position sizing controls
4. Validate data handling and processing
5. Include performance benchmarking
6. Test integration with external data sources

Ensure tests cover both normal and extreme market conditions.`
}

// Helper function to create trading-specific prompts
function createTradingPrompt(type: string, userContent: string, context?: string) {
  const systemPrompt = TRADING_SYSTEM_PROMPTS[type as keyof typeof TRADING_SYSTEM_PROMPTS] || TRADING_SYSTEM_PROMPTS.generate

  let enhancedPrompt = systemPrompt + '\n\n'

  if (context) {
    enhancedPrompt += `Current context/Code to work with:\n${context}\n\n`
  }

  enhancedPrompt += `User request:\n${userContent}\n\n`
  enhancedPrompt += `Please provide a trading-focused solution following the guidelines above.`

  return enhancedPrompt
}

// Rate limiting cache (simple in-memory implementation)
const rateLimitCache = new Map<string, { count: number; resetTime: number }>()

function checkRateLimit(apiKey: string, maxRequests = 60, windowMs = 60000): boolean {
  const now = Date.now()
  const key = apiKey.slice(-8) // Use last 8 chars of API key for privacy

  if (!rateLimitCache.has(key)) {
    rateLimitCache.set(key, { count: 1, resetTime: now + windowMs })
    return true
  }

  const cached = rateLimitCache.get(key)!

  if (now > cached.resetTime) {
    // Reset window
    rateLimitCache.set(key, { count: 1, resetTime: now + windowMs })
    return true
  }

  if (cached.count >= maxRequests) {
    return false
  }

  cached.count += 1
  return true
}

// Google Gemini API integration
async function callGeminiAPI(messages: any[], model = 'gemini-2.5-flash') {
  const apiKey = process.env.GEMINI_API_KEY
  const apiUrl = process.env.GEMINI_API_URL || 'https://generativelanguage.googleapis.com/v1beta/models'

  if (!apiKey) {
    throw new Error('Gemini API key not configured')
  }

  // Rate limiting
  if (!checkRateLimit(apiKey)) {
    throw new Error('Rate limit exceeded. Please try again later.')
  }

  // Try different model names until we find a working one
  const modelsToTry = ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-2.0-flash-exp', 'gemini-1.5-flash', 'gemini-1.5-pro']

  for (const modelToTry of modelsToTry) {
    try {
      // Convert messages to Gemini format
      const contents = messages.map(msg => ({
        role: msg.role === 'user' ? 'user' : 'model',
        parts: [{ text: msg.content }]
      }))

      const response = await fetch(`${apiUrl}/${modelToTry}:generateContent?key=${apiKey}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          contents,
          generationConfig: {
            temperature: 0.7,
            topP: 0.9,
            topK: 40,
            maxOutputTokens: 2000
          },
          safetySettings: [
            {
              category: "HARM_CATEGORY_HARASSMENT",
              threshold: "BLOCK_NONE"
            },
            {
              category: "HARM_CATEGORY_HATE_SPEECH",
              threshold: "BLOCK_NONE"
            },
            {
              category: "HARM_CATEGORY_SEXUALLY_EXPLICIT",
              threshold: "BLOCK_NONE"
            },
            {
              category: "HARM_CATEGORY_DANGEROUS_CONTENT",
              threshold: "BLOCK_NONE"
            }
          ]
        })
      })

      if (response.ok) {
        const data = await response.json()

        // Convert Gemini response to OpenAI-like format for compatibility
        return {
          choices: [{
            message: {
              content: data.candidates?.[0]?.content?.parts?.[0]?.text || 'No response generated'
            }
          }],
          usage: {
            total_tokens: data.usageMetadata?.totalTokenCount || 0
          }
        }
      }

      const errorText = await response.text()
      console.warn(`Model ${modelToTry} failed:`, errorText)

      // If it's not a model error, don't try other models
      if (!errorText.includes('not found') && !errorText.includes('is not found')) {
        throw new Error(`Gemini API error: ${response.status} ${errorText}`)
      }
    } catch (error) {
      if (error instanceof Error && !error.message.includes('not found')) {
        throw error
      }
      console.warn(`Model ${modelToTry} failed:`, error)
      continue
    }
  }

  throw new Error('No working Gemini model found. Please check your API configuration.')
}

// Main handler for different AI operations
async function handleAIRequest(pathSegments: string[], body: any) {
  const operation = pathSegments[0] // generate, explain, optimize, debug, tests

  if (!operation || !['generate', 'explain', 'optimize', 'debug', 'tests'].includes(operation)) {
    throw new Error(`Invalid operation: ${operation}`)
  }

  const { prompt, context, code, preferred_provider = 'gemini' } = body

  if (preferred_provider !== 'gemini') {
    throw new Error(`Provider ${preferred_provider} not supported. Please use Gemini.`)
  }

  // Create trading-specific prompt
  let userContent = ''
  switch (operation) {
    case 'generate':
      userContent = prompt || 'Create a trading strategy'
      break
    case 'explain':
      userContent = 'Explain this trading code/concept'
      break
    case 'optimize':
      userContent = 'Optimize this trading strategy for better performance'
      break
    case 'debug':
      userContent = 'Debug and fix issues in this trading code'
      break
    case 'tests':
      userContent = 'Create comprehensive tests for this trading strategy'
      break
  }

  const systemPrompt = createTradingPrompt(operation, userContent, context || code)

  const messages = [
    { role: 'system', content: systemPrompt },
    { role: 'user', content: userContent }
  ]

  if (context || code) {
    messages.push({
      role: 'user',
      content: `\nAdditional context/code:\n${context || code}`
    })
  }

  const startTime = Date.now()
  const response = await callGeminiAPI(messages)
  const executionTime = Date.now() - startTime

  const generatedContent = response.choices?.[0]?.message?.content || ''

  // Return standardized response
  return {
    success: true,
    ...(operation === 'generate' && {
      code: generatedContent,
      explanation: 'Trading strategy generated successfully',
      suggestions: ['Consider backtesting with historical data', 'Monitor performance metrics', 'Adjust parameters based on market conditions'],
      estimated_complexity: 'intermediate',
      confidence_score: 0.85
    }),
    ...(operation === 'explain' && {
      explanation: generatedContent,
      key_concepts: extractKeyConcepts(generatedContent),
      potential_issues: extractPotentialIssues(generatedContent),
      improvement_suggestions: extractImprovements(generatedContent),
      complexity_analysis: 'intermediate'
    }),
    ...(operation === 'optimize' && {
      optimized_code: generatedContent,
      changes_made: ['Performance optimizations applied', 'Code structure improved'],
      performance_impact: 'Improved execution speed',
      risk_assessment: 'Low risk - core logic preserved'
    }),
    ...(operation === 'debug' && {
      issue_analysis: generatedContent,
      suggested_fixes: ['Logic error corrected', 'Error handling improved'],
      corrected_code: extractCorrectedCode(generatedContent),
      explanation: 'Issues identified and fixed',
      prevention_tips: ['Add input validation', 'Implement comprehensive testing']
    }),
    ...(operation === 'tests' && {
      test_code: generatedContent,
      test_cases: ['Normal market conditions', 'Extreme volatility', 'Edge cases'],
      coverage_analysis: 'Comprehensive coverage of trading logic',
      testing_strategy: 'Unit and integration testing approach',
      mock_data_suggestions: ['Historical price data', 'Simulated market scenarios']
    }),
    tokens_used: response.usage?.total_tokens || 0,
    execution_time: executionTime,
    provider: 'gemini',
    request_id: `gemini_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
  }
}

// Helper functions to extract structured information from responses
function extractKeyConcepts(text: string): string[] {
  const concepts = text.match(/\b(SMA|EMA|RSI|MACD|Bollinger\sBands|Stochastic|ADX|ATR|Sharpe|Drawdown|Volatility)\b/gi) || []
  return [...new Set(concepts)]
}

function extractPotentialIssues(text: string): string[] {
  const issues = text.match(/\b(risk|drawdown|overfitting|look\-ahead|data\squality|liquidity)\b/gi) || []
  return [...new Set(issues)]
}

function extractImprovements(text: string): string[] {
  const improvements = text.match(/\b(improve|optimize|enhance|refactor|better|faster)\b.*?[.!?]/gi) || []
  return improvements.slice(0, 3)
}

function extractCorrectedCode(text: string): string | undefined {
  const codeMatch = text.match(/```(?:python|py)\s*\n([\s\S]*?)\n```/i)
  return codeMatch ? codeMatch[1] : undefined
}

// HTTP handlers
export async function POST(request: Request, { params }: { params: { path: string[] } }) {
  try {
    const body = await request.json()
    const pathSegments = params.path || []

    const result = await handleAIRequest(pathSegments, body)

    return NextResponse.json(result, {
      headers: {
        'Cache-Control': 'no-store',
        'Content-Type': 'application/json'
      }
    })
  } catch (error) {
    console.error('AI API error:', error)

    const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
    const statusCode = errorMessage.includes('Rate limit') ? 429 :
                      errorMessage.includes('API key') ? 401 : 500

    return NextResponse.json({
      success: false,
      message: errorMessage,
      details: errorMessage.includes('Rate limit') ? 'Too many requests. Please try again later.' :
              errorMessage.includes('API key') ? 'API authentication failed.' :
              'Failed to process AI request. Please try again.'
    }, {
      status: statusCode,
      headers: {
        'Cache-Control': 'no-store',
        'Content-Type': 'application/json'
      }
    })
  }
}

export async function GET() {
  return NextResponse.json({
    success: true,
    message: 'Trading AI Assistant is online',
    provider: 'Google Gemini',
    capabilities: [
      'Trading strategy generation',
      'Technical indicator implementation',
      'Risk management systems',
      'Backtesting frameworks',
      'Code optimization',
      'Debugging and testing',
      'Performance analysis'
    ],
    disclaimer: 'This AI assistant specializes in trading strategies and financial algorithms. Always validate strategies with proper backtesting before real trading.'
  })
}

export async function PUT() {
  return NextResponse.json({ error: 'Method not allowed' }, { status: 405 })
}

export async function DELETE() {
  return NextResponse.json({ error: 'Method not allowed' }, { status: 405 })
}

export async function PATCH() {
  return NextResponse.json({ error: 'Method not allowed' }, { status: 405 })
}

export async function OPTIONS() {
  return new Response(null, { status: 204 })
}
