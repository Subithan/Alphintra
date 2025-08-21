import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import Icon from 'react-native-vector-icons/Ionicons';
import AccountsScreen from '../screens/Home';

// Placeholder screens
const TradeScreen = () => null;
const InsightsScreen = () => null;
const PerformanceScreen = () => null;
const ProfileScreen = () => null;

const Tab = createBottomTabNavigator();

const BottomTabs = () => {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarStyle: {
          backgroundColor: '#0D0D0D',
          borderTopColor: '#1c1c1c',
        },
        tabBarLabelStyle: {
          fontSize: 12,
          color: '#ccc',
        },
        tabBarIcon: ({ focused, color, size }) => {
          let iconName = 'ellipse';

          switch (route.name) {
            case 'Accounts':
              iconName = 'grid-outline';
              break;
            case 'Trade':
              iconName = 'bar-chart-outline';
              break;
            case 'Insights':
              iconName = 'globe-outline';
              break;
            case 'Profile':
              iconName = 'person-outline';
              break;
          }

          return <Icon name={iconName} size={20} color={focused ? '#fff' : '#aaa'} />;
        },
        tabBarActiveTintColor: '#fff',
        tabBarInactiveTintColor: '#aaa',
      })}
    >
      <Tab.Screen name="Accounts" component={AccountsScreen} />
      <Tab.Screen name="Trade" component={TradeScreen} />
      <Tab.Screen name="Insights" component={InsightsScreen} />
      <Tab.Screen name="Profile" component={ProfileScreen} />
    </Tab.Navigator>
  );
};

export default BottomTabs;
