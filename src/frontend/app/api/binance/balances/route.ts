import { NextRequest, NextResponse } from 'next/server';

// Mock balance data for testing
const mockBalances = [
  { asset: 'BTC', free: '0.00123456', locked: '0.00000000' },
  { asset: 'ETH', free: '0.15678900', locked: '0.00000000' },
  { asset: 'USDT', free: '1234.56789012', locked: '100.00000000' },
  { asset: 'BNB', free: '5.67890123', locked: '0.00000000' },
  { asset: 'ADA', free: '100.00000000', locked: '0.00000000' },
];

declare global {
  var userConnections: Map<string, any>;
}

export async function GET(request: NextRequest) {
  try {
    const userId = 'current_user'; // Get from authenticated session
    const connection = global.userConnections?.get(userId);
    
    if (!connection?.connected) {
      return NextResponse.json(
        { error: 'Not connected to Binance' },
        { status: 401 }
      );
    }

    // In production, use real Binance API:
    /*
    const ccxt = require('ccxt');
    const exchange = new ccxt.binance({
      apiKey: decryptedApiKey,
      secret: decryptedSecret,
      sandbox: true, // Use testnet
    });
    
    const balanceData = await exchange.fetchBalance();
    const balances = Object.entries(balanceData.info.balances)
      .filter(([_, data]) => parseFloat(data.free) > 0 || parseFloat(data.locked) > 0)
      .map(([asset, data]) => ({
        asset,
        free: data.free,
        locked: data.locked
      }));
    */

    // Return mock data for now
    return NextResponse.json({
      balances: mockBalances,
      lastUpdated: new Date().toISOString()
    });

  } catch (error) {
    console.error('Error fetching balances:', error);
    return NextResponse.json(
      { error: 'Failed to fetch balances' },
      { status: 500 }
    );
  }
}
