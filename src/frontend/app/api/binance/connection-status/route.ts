import { NextRequest, NextResponse } from 'next/server';

// Same storage reference as connect route
declare global {
  var userConnections: Map<string, any>;
}

if (!global.userConnections) {
  global.userConnections = new Map();
}

export async function GET(request: NextRequest) {
  try {
    const userId = 'current_user'; // Get from authenticated session
    const connection = global.userConnections.get(userId);
    
    return NextResponse.json({
      connected: connection?.connected || false,
      connectedAt: connection?.connectedAt || null
    });

  } catch (error) {
    console.error('Error checking connection status:', error);
    return NextResponse.json(
      { error: 'Failed to check connection status' },
      { status: 500 }
    );
  }
}
