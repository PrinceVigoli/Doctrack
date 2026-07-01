import React from 'react';
import { View, Text, ActivityIndicator, StyleSheet, TouchableOpacity } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../utils/theme';

import LoginScreen          from '../screens/auth/LoginScreen';
import DashboardScreen      from '../screens/dashboard/DashboardScreen';
import DocumentListScreen   from '../screens/documents/DocumentListScreen';
import DocumentDetailScreen from '../screens/documents/DocumentDetailScreen';
import SubmitDocumentScreen from '../screens/documents/SubmitDocumentScreen';
import ScannerScreen        from '../screens/scanner/ScannerScreen';
import QRScannerScreen      from '../screens/qr/QRScannerScreen';
import NotificationsScreen  from '../screens/notifications/NotificationsScreen';
import AnalyticsScreen      from '../screens/analytics/AnalyticsScreen';
import ProfileScreen        from '../screens/profile/ProfileScreen';

const Stack = createNativeStackNavigator();
const Tab   = createBottomTabNavigator();

// Vector icons instead of raw emoji — some Android fonts don't have full
// color-emoji coverage and silently fall back to broken glyphs (📁/🔔 were
// rendering as stray "||" / "<" characters on some devices).
const TAB_ICON = {
  Dashboard:     { focused: 'grid',            unfocused: 'grid-outline' },
  Documents:     { focused: 'folder',          unfocused: 'folder-outline' },
  Scanner:       { focused: 'camera',          unfocused: 'camera-outline' },
  Notifications: { focused: 'notifications',   unfocused: 'notifications-outline' },
  Profile:       { focused: 'person-circle',   unfocused: 'person-circle-outline' },
};

function TabIcon({ name, focused, color }) {
  const icon = TAB_ICON[name];
  return (
    <Ionicons
      name={focused ? icon.focused : icon.unfocused}
      size={name === 'Scanner' ? 22 : 24}
      color={color}
    />
  );
}

function MainTabs() {
  const C = useTheme();
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color }) => <TabIcon name={route.name} focused={focused} color={color} />,
        tabBarActiveTintColor:   C.g800,
        tabBarInactiveTintColor: C.ink4,
        tabBarStyle: { backgroundColor:C.card, borderTopColor:C.brd2, paddingBottom:14, paddingTop:8, height:66 },
        tabBarLabelStyle:    { fontSize:10, fontWeight:'600' },
        headerStyle:         { backgroundColor:C.g900 },
        headerTintColor:     '#fff',
        headerTitleStyle:    { fontWeight:'700', letterSpacing:-.3, fontSize:17 },
        headerShadowVisible: false,
      })}
    >
      <Tab.Screen name="Dashboard" component={DashboardScreen} />
      <Tab.Screen name="Documents" component={DocumentListScreen} />
      <Tab.Screen name="Scanner"   component={ScannerScreen} options={{ title:'Scan Document' }} />
      <Tab.Screen name="Notifications" component={NotificationsScreen} options={{ title:'Notifications' }} />
      <Tab.Screen name="Profile"   component={ProfileScreen} />
    </Tab.Navigator>
  );
}

function AuthStack() {
  return <Stack.Navigator screenOptions={{ headerShown:false }}><Stack.Screen name="Login" component={LoginScreen} /></Stack.Navigator>;
}

function AppStack() {
  const C = useTheme();
  return (
    <Stack.Navigator screenOptions={{
      headerStyle:{ backgroundColor:C.g900 }, headerTintColor:'#fff',
      headerTitleStyle:{ fontWeight:'700', letterSpacing:-.3, fontSize:17 }, headerShadowVisible:false,
    }}>
      <Stack.Screen name="Main"           component={MainTabs}            options={{ headerShown:false }} />
      <Stack.Screen name="DocumentDetail" component={DocumentDetailScreen} options={{ title:'Document' }} />
      <Stack.Screen name="SubmitDocument" component={SubmitDocumentScreen} options={{ title:'Submit Document' }} />
      <Stack.Screen name="DocumentList"   component={DocumentListScreen}   options={{ title:'Documents' }} />
      <Stack.Screen name="QRScanner"      component={QRScannerScreen}      options={{ title:'Scan QR Code' }} />
      <Stack.Screen name="Analytics"      component={AnalyticsScreen}      options={{ title:'Analytics' }} />
    </Stack.Navigator>
  );
}

export default function AppNavigator() {
  const { user, loading } = useAuth();
  const C = useTheme();
  if (loading) {
    return (
      <View style={[s.loading,{backgroundColor:C.surf}]}>
        <ActivityIndicator size="large" color={C.g800} />
        <Text style={[s.loadingTxt,{color:C.ink3}]}>Loading ASC DocTrack...</Text>
      </View>
    );
  }
  return <NavigationContainer>{user ? <AppStack /> : <AuthStack />}</NavigationContainer>;
}

const s = StyleSheet.create({
  loading:    { flex:1, alignItems:'center', justifyContent:'center' },
  loadingTxt: { fontSize:13, marginTop:14 },
});
