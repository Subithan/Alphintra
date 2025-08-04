import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';

interface Props {
  label: string;
  icon: string;
  color?: string;
}

export const ActionButton = ({ label, icon, color = '#444' }: Props) => (
  <TouchableOpacity style={styles.btn}>
    <View style={[styles.iconWrap, { backgroundColor: color }]}>
      <Icon name={icon} size={18} color="#000" />
    </View>
    <Text style={styles.label}>{label}</Text>
  </TouchableOpacity>
);

const styles = StyleSheet.create({
  btn: { alignItems: 'center' },
  iconWrap: {
    padding: 10,
    borderRadius: 50,
    backgroundColor: '#FFD700',
    marginBottom: 4,
    fontWeight: 'bold', 
  },
  label: { color: '#ccc', fontSize: 12,  fontWeight: 'bold',  },
});
