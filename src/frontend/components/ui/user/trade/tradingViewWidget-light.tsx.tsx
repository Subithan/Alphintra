'use client';

import { useEffect, useRef, memo } from 'react';
import { useTheme } from 'next-themes';

const TradingViewWidget = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const { theme } = useTheme(); // Detect theme from next-themes

  useEffect(() => {
    if (!containerRef.current) return;

    // Clear container on rerender
    containerRef.current.innerHTML = '';

    const script = document.createElement('script');
    script.src = 'https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js';
    script.type = 'text/javascript';
    script.async = true;

    const currentTheme = theme === 'dark' ? 'dark' : 'light';

    script.innerHTML = `
      {
        "autosize": true,
        "symbol": "OKX:BTCUSD",
        "interval": "D",
        "timezone": "Etc/UTC",
        "theme": "${currentTheme}",
        "style": "1",
        "locale": "en",
        "hide_top_toolbar": false,
        "hide_side_toolbar": true,
        "allow_symbol_change": true,
        "save_image": true,
        "backgroundColor": "${currentTheme === 'dark' ? '#020817' : '#ffffff'}",
        "gridColor": "rgba(46, 46, 46, 0.06)"
      }
    `;

    containerRef.current.appendChild(script);
  }, [theme]); // Re-render when theme changes

  return (
    <div
      className="tradingview-widget-container"
      ref={containerRef}
      style={{ height: '100%', width: '100%' }}
    >
      <div
        className="tradingview-widget-container__widget"
        style={{ height: 'calc(100% - 32px)', width: '100%' }}
      />
      <div className="tradingview-widget-copyright">
        <a
          href="https://www.tradingview.com/"
          rel="noopener noreferrer"
          target="_blank"
        >
          <span className="blue-text">Track all markets on TradingView</span>
        </a>
      </div>
    </div>
  );
};

export default memo(TradingViewWidget);
