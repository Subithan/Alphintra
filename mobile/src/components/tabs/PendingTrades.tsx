// TradeList.tsx
import React from 'react';
import { FlatList, StyleSheet, Text, View } from 'react-native';

type Trade = {
  id: string;
  symbol: string;
  type: string;
  volume: number;
  price: number;
};

type Props = {
  trades: Trade[];
  emptyMessage: string;
};

export const PendingTrades: React.FC<Props> = ({ trades, emptyMessage }) => {
  if (trades.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyText}>{emptyMessage}</Text>
      </View>
    );
  }

  return (
    <FlatList
      data={trades}
      keyExtractor={(item) => item.id}
      renderItem={({ item }) => (
        <View style={styles.tradeItem}>
          <Text style={styles.symbol}>{item.symbol}</Text>
          <Text style={styles.details}>
            {item.type} • {item.volume} lot @ {item.price}
          </Text>
        </View>
      )}
      ItemSeparatorComponent={() => <View style={{ height: 12 }} />}
      contentContainerStyle={styles.listContainer}
    />
  );
};

const styles = StyleSheet.create({
  listContainer: {
    marginTop: 24,
  },
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
});
