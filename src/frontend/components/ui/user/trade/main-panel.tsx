'use client';

import { useState, useEffect, use } from 'react';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Play,
  StopCircle,
  History,
  Edit,
  Trash2,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react';
import type { Position, Bot, Order, Trade } from '@/lib/api/types';

interface TradeOrderData {
  id: number;
  botId: number;
  symbol: string;
  type: string;
  side: string;
  price: number;
  amount: number;
  status: string;
  createdAt: string;
}

const positions: Position[] = [
  {
    asset: 'BTC/USDT',
    type: 'Long',
    quantity: 0.5,
    entryPrice: 65000,
    markPrice: 68123.45,
    pnl: 1561.72,
    pnlPercentage: 4.8,
  },
  {
    asset: 'ETH/USDT',
    type: 'Short',
    quantity: 10,
    entryPrice: 3500,
    markPrice: 3450.5,
    pnl: -495,
    pnlPercentage: -1.41,
  },
  {
    asset: 'SOL/USDT',
    type: 'Long',
    quantity: 100,
    entryPrice: 150,
    markPrice: 162.3,
    pnl: 1230,
    pnlPercentage: 8.2,
  },
];

const activeBots: Bot[] = [
  {
    name: 'BTC Grid Master',
    asset: 'BTC/USDT',
    pnl: 234.56,
    status: 'Running',
    stats: 'Win Rate: 68%',
  },
  {
    name: 'ETH Momentum Rider',
    asset: 'ETH/USDT',
    pnl: -56.12,
    status: 'Stopped',
    stats: 'Trades: 128',
  },
  {
    name: 'SOL Scalper Pro',
    asset: 'SOL/USDT',
    pnl: 102.78,
    status: 'Stopped',
    stats: 'Avg PNL: $1.12',
  },
  {
    name: 'DCA Bot',
    asset: 'ADA/USDT',
    pnl: 12.4,
    status: 'Error',
    stats: 'Last error: API Key Invalid',
  },
];

const generateMockId = () =>
  typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : `order-${Math.random().toString(36).slice(2)}`;

const createMockOrder = (overrides: Partial<Order>): Order => ({
  orderId: overrides.orderId ?? Math.floor(Math.random() * 100000),
  orderUuid: overrides.orderUuid ?? generateMockId(),
  userId: overrides.userId ?? 0,
  accountId: overrides.accountId ?? 0,
  symbol: overrides.symbol ?? '',
  side: overrides.side ?? 'BUY',
  orderType: overrides.orderType ?? 'LIMIT',
  quantity: overrides.quantity ?? '0',
  price: overrides.price ?? '0',
  stopPrice: overrides.stopPrice ?? null,
  timeInForce: overrides.timeInForce ?? 'GTC',
  status: overrides.status ?? 'PENDING',
  filledQuantity: overrides.filledQuantity ?? '0',
  averagePrice: overrides.averagePrice ?? null,
  fee: overrides.fee ?? '0',
  exchange: overrides.exchange ?? 'MockExchange',
  clientOrderId: overrides.clientOrderId ?? null,
  exchangeOrderId: overrides.exchangeOrderId ?? null,
  createdAt: overrides.createdAt ?? new Date().toISOString(),
  updatedAt: overrides.updatedAt ?? new Date().toISOString(),
  expiresAt: overrides.expiresAt ?? null,
});

const mockPendingOrders: Order[] = [
  createMockOrder({
    symbol: 'BTC/USDT',
    orderType: 'LIMIT',
    side: 'SELL',
    price: '68000.0',
    quantity: '0.5',
    status: 'PENDING',
  }),
  createMockOrder({
    symbol: 'ETH/USDT',
    orderType: 'LIMIT',
    side: 'BUY',
    price: '3450.0',
    quantity: '5.0',
    status: 'PENDING',
  }),
];

const ROW_HEIGHT = 40;
const VISIBLE_ROWS = 4;
const MAX_HEIGHT = 240; // 40px * 4 rows

