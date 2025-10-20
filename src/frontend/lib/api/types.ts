export interface Coin {
    id: string;
    name: string;
    symbol: string;
    image: string;
    current_price: number;
    market_cap: number;
    total_volume: number;
    price_change_percentage_24h: number;
  }

  export interface NewsItem  {
  id: string;
  title: string;
  url: string;
  imageurl: string | null;
  published_on: number;
  source: string;
  body: string | null;
}
export type Portfolio = {
  totalValue: number;
  availableBalance: number;
  pnlDay: number;
  pnlWeek: number;
  pnlMonth: number;
};

export type Bot = {
  id: number;
  userId: number;
  strategyId: number;
  status: 'RUNNING' | 'STOPPED' | 'ERROR';
  symbol: string;
  capitalAllocationPercentage: number;
  startedAt: string;
  stoppedAt?: string | null;
};

export type Position = {
  id: number;
  userId: number;
  botId: number;
  asset: string;
  symbol: string;
  entryPrice: number;
  quantity: number;
  openedAt: string;
  closedAt?: string | null;
  status: 'OPEN' | 'CLOSED';
  pnl?: number | null;
};

export interface Order {
  orderId: number;
  orderUuid: string;
  userId: number;
  accountId: number;
  symbol: string; // Matches backend 'symbol' instead of 'asset'
  side: string;
  orderType: string;
  quantity: string; // BigDecimal as string
  price: string;   // BigDecimal as string
  stopPrice: string | null;
  timeInForce: string;
  status: string;
  filledQuantity: string; // BigDecimal as string
  averagePrice: string | null;
  fee: string; // BigDecimal as string
  exchange: string;
  clientOrderId: string | null;
  exchangeOrderId: string | null;
  createdAt: string; // ISO date
  updatedAt: string; // ISO date
  expiresAt: string | null;
}

export type Trade = {
  asset: string;
  side: 'Buy' | 'Sell';
  price: number;
  quantity: number;
  pnl: number;
  time: string;
};

export type PendingOrder = {
  id: number;
  positionId: number;
  takeProfitPrice: number | null;
  stopLossPrice: number | null;
  quantity: number;
  status: 'PENDING' | 'TRIGGERED' | 'CANCELLED';
  symbol: string;
  createdAt: string;
  triggeredAt?: string | null;
  triggeredType?: string | null;
  cancelledAt?: string | null;
};

export type OrderBookEntry = {
    price: number;
    amount: number;
    total: number;
}

export interface OrderRequest {
  userId: number;
  accountId: number;
  symbol: string;
  side: 'BUY' | 'SELL';
  orderType: 'LIMIT' | 'MARKET' | 'STOP';
  quantity: number;
  price: number;
  timeInForce: 'GTC' | 'FOK' | 'IOC';
}

export interface User {
  name: string;
  email: string;
  phone: string;
  location: string;
  tier: 'premium' | 'standard' | 'basic';
  status: 'active' | 'pending' | 'inactive';
}