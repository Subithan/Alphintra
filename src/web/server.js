const express = require('express');
const cors = require('cors');
const path = require('path');

const app = express();
const port = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// Serve static dashboard
app.get('/', (req, res) => {
    res.send(`
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Alphintra Trading Platform</title>
        <style>
            body { 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
            }
            .container { 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 20px; 
            }
            .header { 
                text-align: center; 
                margin-bottom: 40px; 
                padding: 40px 0;
            }
            .header h1 { 
                font-size: 3em; 
                margin: 0; 
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
            .header p { 
                font-size: 1.2em; 
                margin: 10px 0; 
                opacity: 0.9;
            }
            .grid { 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
                gap: 20px; 
                margin-bottom: 40px;
            }
            .card { 
                background: rgba(255,255,255,0.1); 
                padding: 30px; 
                border-radius: 15px; 
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255,255,255,0.2);
                transition: transform 0.3s ease;
            }
            .card:hover { 
                transform: translateY(-5px); 
            }
            .card h3 { 
                margin-top: 0; 
                color: #fff;
                font-size: 1.5em;
            }
            .status { 
                padding: 8px 16px; 
                border-radius: 20px; 
                font-weight: bold; 
                display: inline-block;
                margin: 10px 0;
            }
            .status.online { 
                background: rgba(76, 175, 80, 0.3); 
                border: 1px solid #4CAF50;
            }
            .metrics { 
                display: flex; 
                justify-content: space-between; 
                margin: 20px 0;
            }
            .metric { 
                text-align: center; 
            }
            .metric-value { 
                font-size: 2em; 
                font-weight: bold; 
                color: #4CAF50;
            }
            .metric-label { 
                font-size: 0.9em; 
                opacity: 0.8;
            }
            .links { 
                text-align: center; 
                margin-top: 40px;
            }
            .link-button { 
                display: inline-block; 
                padding: 12px 24px; 
                margin: 10px; 
                background: rgba(255,255,255,0.2); 
                color: white; 
                text-decoration: none; 
                border-radius: 25px; 
                border: 1px solid rgba(255,255,255,0.3);
                transition: all 0.3s ease;
            }
            .link-button:hover { 
                background: rgba(255,255,255,0.3); 
                transform: translateY(-2px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 Alphintra Trading Platform</h1>
                <p>Enterprise-Grade Algorithmic Trading with AI/ML</p>
                <div class="status online">Local Development Environment</div>
            </div>
            
            <div class="grid">
                <div class="card">
                    <h3>📊 Trading Engine</h3>
                    <div class="status online">Online</div>
                    <p>Ultra-low latency order execution and market making</p>
                    <div class="metrics">
                        <div class="metric">
                            <div class="metric-value">0.3ms</div>
                            <div class="metric-label">Latency</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">1.2M</div>
                            <div class="metric-label">Orders/sec</div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <h3>🤖 AI/ML Services</h3>
                    <div class="status online">Online</div>
                    <p>Generative AI strategy synthesis and market analysis</p>
                    <div class="metrics">
                        <div class="metric">
                            <div class="metric-value">3</div>
                            <div class="metric-label">LLM Models</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">Real-time</div>
                            <div class="metric-label">Analysis</div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <h3>🌍 Global Services</h3>
                    <div class="status online">Online</div>
                    <p>Multi-region coordination and compliance</p>
                    <div class="metrics">
                        <div class="metric">
                            <div class="metric-value">3</div>
                            <div class="metric-label">Regions</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">24/7</div>
                            <div class="metric-label">Operations</div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <h3>📈 Portfolio Analytics</h3>
                    <div class="status online">Online</div>
                    <p>Advanced portfolio optimization and risk management</p>
                    <div class="metrics">
                        <div class="metric">
                            <div class="metric-value">99.99%</div>
                            <div class="metric-label">Uptime</div>
                        </div>
                        <div class="metric">
                            <div class="metric-value">Real-time</div>
                            <div class="metric-label">Risk Monitor</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="links">
                <a href="http://localhost:8080/docs" class="link-button">📚 API Documentation</a>
                <a href="http://localhost:3001" class="link-button">📊 Monitoring</a>
                <a href="http://localhost:8000" class="link-button">📖 Architecture Guide</a>
                <a href="http://localhost:8080/health" class="link-button">🏥 Health Check</a>
            </div>
        </div>
    </body>
    </html>
    `);
});

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        service: 'alphintra-dashboard',
        timestamp: new Date().toISOString()
    });
});

app.listen(port, () => {
    console.log(`Alphintra Dashboard running on port ${port}`);
});