import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

export const OpenPositions = () => {
  return (
    <View style={styles.container}>
      <Text style={styles.message}>No open positions</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginTop: 24,
    alignItems: 'center',
  },
  message: {
    color: '#888',
    fontSize: 16,
    textAlign: 'center',
    marginTop: 40,
  },
});

