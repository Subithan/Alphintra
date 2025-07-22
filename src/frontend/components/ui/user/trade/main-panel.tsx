
'use client';

import { useState, useEffect } from 'react';
import axios from 'axios';
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
    pnl: 495,
    pnlPercentage: 1.41,
  },
  {
    asset: 'SOL/USDT',
    type: 'Long',
    quantity: 100,
    entryPrice: 150,
    markPrice: 162.3,
    pnl: -1230,
    pnlPercentage: -8.2,
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

const ROW_HEIGHT = 40;
const VISIBLE_ROWS = 4;
const MAX_HEIGHT = 240; // 40px * 4 rows

export default function MainPanel() {
  const [pendingOrders, setPendingOrders] = useState<Order[]>([]);
  const [tradeHistory, setTradeHistory] = useState<Trade[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [ordRes, tradeRes] = await Promise.all([
        axios.get<Order[]>('http://localhost:8008/api/orders?status=OPEN'),
        axios.get<Trade[]>('http://localhost:8008/api/trades'),
      ]);
      setPendingOrders(ordRes.data);
      setTradeHistory(tradeRes.data);
    } catch (err: any) {
      setError('Network error. Please check API or server connection.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

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
          <TableRow key={`${order.asset}-${index}`} style={{ height: ROW_HEIGHT }}>
            <TableCell className="font-medium text-xs sm:text-sm">{order.asset}</TableCell>
            <TableCell className="text-xs sm:text-sm">{order.type}</TableCell>
            <TableCell className={`text-xs sm:text-sm ${order.side === 'Buy' ? 'text-[#0b9981]' : 'text-red-500'}`}>
              {order.side}
            </TableCell>
            <TableCell className="text-right text-xs sm:text-sm">${order.price.toLocaleString()}</TableCell>
            <TableCell className="text-right text-xs sm:text-sm">{order.quantity}</TableCell>
            <TableCell className="text-right text-xs sm:text-sm">
              <Badge variant="outline">{order.status}</Badge>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </div>
);

const TradeHistoryTable = ({ data }: { data: Trade[] }) => (
  <div className="overflow-x-auto">
    <Table className="min-w-[600px]">
      <TableHeader>
        <TableRow>
          <TableHead className="text-xs sm:text-sm">Time</TableHead>
          <TableHead className="text-xs sm:text-sm">Asset</TableHead>
          <TableHead className="text-xs sm:text-sm">Side</TableHead>
          <TableHead className="text-xs sm:text-sm text-right">Price</TableHead>
          <TableHead className="text-xs sm:text-sm text-right">Quantity</TableHead>
          <TableHead className="text-xs sm:text-sm text-right">PNL</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((trade, index) => (
          <TableRow key={`${trade.asset}-${index}`} style={{ height: ROW_HEIGHT }}>
            <TableCell className="text-xs sm:text-sm">{new Date(trade.time).toLocaleTimeString()}</TableCell>
            <TableCell className="font-medium text-xs sm:text-sm">{trade.asset}</TableCell>
            <TableCell
              className={`font-medium text-xs sm:text-sm ${trade.side === 'Buy' ? 'text-[#0b9981]' : 'text-red-500'}`}
            >
              <div className="flex items-center gap-1">
                {trade.side === 'Buy' ? (
                  <ArrowUpRight className="h-3 sm:h-4 w-3 sm:w-4" />
                ) : (
                  <ArrowDownRight className="h-3 sm:h-4 w-3 sm:w-4" />
                )}
                {trade.side}
              </div>
            </TableCell>
            <TableCell className="text-right text-xs sm:text-sm">${trade.price.toLocaleString()}</TableCell>
            <TableCell className="text-right text-xs sm:text-sm">{trade.quantity}</TableCell>
            <TableCell
              className={`text-right text-xs sm:text-sm ${trade.pnl >= 0 ? 'text-[#0b9981]' : 'text-red-500'}`}
            >
              {trade.pnl.toFixed(2)}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </div>
);
