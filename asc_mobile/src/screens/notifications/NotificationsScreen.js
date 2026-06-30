/**
 * NotificationsScreen — inbox showing all notification history
 * Features: mark all read, tap to open document, pull-to-refresh
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, FlatList,
  TouchableOpacity, RefreshControl,
} from 'react-native';
import client from '../../api/client';
import { EmptyState, LoadingOverlay } from '../../components';
import { useTheme, RADIUS, SHADOW } from '../../utils/theme';

const ACTION_ICON = {
  submitted:'📤', forwarded:'➡️', approved:'✅', rejected:'❌',
  returned:'↩️', completed:'🎉', commented:'💬', in_review:'🔍',
};

export default function NotificationsScreen({ navigation }) {
  const C  = useTheme();
  const [notifs,     setNotifs]     = useState([]);
  const [loading,    setLoading]    = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [unread,     setUnread]     = useState(0);

  const load = useCallback(async () => {
    try {
      const { data } = await client.get('/notifications/mine/');
      const results  = data.results ?? data;
      setNotifs(results);
      setUnread(results.filter(n => n.status === 'pending').length);
    } catch {}
  }, []);

  useEffect(() => { load().finally(() => setLoading(false)); }, []);
  const onRefresh = async () => { setRefreshing(true); await load(); setRefreshing(false); };

  const markAllRead = async () => {
    try { await client.post('/notifications/mark-read/'); setUnread(0); } catch {}
  };

  const s = makeStyles(C);

  const renderItem = ({ item }) => (
    <TouchableOpacity
      style={[s.item, item.status === 'pending' && s.itemUnread]}
      activeOpacity={0.75}
      onPress={() => {
        if (item.document_id) navigation.navigate('DocumentDetail', { id: item.document_id });
      }}
    >
      <View style={s.itemIcon}>
        <Text style={{ fontSize:20 }}>
          {ACTION_ICON[item.data?.event] || '🔔'}
        </Text>
      </View>
      <View style={s.itemBody}>
        <Text style={s.itemTitle} numberOfLines={1}>{item.title}</Text>
        <Text style={s.itemBody2} numberOfLines={2}>{item.body}</Text>
        {item.tracking_number ? (
          <Text style={s.itemTrack}>{item.tracking_number}</Text>
        ) : null}
        <Text style={s.itemTime}>
          {new Date(item.sent_at).toLocaleString('en-PH',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})}
        </Text>
      </View>
      {item.status === 'pending' && <View style={s.unreadDot} />}
    </TouchableOpacity>
  );

  if (loading) return <LoadingOverlay />;

  return (
    <View style={s.screen}>
      {unread > 0 && (
        <TouchableOpacity style={s.markAllBar} onPress={markAllRead}>
          <Text style={s.markAllTxt}>{unread} unread · Tap to mark all read</Text>
        </TouchableOpacity>
      )}
      <FlatList
        data={notifs}
        keyExtractor={n => String(n.id)}
        renderItem={renderItem}
        contentContainerStyle={s.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={C.g800} />}
        showsVerticalScrollIndicator={false}
        ListEmptyComponent={
          <EmptyState icon="🔔" title="No notifications yet" subtitle="You'll see document updates here." />
        }
      />
    </View>
  );
}

const makeStyles = (C) => StyleSheet.create({
  screen:       { flex:1, backgroundColor:C.surf },
  markAllBar:   { backgroundColor:C.g100, padding:12, alignItems:'center', borderBottomWidth:1, borderBottomColor:C.brd2 },
  markAllTxt:   { fontSize:12, fontWeight:'600', color:C.g800 },
  list:         { padding:16, paddingBottom:40, gap:8 },
  item:         { flexDirection:'row', alignItems:'flex-start', gap:12, backgroundColor:C.card, borderRadius:RADIUS.lg, padding:14, borderWidth:1, borderColor:C.brd2, ...SHADOW.sm },
  itemUnread:   { borderLeftWidth:3, borderLeftColor:C.g700 },
  itemIcon:     { width:40, height:40, borderRadius:12, backgroundColor:C.g50, alignItems:'center', justifyContent:'center', flexShrink:0 },
  itemBody:     { flex:1 },
  itemTitle:    { fontSize:14, fontWeight:'600', color:C.ink, letterSpacing:-.2 },
  itemBody2:    { fontSize:12, color:C.ink3, marginTop:3, lineHeight:17 },
  itemTrack:    { fontSize:10, color:C.g700, fontFamily:'monospace', marginTop:4, fontWeight:'600' },
  itemTime:     { fontSize:10, color:C.ink4, marginTop:4 },
  unreadDot:    { width:9, height:9, borderRadius:5, backgroundColor:C.g700, marginTop:5, flexShrink:0 },
});
