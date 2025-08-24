import { NextRequest, NextResponse } from 'next/server';

declare global {
  var userConnections: Map<string, any>;
}

export async function POST(request: NextRequest) {
  try {
    const userId = 'current_user'; // Get from authenticated session
    
    if (global.userConnections) {
      global.userConnections.delete(userId);
    }

    return NextResponse.json({
      message: 'Successfully disconnected from Binance',
      connected: false
    });

  } catch (error) {
    console.error('Error disconnecting:', error);
    return NextResponse.json(
      { error: 'Failed to disconnect' },
      { status: 500 }
    );
  }
}
