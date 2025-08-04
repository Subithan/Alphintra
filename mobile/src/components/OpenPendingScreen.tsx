import React, { useState } from 'react';
import { View, StyleSheet } from 'react-native';
import { TabBar } from '../components/TabBar';
import { OpenPositions } from '../components/tabs/OpenPositions';
import { PendingTrades } from '../components/tabs/PendingTrades';

export const OpenPendingScreen = () => {
  const [tab, setTab] = useState<'Open' | 'Pending'>('Open');

  return (
    <View style={styles.container}>
      <TabBar onTabChange={setTab} />
      {tab === 'Open' ? <OpenPositions /> : <PendingTrades />}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
    padding: 16,
  },
});