export default function MainPanel() {
  const [pendingOrders, setPendingOrders] = useState<Order[]>(mockPendingOrders);
  const [tradeHistory, setTradeHistory] = useState<TradeOrderData[]>([]);
  const [loading, setLoading] = useState(true); 
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true; 
    const fetchTradeHistory = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch('http://localhost:8008/api/trading/trades?limit=20');
        
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data: TradeOrderData[] = await response.json();
        
        if (mounted) {
          setTradeHistory(data);
        }
      } catch (err) {
        if (mounted) {
          setError("Failed to fetch trade history");
        } 
      } finally {
        setLoading(false);
      }
    };

    fetchTradeHistory();
    
    // Poll for updates every 10 seconds
    const interval = setInterval(fetchTradeHistory, 10000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return ( 
    <Tabs defaultValue="orders" className="w-full max-w-full">
      <TabsList className="flex flex-col flex-nowrap w-full gap-1 sm:grid sm:grid-cols-2 md:grid-cols-4 sm:gap-2 min-w-[300px] p-0">
        <TabsTrigger
          value="orders"
          className="w-full text-xs sm:text-sm py-3 px-2 text-left sm:text-center min-h-[44px] box-border"
        >
          Pending Orders ({pendingOrders.length})
        </TabsTrigger>
        <TabsTrigger
          value="history"
          className="w-full text-xs sm:text-sm py-3 px-2 text-left sm:text-center min-h-[44px] box-border"
        >
          Trade History ({tradeHistory.length})
        </TabsTrigger>
        <TabsTrigger
          value="positions"
          className="w-full text-xs sm:text-sm py-3 px-2 text-left sm:text-center min-h-[44px] box-border"
        >
          Open Positions ({positions.length})
        </TabsTrigger>
        <TabsTrigger
          value="bots"
          className="w-full text-xs sm:text-sm py-3 px-2 text-left sm:text-center min-h-[44px] box-border"
        >
          Active Bots
        </TabsTrigger>
      </TabsList>
      <div className="mt-2 sm:mt-4 rounded-lg border bg-card text-card-foreground shadow-sm">
        <TabsContent value="positions">
          <ScrollArea style={{ maxHeight: MAX_HEIGHT }}>
            {positions.length > 0 ? (
              <PositionsTable data={positions} />
            ) : (
              <p className="p-2 sm:p-4 text-xs sm:text-sm text-muted-foreground">No open positions</p>
            )}
          </ScrollArea>
        </TabsContent>
        <TabsContent value="bots">
          <ScrollArea style={{ maxHeight: MAX_HEIGHT }}>
            {activeBots.length > 0 ? (
              <ActiveBotsTable data={activeBots} />
            ) : (
              <p className="p-2 sm:p-4 text-xs sm:text-sm text-muted-foreground">No active bots</p>
            )}
          </ScrollArea>
        </TabsContent>
        <TabsContent value="orders">
          <ScrollArea style={{ maxHeight: MAX_HEIGHT }}>
            {loading ? (
              <p className="p-2 sm:p-4 text-xs sm:text-sm">Loading orders...</p>
            ) : error ? (
              <p className="p-2 sm:p-4 text-xs sm:text-sm text-red-500">{error}</p>
            ) : pendingOrders.length > 0 ? (
              <PendingOrdersTable data={pendingOrders} />
            ) : (
              <p className="p-2 sm:p-4 text-xs sm:text-sm text-muted-foreground">No pending orders</p>
            )}
          </ScrollArea>
        </TabsContent>
        <TabsContent value="history">
          <ScrollArea style={{ maxHeight: MAX_HEIGHT }}>
            {loading ? (
              <p className="p-2 sm:p-4 text-xs sm:text-sm">Loading trades...</p>
            ) : error ? (
              <p className="p-2 sm:p-4 text-xs sm:text-sm text-red-500">{error}</p>
            ) : tradeHistory.length > 0 ? (
              <TradeHistoryTable data={tradeHistory} />
            ) : (
              <p className="p-2 sm:p-4 text-xs sm:text-sm text-muted-foreground">No trade history</p>
            )}
          </ScrollArea>
        </TabsContent>
      </div>
    </Tabs>
  );
}

