
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { OrderRequest } from '@/lib/api/types';
import axios from 'axios';

export default function OrderModal({ onOrderPlaced }: { onOrderPlaced: () => void }) {
  const [open, setOpen] = useState(false);
  const [formData, setFormData] = useState<OrderRequest>({
    userId: 1,
    accountId: 1,
    symbol: 'BTC/USD',
    side: 'BUY',
    orderType: 'Limit',
    quantity: 0.1,
    price: 50000.0,
    timeInForce: 'GTC',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await axios.post('http://localhost:8008/api/orders', formData);
      setOpen(false);
      onOrderPlaced(); // Refresh parent component data
    } catch (error) {
      console.error('Error placing order:', error);
      // Handle error (e.g., show toast notification)
    }
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button className='bg-yellow-500 hover:bg-yellow-500 hover:scale-105'>Place New Order</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Place Order</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <Label htmlFor="symbol">Symbol</Label>
            <Input
              id="symbol"
              value={formData.symbol}
              onChange={(e) => setFormData({ ...formData, symbol: e.target.value })}
            />
          </div>
          <div>
            <Label htmlFor="side">Side</Label>
            <Select
              value={formData.side}
              onValueChange={(value) => setFormData({ ...formData, side: value as 'BUY' | 'SELL' })}
            >
              <SelectTrigger id="side">
                <SelectValue placeholder="Select side" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="BUY">Buy</SelectItem>
                <SelectItem value="SELL">Sell</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="orderType">Order Type</Label>
            <Select
              value={formData.orderType}
              onValueChange={(value) => setFormData({ ...formData, orderType: value as 'Limit' | 'Market' | 'Stop'
               })}
            >
              <SelectTrigger id="orderType">
                <SelectValue placeholder="Select order type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Limit">Limit</SelectItem>
                <SelectItem value="Stop">Stop</SelectItem>
                <SelectItem value="Market">Market</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label htmlFor="quantity">Quantity</Label>
            <Input
              id="quantity"
              type="number"
              step="0.1"
              value={formData.quantity}
              onChange={(e) => setFormData({ ...formData, quantity: Number(e.target.value) })}
            />
          </div>
          <div>
            <Label htmlFor="price">Price</Label>
            <Input
              id="price"
              type="number"
              step="0.01"
              value={formData.price}
              onChange={(e) => setFormData({ ...formData, price: Number(e.target.value) })}
            />
          </div>
          <div>
            <Label htmlFor="timeInForce">Time in Force</Label>
            <Select
              value={formData.timeInForce}
              onValueChange={(value) => setFormData({ ...formData, timeInForce: value as 'GTC' | 'FOK' | 'IOC' })}
            >
              <SelectTrigger id="timeInForce">
                <SelectValue placeholder="Select time in force" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="GTC">GTC (Good Till Cancelled)</SelectItem>
                <SelectItem value="FOK">FOK (Fill or Kill)</SelectItem>
                <SelectItem value="IOC">IOC (Immediate or Cancel)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <Button type="submit" className='bg-yellow-500 hover:bg-yellow-500 hover:scale-105'>Submit</Button>
        </form>
      </DialogContent>
    </Dialog>
  );
}