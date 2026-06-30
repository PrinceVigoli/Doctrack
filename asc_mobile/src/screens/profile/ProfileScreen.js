import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, Switch } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '../../context/AuthContext';
import { Card, Button } from '../../components';
import { useTheme, RADIUS, SHADOW } from '../../utils/theme';
import { useBiometric } from '../../hooks/useBiometric';

const ROLE_LABEL = {
  superadmin:      '🛡 Super Admin',
  records_officer: '📋 Records Officer',
  program_chair:   '🎓 Program Chair',
  faculty:         '👨‍🏫 Faculty',
};

export default function ProfileScreen() {
  const { user, logout } = useAuth();
  const C   = useTheme();
  const nav = useNavigation();
  const bio = useBiometric();
  const [bioType, setBioType] = useState('Biometrics');

  useEffect(() => { bio.getType().then(setBioType); }, []);

  const handleLogout = () => {
    Alert.alert('Sign out', 'Are you sure you want to sign out?', [
      { text:'Cancel', style:'cancel' },
      { text:'Sign out', style:'destructive', onPress: async () => { await bio.clearCreds(); logout(); } },
    ]);
  };

  const toggleBio = async (val) => {
    if (!val) await bio.clearCreds();
    else Alert.alert('Enable on next login', 'Sign in with your password once more to enable biometric login.');
  };

  if (!user) return null;
  const isAdmin = ['superadmin','records_officer'].includes(user.role);
  const s = makeStyles(C);

  return (
    <ScrollView style={s.screen} contentContainerStyle={s.content}>
      <View style={s.hero}>
        <View style={s.avatar}><Text style={s.avatarTxt}>{(user.first_name?.[0]||user.username[0]).toUpperCase()}</Text></View>
        <Text style={s.name}>{user.first_name} {user.last_name}</Text>
        <Text style={s.username}>@{user.username}</Text>
        <View style={s.roleBadge}><Text style={s.roleTxt}>{ROLE_LABEL[user.role]||user.role}</Text></View>
      </View>

      <Card style={s.card}>
        <InfoRow C={C} label="Email" value={user.email||'—'} />
        <InfoRow C={C} label="Phone" value={user.phone||'—'} />
        <InfoRow C={C} label="Office" value={user.office?.name||'—'} />
        <InfoRow C={C} label="Department" value={user.office?.code||'—'} last />
      </Card>

      {/* Admin-only shortcut */}
      {isAdmin && (
        <TouchableOpacity style={s.adminCard} onPress={() => nav.navigate('Analytics')}>
          <Text style={s.adminTitle}>📈 Analytics dashboard</Text>
          <Text style={s.adminArrow}>→</Text>
        </TouchableOpacity>
      )}

      <TouchableOpacity style={s.adminCard} onPress={() => nav.navigate('QRScanner')}>
        <Text style={s.adminTitle}>📷 Scan QR to find document</Text>
        <Text style={s.adminArrow}>→</Text>
      </TouchableOpacity>

      {/* Settings */}
      <Card style={s.card}>
        <Text style={s.cardTitle}>Settings</Text>
        {bio.supported && bio.enrolled && (
          <View style={s.settingRow}>
            <View style={{ flex:1 }}>
              <Text style={s.settingLabel}>{bioType} login</Text>
              <Text style={s.settingSub}>Sign in faster with {bioType}</Text>
            </View>
            <Switch value={bio.enabled} onValueChange={toggleBio}
              trackColor={{ false:C.brd, true:C.g600 }} thumbColor="#fff" />
          </View>
        )}
        <View style={[s.settingRow, { borderBottomWidth:0 }]}>
          <View style={{ flex:1 }}>
            <Text style={s.settingLabel}>Dark mode</Text>
            <Text style={s.settingSub}>Follows your device system setting</Text>
          </View>
        </View>
      </Card>

      <Card style={s.card}>
        <Text style={s.cardTitle}>About ASC DocTrack</Text>
        <Text style={s.about}>
          AI-Assisted Smart Document Tracking System{'\n'}
          Apayao State College – Luna Campus{'\n\n'}
          Version 1.0.0 · Research & Development{'\n'}
          ASC-DRD-IQF-02-Rev_01
        </Text>
      </Card>

      <Button title="Sign out" variant="danger" onPress={handleLogout} style={{ marginTop:8 }} />
    </ScrollView>
  );
}

function InfoRow({ C, label, value, last }) {
  const s = makeStyles(C);
  return (
    <View style={[s.infoRow, !last && s.infoRowBorder]}>
      <Text style={s.infoLabel}>{label}</Text>
      <Text style={s.infoValue}>{value}</Text>
    </View>
  );
}

const makeStyles = (C) => StyleSheet.create({
  screen:       { flex:1, backgroundColor:C.surf },
  content:      { padding:20, paddingBottom:50 },
  hero:         { alignItems:'center', marginBottom:24 },
  avatar:       { width:80, height:80, borderRadius:40, backgroundColor:C.g800, alignItems:'center', justifyContent:'center', marginBottom:12 },
  avatarTxt:    { fontSize:32, fontWeight:'700', color:'#fff' },
  name:         { fontSize:20, fontWeight:'700', color:C.ink },
  username:     { fontSize:14, color:C.ink3, marginTop:2 },
  roleBadge:    { marginTop:8, backgroundColor:C.g50, paddingHorizontal:14, paddingVertical:5, borderRadius:RADIUS.pill },
  roleTxt:      { fontSize:13, fontWeight:'600', color:C.g800 },
  card:         { marginBottom:14 },
  cardTitle:    { fontSize:14, fontWeight:'700', color:C.ink, marginBottom:10 },
  about:        { fontSize:13, color:C.ink3, lineHeight:20 },
  infoRow:      { flexDirection:'row', justifyContent:'space-between', alignItems:'center', paddingVertical:12 },
  infoRowBorder:{ borderBottomWidth:1, borderBottomColor:C.brd2 },
  infoLabel:    { fontSize:13, color:C.ink4, fontWeight:'500' },
  infoValue:    { fontSize:14, color:C.ink, fontWeight:'600', maxWidth:'60%', textAlign:'right' },
  adminCard:    { flexDirection:'row', alignItems:'center', justifyContent:'space-between', backgroundColor:C.g50, borderRadius:RADIUS.lg, padding:16, marginBottom:14, borderWidth:1, borderColor:C.g200 },
  adminTitle:   { fontSize:14, fontWeight:'700', color:C.g800 },
  adminArrow:   { fontSize:18, color:C.g700 },
  settingRow:   { flexDirection:'row', alignItems:'center', paddingVertical:12, borderBottomWidth:1, borderBottomColor:C.brd2 },
  settingLabel: { fontSize:14, fontWeight:'600', color:C.ink },
  settingSub:   { fontSize:11, color:C.ink3, marginTop:2 },
});
