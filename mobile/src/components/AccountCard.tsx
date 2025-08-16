import React from 'react';
import { View, Text, StyleSheet, Pressable  } from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import { ActionButton } from './ActionButton';

export const AccountCard = () => (
  <View style={styles.card}>
    <View style={styles.header}>
      <Text style={styles.name}>John</Text>
      <Icon name="chevron-forward-outline" size={20} color="#aaa" />
    </View>

    <Text style={styles.balance}>41.67 USD</Text>

    <View style={styles.actions}>
      <ActionButton label="Trade" icon="trending-up-outline" color="#FFD700" />
      <ActionButton label="Deposit" icon="download-outline" />
      <ActionButton label="Withdraw" icon="arrow-up-outline" /> 
      <ActionButton label="Details" icon="ellipsis-horizontal-outline" />
    </View>
  </View>
);

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#1C1C1E',
    borderRadius: 12,
    padding: 20,
    marginTop: 24,
  },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  name: { color: '#fff', fontSize: 20 },
  badges: { flexDirection: 'row', marginTop: 8, gap: 8 },
  badge: {
    backgroundColor: '#333',
    color: '#ccc',
    fontSize: 16,
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  balance: { fontSize: 28, color: '#fff', marginTop: 12 },
  actions: { flexDirection: 'row', justifyContent: 'space-around', marginTop: 16 },
});
