'use client';

import { useEffect, useState } from 'react';
import { tradingApi, type UserBalance } from '@/lib/api/trading-api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Wallet } from 'lucide-react';

export default function UserBalances() {
  const [balances, setBalances] = useState<UserBalance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchBalances = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await tradingApi.getUserBalances();
        setBalances(data);
      } catch (err: any) {
        console.error('Error fetching user balances:', err);
        setError(err.message || 'Failed to load balances');
      } finally {
        setLoading(false);
      }
    };

    fetchBalances();
  }, []);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wallet className="w-5 h-5" />
            Portfolio Balance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground">Loading balances...</div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wallet className="w-5 h-5" />
            Portfolio Balance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-destructive">{error}</div>
        </CardContent>
      </Card>
    );
  }

  if (balances.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Wallet className="w-5 h-5" />
            Portfolio Balance
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-muted-foreground">No balances found</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {balances.map((balance) => (
        <Card key={balance.id}>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {balance.asset}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-1">
              <div className="text-2xl font-bold">
                {Number(balance.free).toFixed(8)}
              </div>
              {balance.locked > 0 && (
                <div className="text-xs text-muted-foreground">
                  Locked: {Number(balance.locked).toFixed(8)}
                </div>
              )}
              <div className="text-xs text-muted-foreground">
                Total: {(Number(balance.free) + Number(balance.locked)).toFixed(8)}
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
