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

export type Order = {
  asset: string;
  type: 'Limit' | 'Market' | 'Stop Market';
  side: 'Buy' | 'Sell';
  price: number;
  quantity: number;
  status: 'Open' | 'Filled' | 'Cancelled';
};

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
