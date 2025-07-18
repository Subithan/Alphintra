'use client';

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
import { Button } from '@/components/ui/button';
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
import { ScrollArea } from '@/components/ui/scroll-area';

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

const pendingOrders: Order[] = [
  {
    asset: 'BTC/USDT',
    type: 'Limit',
    side: 'Buy',
    price: 64500,
    quantity: 0.2,
    status: 'Open',
  },
  {
    asset: 'ETH/USDT',
    type: 'Stop Market',
    side: 'Sell',
    price: 3600,
    quantity: 5,
    status: 'Open',
  },
  {
    asset: 'SOL/USDT',
    type: 'Limit',
    side: 'Sell',
    price: 175,
    quantity: 50,
    status: 'Open',
  },
];

const tradeHistory: Trade[] = [
  {
    asset: 'BTC/USDT',
    side: 'Buy',
    price: 68123.45,
    quantity: 0.05,
    pnl: 12.3,
    time: new Date().toISOString(),
  },
  {
    asset: 'ETH/USDT',
    side: 'Sell',
    price: 3400.12,
    quantity: 2,
    pnl: 45.67,
    time: new Date(Date.now() - 5 * 60 * 1000).toISOString(),
  },
  {
    asset: 'SOL/USDT',
    side: 'Buy',
    price: 160.5,
    quantity: 20,
    pnl: -5.5,
    time: new Date(Date.now() - 15 * 60 * 1000).toISOString(),
  },
  {
    asset: 'BTC/USDT',
    side: 'Sell',
    price: 68500,
    quantity: 0.1,
    pnl: 250.1,
    time: new Date(Date.now() - 35 * 60 * 1000).toISOString(),
  },
];

const ROW_HEIGHT = 40;
const VISIBLE_ROWS = 4;
const MAX_HEIGHT = 240; // 40px * 4 rows

export default function MainPanel() {
  return (
    <Tabs defaultValue="positions" className="w-full">
      <TabsList className="grid w-full grid-cols-2 md:grid-cols-4">
        <TabsTrigger value="positions">Open Positions ({positions.length})</TabsTrigger>
        <TabsTrigger value="bots">Active Bots</TabsTrigger>
        <TabsTrigger value="orders">Pending Orders ({pendingOrders.length})</TabsTrigger>
        <TabsTrigger value="history">Trade History ({tradeHistory.length})</TabsTrigger>
      </TabsList>
      <div className="mt-4 rounded-lg border bg-card text-card-foreground shadow-sm">
        <TabsContent value="positions">
          <ScrollArea style={{ maxHeight: MAX_HEIGHT }}>
            <PositionsTable data={positions} />
          </ScrollArea>
        </TabsContent>
        <TabsContent value="bots">
          <ScrollArea style={{ maxHeight: MAX_HEIGHT }}>
            <ActiveBotsTable data={activeBots} />
          </ScrollArea>
        </TabsContent>
        <TabsContent value="orders">
          <ScrollArea style={{ maxHeight: MAX_HEIGHT }}>
            <PendingOrdersTable data={pendingOrders} />
          </ScrollArea>
        </TabsContent>
        <TabsContent value="history">
          <ScrollArea style={{ maxHeight: MAX_HEIGHT }}>
            <TradeHistoryTable data={tradeHistory} />
          </ScrollArea>
        </TabsContent>
      </div>
    </Tabs>
  )
}


const PositionsTable = ({ data }: { data: Position[] }) => (
  <Table>
    <TableHeader>
      <TableRow>
        <TableHead>Asset</TableHead>
        <TableHead>Type</TableHead>
        <TableHead className="text-right">Quantity</TableHead>
        <TableHead className="text-right">Entry Price</TableHead>
        <TableHead className="text-right">Mark Price</TableHead>
        <TableHead className="text-right">PNL (USDT)</TableHead>
      </TableRow>
    </TableHeader>
    <TableBody>
      {data.map((pos) => (
        <TableRow key={pos.asset} style={{ height: ROW_HEIGHT }}>
          <TableCell className="font-medium">{pos.asset}</TableCell>
          <TableCell>
            <span className={pos.type === 'Long' ? 'text-[#0b9981]' : 'text-red-500'}>
              {pos.type}
            </span>
          </TableCell>
          <TableCell className="text-right">{pos.quantity}</TableCell>
          <TableCell className="text-right">${pos.entryPrice.toLocaleString()}</TableCell>
          <TableCell className="text-right">${pos.markPrice.toLocaleString()}</TableCell>
          <TableCell
            className={`text-right font-semibold ${pos.pnl >= 0 ? 'text-[#0b9981]' : 'text-red-500'}`}
          >
            {pos.pnl >= 0 ? '+' : ''}
            {pos.pnl.toFixed(2)} ({pos.pnlPercentage.toFixed(2)}%)
          </TableCell>
        </TableRow>
      ))}
    </TableBody>
  </Table>
);

