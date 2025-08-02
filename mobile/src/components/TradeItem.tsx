import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export const TradeItem = () => (
  <View style={styles.card}>
    <Text style={styles.text}>🇺🇸 XAU/USD - Trade</Text>
  </View>
);

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#222',
    padding: 16,
    borderRadius: 8,
    marginVertical: 12,
  },
  text: { color: '#fff', fontSize: 16 },
});
