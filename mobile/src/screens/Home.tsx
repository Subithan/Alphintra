import React, { useState } from 'react';
import { FlatList, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Header } from '../components/Header';
import { AccountCard } from '../components/AccountCard';
import { TabBar } from '../components/TabBar';

// Sample pending trades data
const pendingTrades = [
  { id: '1', symbol: 'EUR/USD', type: 'Buy', volume: 1.5, price: 1.1023 },
  { id: '2', symbol: 'XAU/USD', type: 'Sell', volume: 0.5, price: 1942.67 },
];

// Empty open positions data for demo
const openPositions: typeof pendingTrades = [];

const renderTradeItem = ({ item }: { item: typeof pendingTrades[0] }) => (
  <View style={styles.tradeItem}>
    <Text style={styles.symbol}>{item.symbol}</Text>
    <Text style={styles.details}>
      {item.type} • {item.volume} lot @ {item.price}
    </Text>
  </View>
);

const Home = () => {
  const [tab, setTab] = useState<'Open' | 'Pending'>('Open');

  const data = tab === 'Open' ? openPositions : pendingTrades;
  const isEmpty = data.length === 0;

  return (
    <SafeAreaView style={styles.safeArea}>
      <FlatList
        data={data}
        renderItem={renderTradeItem}
        keyExtractor={(item) => item.id}
        ListHeaderComponent={
          <>
            <Header />
            <AccountCard />
            <TabBar onTabChange={setTab} />
            {isEmpty && (
              <>
                <View style={styles.emptyContainer}>
                  <Text style={styles.emptyText}>
                    {tab === 'Open' ? 'No open positions' : 'No pending trades'}
                  </Text>
                </View>

                <View style={styles.tradeCard}>
                  <Text style={styles.tradeTitle}>🇺🇸 XAU/USD - Trade</Text>
                </View>
              </>
            )}
          </>
        }
        contentContainerStyle={styles.container}
        ItemSeparatorComponent={() => <View style={{ height: 12 }} />}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#0D0D0D' },
  container: { backgroundColor: '#0D0D0D', padding: 16 },
  tradeItem: {
    backgroundColor: '#1C1C1E',
    borderRadius: 12,
    padding: 16,
  },
  symbol: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#fff',
  },
  details: {
    marginTop: 4,
    color: '#ccc',
    fontSize: 14,
  },
  emptyContainer: {
    marginTop: 24,
    alignItems: 'center',
  },
  emptyText: {
    color: '#888',
    fontSize: 16,
  },
  tradeCard: {
    backgroundColor: '#222',
    padding: 16,
    borderRadius: 8,
    marginVertical: 12,
    alignItems: 'center',
  },
  tradeTitle: {
    color: '#fff',
    fontSize: 16,
  },
});

export default Home;