const ActiveBotsTable = ({ data }: { data: Bot[] }) => (
  <Table>
    <TableHeader>
      <TableRow>
        <TableHead>Name</TableHead>
        <TableHead>Asset</TableHead>
        <TableHead>Status</TableHead>
        <TableHead>Performance</TableHead>
        <TableHead className="text-right">PNL (USDT)</TableHead>
      </TableRow>
    </TableHeader>
    <TableBody>
      {data.map((bot) => (
        <TableRow key={bot.name} style={{ height: ROW_HEIGHT }}>
          <TableCell className="font-medium">{bot.name}</TableCell>
          <TableCell>{bot.asset}</TableCell>
          <TableCell>
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
          <TableCell>{bot.stats}</TableCell>
          <TableCell
            className={`text-right font-semibold ${bot.pnl >= 0 ? 'text-[#0b9981]' : 'text-red-500'}`}
          >
            {bot.pnl >= 0 ? '+' : ''}
            {bot.pnl.toFixed(2)}
          </TableCell>
        </TableRow>
      ))}
    </TableBody>
  </Table>
);

const PendingOrdersTable = ({ data }: { data: Order[] }) => (
  <Table>
    <TableHeader>
      <TableRow>
        <TableHead>Asset</TableHead>
        <TableHead>Type</TableHead>
        <TableHead>Side</TableHead>
        <TableHead className="text-right">Price</TableHead>
        <TableHead className="text-right">Quantity</TableHead>
        <TableHead className="text-right">Status</TableHead>
      </TableRow>
    </TableHeader>
    <TableBody>
      {data.map((order, index) => (
        <TableRow key={`${order.asset}-${index}`} style={{ height: ROW_HEIGHT }}>
          <TableCell className="font-medium">{order.asset}</TableCell>
          <TableCell>{order.type}</TableCell>
          <TableCell className={order.side === 'Buy' ? 'text-[#0b9981]' : 'text-red-500'}>
            {order.side}
          </TableCell>
          <TableCell className="text-right">${order.price.toLocaleString()}</TableCell>
          <TableCell className="text-right">{order.quantity}</TableCell>
          <TableCell className="text-right">
            <Badge variant="outline">{order.status}</Badge>
          </TableCell>
        </TableRow>
      ))}
    </TableBody>
  </Table>
);

const TradeHistoryTable = ({ data }: { data: Trade[] }) => (
  <Table>
    <TableHeader>
      <TableRow>
        <TableHead>Time</TableHead>
        <TableHead>Asset</TableHead>
        <TableHead>Side</TableHead>
        <TableHead className="text-right">Price</TableHead>
        <TableHead className="text-right">Quantity</TableHead>
        <TableHead className="text-right">PNL</TableHead>
      </TableRow>
    </TableHeader>
    <TableBody>
      {data.map((trade, index) => (
        <TableRow key={`${trade.asset}-${index}`} style={{ height: ROW_HEIGHT }}>
          <TableCell>{new Date(trade.time).toLocaleTimeString()}</TableCell>
          <TableCell className="font-medium">{trade.asset}</TableCell>
          <TableCell
            className={`font-medium ${trade.side === 'Buy' ? 'text-[#0b9981]' : 'text-red-500'}`}
          >
            <div className="flex items-center gap-1">
              {trade.side === 'Buy' ? (
                <ArrowUpRight className="h-4 w-4" />
              ) : (
                <ArrowDownRight className="h-4 w-4" />
              )}
              {trade.side}
            </div>
          </TableCell>
          <TableCell className="text-right">${trade.price.toLocaleString()}</TableCell>
          <TableCell className="text-right">{trade.quantity}</TableCell>
          <TableCell className={`text-right ${trade.pnl >= 0 ? 'text-[#0b9981]' : 'text-red-500'}`}>
            {trade.pnl.toFixed(2)}
          </TableCell>
        </TableRow>
      ))}
    </TableBody>
  </Table>
);
