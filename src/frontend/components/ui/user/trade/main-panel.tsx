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
import type { Order, Trade, PendingOrder } from '@/lib/api/types';
import { getToken, getUserId } from '@/lib/auth';
import { buildGatewayUrl } from '@/lib/config/gateway';
import { tradingApi, type Position, type TradingBot } from '@/lib/api/trading-api';

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

const ROW_HEIGHT = 40;
const VISIBLE_ROWS = 4;
const MAX_HEIGHT = 240; // 40px * 4 rows

export default function MainPanel() {
  const [pendingOrders, setPendingOrders] = useState<PendingOrder[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [activeBots, setActiveBots] = useState<TradingBot[]>([]);
  const [tradeHistory, setTradeHistory] = useState<TradeOrderData[]>([]);
  const [loading, setLoading] = useState(true); 
  const [error, setError] = useState<string | null>(null);
  const [userId, setUserId] = useState<number | null>(null);

  useEffect(() => {
    // Get user ID from JWT token
    const id = getUserId();
    setUserId(id);
    console.log('[Trading UI] User ID from JWT:', id);
  }, []);

  useEffect(() => {
    let mounted = true; 
    
    const fetchAllData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Get user ID from JWT
        const currentUserId = getUserId();
        console.log('[Trading UI] Fetching data for user ID:', currentUserId);

        // Fetch all data in parallel - filtered by user ID
        const [trades, orders, pos, bots] = await Promise.all([
          tradingApi.getTradeHistory(20),
          currentUserId ? tradingApi.getPendingOrders(currentUserId, 'PENDING') : tradingApi.getPendingOrders(undefined, 'PENDING'),
          currentUserId ? tradingApi.getPositions(currentUserId, 'OPEN') : tradingApi.getPositions(undefined, 'OPEN'),
          currentUserId ? tradingApi.getAllBots(currentUserId) : tradingApi.getAllBots()
        ]);
        
        if (mounted) {
          setTradeHistory(trades);
          setPendingOrders(orders);
          setPositions(pos);
          setActiveBots(bots);
          
          console.log('[Trading UI] Data loaded:', {
            trades: trades.length,
            orders: orders.length,
            positions: pos.length,
            bots: bots.length
          });
        }
      } catch (err) {
        if (mounted) {
          console.error('[Trading UI] Failed to fetch trading data', err);
          setError("Failed to fetch trading data");
        } 
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    fetchAllData();
    
    // Poll for updates every 10 seconds
    const interval = setInterval(fetchAllData, 10000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="w-full">
      {/* User Info Display */}
      
      
      <Tabs defaultValue="bots" className="w-full max-w-full">
        <TabsList className="flex flex-col flex-nowrap w-full gap-1 sm:grid sm:grid-cols-2 md:grid-cols-4 sm:gap-2 min-w-[300px] p-0">
        <TabsTrigger
          value="bots"
          className="w-full text-xs sm:text-sm py-3 px-2 text-left sm:text-center min-h-[44px] box-border"
        >
          Bots ({activeBots.length})
        </TabsTrigger>
        <TabsTrigger
          value="positions"
          className="w-full text-xs sm:text-sm py-3 px-2 text-left sm:text-center min-h-[44px] box-border"
        >
          Open Positions ({positions.length})
        </TabsTrigger>
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
          Trade History 
        </TabsTrigger>
      </TabsList>
      <div className="mt-2 sm:mt-4 rounded-lg border bg-card text-card-foreground shadow-sm">
        <TabsContent value="bots">
          <ScrollArea style={{ maxHeight: MAX_HEIGHT }}>
            {activeBots.length > 0 ? (
              <ActiveBotsTable data={activeBots} />
            ) : (
              <p className="p-2 sm:p-4 text-xs sm:text-sm text-muted-foreground">No active bots</p>
            )}
          </ScrollArea>
        </TabsContent>
        <TabsContent value="positions">
          <ScrollArea style={{ maxHeight: MAX_HEIGHT }}>
            {positions.length > 0 ? (
              <PositionsTable data={positions} />
            ) : (
              <p className="p-2 sm:p-4 text-xs sm:text-sm text-muted-foreground">No open positions</p>
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
            <p className="p-2 sm:p-4 text-xs sm:text-sm text-muted-foreground">No trade history</p>
          </ScrollArea>
        </TabsContent>
      </div>
    </Tabs>
    </div>
  );
}

const PositionsTable = ({ data }: { data: Position[] }) => (
  <div className="overflow-x-auto" style={{ overflowX: 'auto' }}>
    <Table className="min-w-[600px] overflow-x-auto">
      <TableHeader>
        <TableRow>
          <TableHead className="text-xs sm:text-sm">Symbol</TableHead>
          <TableHead className="text-xs sm:text-sm">Status</TableHead>
          <TableHead className="text-xs sm:text-sm text-right">Quantity</TableHead>
          <TableHead className="text-xs sm:text-sm text-right">Entry Price</TableHead>
          {/* <TableHead className="text-xs sm:text-sm text-right">Opened At</TableHead> */}
          <TableHead className="text-xs sm:text-sm text-right">PNL</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((pos) => (
          <TableRow key={pos.id} style={{ height: ROW_HEIGHT }}>
            <TableCell className="font-medium text-xs sm:text-sm">{pos.symbol}</TableCell>
            <TableCell className="text-xs sm:text-sm">
              <Badge variant={pos.status === 'OPEN' ? 'default' : 'secondary'}>
                {pos.status}
              </Badge>
            </TableCell>
            <TableCell className="text-right text-xs sm:text-sm">{pos.quantity}</TableCell>
            <TableCell className="text-right text-xs sm:text-sm">${pos.entryPrice.toLocaleString()}</TableCell>
            {/* <TableCell className="text-right text-xs sm:text-sm">
              {new Date(pos.createdAt).toLocaleString()}
            </TableCell> */}
            <TableCell
              className={`text-right font-semibold text-xs sm:text-sm ${(pos.pnl || 0) >= 0 ? 'text-[#0b9981]' : 'text-red-500'}`}
            >
              {pos.pnl ? (
                <>
                  {pos.pnl >= 0 ? '+' : ''}
                  {pos.pnl.toFixed(2)}
                </>
              ) : (
                'N/A'
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </div>
);

const ActiveBotsTable = ({ data }: { data: TradingBot[] }) => (
  <div className="overflow-x-auto">
    <Table className="min-w-[600px]">
      <TableHeader>
        <TableRow>
          <TableHead className="text-xs sm:text-sm">Bot ID</TableHead>
          <TableHead className="text-xs sm:text-sm">Symbol</TableHead>
          <TableHead className="text-xs sm:text-sm">Status</TableHead>
          <TableHead className="text-xs sm:text-sm text-right">Capital %</TableHead>
          {/* <TableHead className="text-xs sm:text-sm text-right">Started At</TableHead> */}
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((bot) => (
          <TableRow key={bot.id} style={{ height: ROW_HEIGHT }}>
            <TableCell className="font-medium text-xs sm:text-sm">#{bot.id}</TableCell>
            <TableCell className="text-xs sm:text-sm">{bot.symbol}</TableCell>
            <TableCell className="text-xs sm:text-sm">
              <Badge
                variant={
                  bot.status === 'RUNNING'
                    ? 'default'
                    : bot.status === 'STOPPED'
                    ? 'secondary'
                    : 'destructive'
                }
                className={bot.status === 'RUNNING' ? 'bg-[#0b9981]' : ''}
              >
                {bot.status}
              </Badge>
            </TableCell>
            <TableCell className="text-right text-xs sm:text-sm">{bot.capitalAllocationPercentage}%</TableCell>
            {/* <TableCell className="text-right text-xs sm:text-sm">
              {new Date(bot.createdAt).toLocaleString()}
            </TableCell> */}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </div>
);

const PendingOrdersTable = ({ data }: { data: PendingOrder[] }) => (
  <div className="overflow-x-auto">
    <Table className="min-w-[600px]">
      <TableHeader>
        <TableRow>
          <TableHead className="text-xs sm:text-sm">Symbol</TableHead>
          <TableHead className="text-xs sm:text-sm text-right">Take Profit</TableHead>
          <TableHead className="text-xs sm:text-sm text-right">Stop Loss</TableHead>
          <TableHead className="text-xs sm:text-sm text-right">Quantity</TableHead>
          <TableHead className="text-xs sm:text-sm text-right">Status</TableHead>
          {/* <TableHead className="text-xs sm:text-sm text-right">Created At</TableHead> */}
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.map((order) => (
          <TableRow key={order.id} style={{ height: ROW_HEIGHT }}>
            <TableCell className="font-medium text-xs sm:text-sm">{order.symbol}</TableCell>
            <TableCell className="text-right text-xs sm:text-sm text-[#0b9981]">
              {order.takeProfitPrice ? `$${order.takeProfitPrice.toFixed(2)}` : 'N/A'}
            </TableCell>
            <TableCell className="text-right text-xs sm:text-sm text-red-500">
              {order.stopLossPrice ? `$${order.stopLossPrice.toFixed(2)}` : 'N/A'}
            </TableCell>
            <TableCell className="text-right text-xs sm:text-sm">{order.quantity}</TableCell>
            <TableCell className="text-right text-xs sm:text-sm">
              <Badge variant={order.status === 'PENDING' ? 'outline' : order.status === 'TRIGGERED' ? 'default' : 'secondary'}>
                {order.status}
              </Badge>
            </TableCell>
            {/* <TableCell className="text-right text-xs sm:text-sm">
              {new Date(order.createdAt).toLocaleString()}
            </TableCell> */}
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
          {/* <TableHead className="text-xs sm:text-sm">Time</TableHead> */}
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
            {/* <TableCell className="text-xs sm:text-sm">
              {new Date(trade.createdAt).toLocaleString()}
            </TableCell> */}
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
