import { View, Text } from 'react-native';
import React from 'react';

export default function BottomNav() {
  return (
    <View className="flex-row justify-around py-3 bg-white border-t border-gray-100">
      {['Home', 'Trade', 'Wallet', 'Settings'].map((item, index) => (
        <Text key={index} className="text-sm text-gray-600">{item}</Text>
      ))}
    </View>
  );
}
