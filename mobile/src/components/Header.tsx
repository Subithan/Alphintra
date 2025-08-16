import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';

export const Header = () => (
  <View style={styles.header}>
    <Text style={styles.title}>Accounts</Text>
    <View style={styles.icons}>
      <Icon name="notifications-outline" size={24} color="#fff" style={styles.icon} />
    </View>
  </View>
);

const styles = StyleSheet.create({
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  title: { color: '#fff', fontSize: 24, fontWeight: '600' },
  icons: { flexDirection: 'row' },
  icon: { marginLeft: 16 },
});
