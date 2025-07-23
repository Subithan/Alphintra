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
  name: string;
  asset: string;
  pnl: number;
  status: 'Running' | 'Stopped' | 'Error';
  stats: string;
};

export type Position = {
  asset: string;
  type: 'Long' | 'Short';
  quantity: number;
  entryPrice: number;
  markPrice: number;
  pnl: number;
  pnlPercentage: number;
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
  orderType: 'Limit' | 'Market' | 'Stop';
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