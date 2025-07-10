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