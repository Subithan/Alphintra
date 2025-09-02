import { View, Text, StyleSheet } from 'react-native';
import React from 'react';

export default function BottomNav() {
  return (
    <View style={styles.container}>
      {['Home', 'Trade', 'Wallet', 'Settings'].map((item, index) => (
        <Text key={index} style={styles.item}>{item}</Text>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingVertical: 12,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e5e7eb', // gray-100
  },
  item: {
    fontSize: 14,
    color: '#4b5563', // gray-600
  },
});
