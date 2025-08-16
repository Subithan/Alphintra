import React, { useState } from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';

interface TabBarProps {
  onTabChange?: (tab: 'Open' | 'Pending') => void;
}

export const TabBar: React.FC<TabBarProps> = ({ onTabChange }) => {
  const [activeTab, setActiveTab] = useState<'Open' | 'Pending'>('Open');

  const handleTabPress = (tab: 'Open' | 'Pending') => {
    setActiveTab(tab);
    onTabChange?.(tab);
  };

  return (
    <View style={styles.tabs}>
      {['Open', 'Pending'].map((tab) => (
        <Pressable key={tab} onPress={() => handleTabPress(tab as 'Open' | 'Pending')}>
          <Text style={[styles.tab, activeTab === tab && styles.active]}>
            {tab}
          </Text>
        </Pressable>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  tabs: {
    flexDirection: 'row',
    marginTop: 24,
    borderBottomColor: '#333',
    borderBottomWidth: 1,
  },
  tab: {
    marginRight: 24,
    paddingVertical: 8,
    color: '#aaa',
    fontSize: 16,
  },
  active: {
    color: '#fff',
    borderBottomWidth: 2,
    borderBottomColor: '#fff',
  },
});
