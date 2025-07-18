// src/frontend/app/test-gateway/page.tsx
'use client';

import { useState } from 'react';

export default function TestGatewayPage() {
  const [gatewayUrl, setGatewayUrl] = useState(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080');
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const testConnection = async () => {
    setLoading(true);
    setResponse('');
    setError('');
    try {
      const res = await fetch(`${gatewayUrl}/actuator/health`);
      const data = await res.json();
      setResponse(JSON.stringify(data, null, 2));
      if (!res.ok) {
        setError(`HTTP Error: ${res.status} ${res.statusText}`);
      }
    } catch (err: any) {
      setError(`Failed to connect: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'sans-serif' }}>
      <h1>Test Gateway Connectivity</h1>
      <p>Enter the gateway URL and click "Test Connection" to check its health endpoint.</p>

      <div style={{ marginBottom: '15px' }}>
        <label htmlFor="gatewayUrl" style={{ display: 'block', marginBottom: '5px' }}>
          Gateway URL:
        </label>
        <input
          type="text"
          id="gatewayUrl"
          value={gatewayUrl}
          onChange={(e) => setGatewayUrl(e.target.value)}
          style={{ width: '100%', padding: '8px', boxSizing: 'border-box' }}
          disabled={loading}
        />
      </div>

      <button
        onClick={testConnection}
        disabled={loading}
        style={{
          padding: '10px 20px',
          backgroundColor: '#0070f3',
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer',
          opacity: loading ? 0.7 : 1,
        }}
      >
        {loading ? 'Testing...' : 'Test Connection'}
      </button>

      {error && (
        <div style={{ marginTop: '20px', color: 'red', whiteSpace: 'pre-wrap' }}>
          <h2>Error:</h2>
          <p>{error}</p>
        </div>
      )}

      {response && (
        <div style={{ marginTop: '20px', backgroundColor: '#f0f0f0', padding: '15px', borderRadius: '5px' }}>
          <h2>Response:</h2>
          <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>{response}</pre>
        </div>
      )}
    </div>
  );
}