const PositionsTable = ({ data }: { data: Position[] }) => (
  <div className="overflow-x-auto" style={{ overflowX: 'auto' }}>
    <Table className="min-w-[600px] overflow-x-auto">
      <TableHeader>
        <TableRow>
          <TableHead className="text-xs sm:text-sm">Asset</TableHead>
          <TableHead className="text-xs sm:text-sm">Type</TableHead>
          <TableHead className="text-xs sm:text-sm text-right">Quantity</TableHead>
          <TableHead className="text-xs sm:text-sm text-right">Entry Price</TableHead>
          <TableHead className="text-xs sm:text-sm text-right">Mark Price</TableHead>
          <TableHead className="text-xs sm:text-sm text-right">PNL (USDT)</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((pos) => (
          <TableRow key={pos.asset} style={{ height: ROW_HEIGHT }}>
            <TableCell className="font-medium text-xs sm:text-sm">{pos.asset}</TableCell>
            <TableCell className="text-xs sm:text-sm">
              <span className={pos.type === 'Long' ? 'text-[#0b9981]' : 'text-red-500'}>
                {pos.type}
              </span>
            </TableCell>
            <TableCell className="text-right text-xs sm:text-sm">{pos.quantity}</TableCell>
            <TableCell className="text-right text-xs sm:text-sm">${pos.entryPrice.toLocaleString()}</TableCell>
            <TableCell className="text-right text-xs sm:text-sm">${pos.markPrice.toLocaleString()}</TableCell>
            <TableCell
              className={`text-right font-semibold text-xs sm:text-sm ${pos.pnl >= 0 ? 'text-[#0b9981]' : 'text-red-500'}`}
            >
              {pos.pnl >= 0 ? '+' : ''}
              {pos.pnl.toFixed(2)} ({pos.pnlPercentage.toFixed(2)}%)
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </div>
);

const ActiveBotsTable = ({ data }: { data: Bot[] }) => (
  <div className="overflow-x-auto">
    <Table className="min-w-[600px]">
      <TableHeader>
        <TableRow>
          <TableHead className="text-xs sm:text-sm">Name</TableHead>
          <TableHead className="text-xs sm:text-sm">Asset</TableHead>
          <TableHead className="text-xs sm:text-sm">Status</TableHead>
          <TableHead className="text-xs sm:text-sm">Performance</TableHead>
          <TableHead className="text-xs sm:text-sm text-right">PNL (USDT)</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((bot) => (
          <TableRow key={bot.name} style={{ height: ROW_HEIGHT }}>
            <TableCell className="font-medium text-xs sm:text-sm">{bot.name}</TableCell>
            <TableCell className="text-xs sm:text-sm">{bot.asset}</TableCell>
            <TableCell className="text-xs sm:text-sm">
              <Badge
                variant={
                  bot.status === 'Running'
                    ? 'default'
                    : bot.status === 'Stopped'
                    ? 'secondary'
                    : 'destructive'
                }
                className={bot.status === 'Running' ? 'bg-[#0b9981]' : ''}
              >
                {bot.status}
              </Badge>
            </TableCell>
            <TableCell className="text-xs sm:text-sm">{bot.stats}</TableCell>
            <TableCell
              className={`text-right font-semibold text-xs sm:text-sm ${bot.pnl >= 0 ? 'text-[#0b9981]' : 'text-red-500'}`}
            >
              {bot.pnl >= 0 ? '+' : ''}
              {bot.pnl.toFixed(2)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </div>
);

const PendingOrdersTable = ({ data }: { data: Order[] }) => (
  <div className="overflow-x-auto">
    <Table className="min-w-[600px]">
      <TableHeader>
        <TableRow>
          <TableHead className="text-xs sm:text-sm">Asset</TableHead>
          <TableHead className="text-xs sm:text-sm">Type</TableHead>
          <TableHead className="text-xs sm:text-sm">Side</TableHead>
          <TableHead className="text-xs sm:text-sm text-right">Price</TableHead>
          <TableHead className="text-xs sm:text-sm text-right">Quantity</TableHead>
          <TableHead className="text-xs sm:text-sm text-right">Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((order, index) => (
          <TableRow key={`${order.symbol}-${index}`} style={{ height: ROW_HEIGHT }}>
            <TableCell className="font-medium text-xs sm:text-sm">{order.symbol}</TableCell>
            <TableCell className="text-xs sm:text-sm">{order.orderType}</TableCell>
            <TableCell className={`text-xs sm:text-sm ${order.side === 'BUY' ? 'text-[#0b9981]' : 'text-red-500'}`}>
              {order.side}
            </TableCell>
            <TableCell className="text-right text-xs sm:text-sm">${parseFloat(order.price).toLocaleString()}</TableCell>
            <TableCell className="text-right text-xs sm:text-sm">{parseFloat(order.quantity).toLocaleString()}</TableCell>
            <TableCell className="text-right text-xs sm:text-sm">
              <Badge variant="outline">{order.status}</Badge>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </div>
);

const TradeHistoryTable = ({ data }: { data: TradeOrderData[] }) => (
  <div className="overflow-x-auto">
    <Table className="min-w-[600px]">
      <TableHeader>
        <TableRow>
          <TableHead className="text-xs sm:text-sm">Time</TableHead>
          <TableHead className="text-xs sm:text-sm">Asset</TableHead>
          <TableHead className="text-xs sm:text-sm">Type</TableHead>
          <TableHead className="text-xs sm:text-sm">Side</TableHead>
          <TableHead className="text-xs sm:text-sm text-right">Price</TableHead>
          <TableHead className="text-xs sm:text-sm text-right">Amount</TableHead>
          <TableHead className="text-xs sm:text-sm text-right">Status</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((trade) => (
          <TableRow key={trade.id} style={{ height: ROW_HEIGHT }}>
            <TableCell className="text-xs sm:text-sm">
              {new Date(trade.createdAt).toLocaleString()}
            </TableCell>
            <TableCell className="font-medium text-xs sm:text-sm">
              {trade.symbol}
            </TableCell>
            <TableCell className="text-xs sm:text-sm">
              <Badge variant="outline" className="text-xs">
                {trade.type}
              </Badge>
            </TableCell>
            <TableCell
              className={`font-medium text-xs sm:text-sm ${
                trade.side === 'BUY' ? 'text-[#0b9981]' : 'text-red-500'
              }`}
            >
              <div className="flex items-center gap-1">
                {trade.side === 'BUY' ? (
                  <ArrowUpRight className="h-3 sm:h-4 w-3 sm:w-4" />
                ) : (
                  <ArrowDownRight className="h-3 sm:h-4 w-3 sm:w-4" />
                )}
                {trade.side}
              </div>
            </TableCell>
            <TableCell className="text-right text-xs sm:text-sm">
              ${trade.price.toFixed(2)}
            </TableCell>
            <TableCell className="text-right text-xs sm:text-sm">
              {trade.amount.toFixed(4)}
            </TableCell>
            <TableCell className="text-right text-xs sm:text-sm">
              <Badge 
                variant={trade.status === 'FILLED' ? 'default' : 'secondary'}
                className={trade.status === 'FILLED' ? 'bg-[#0b9981]' : ''}
              >
                {trade.status}
              </Badge>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </div>
);
