/**
 * DashboardScreen — role-aware, pull-to-refresh, links to Analytics for admins
 */
import React, { useState, useEffect, useCallback } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl, TouchableOpacity } from 'react-native';
import { useAuth } from '../../context/AuthContext';
import { dashAPI } from '../../api/services';
import { KPITile, AiBadge, MiniBar, EmptyState, LoadingOverlay } from '../../components';
import { useTheme, RADIUS, SHADOW } from '../../utils/theme';

const ACTION_ICON = {
  submitted: '📤',
  approved:  '✅',
  rejected:  '❌',
  forwarded: '➡️',
  completed: '🎉',
  returned:  '↩️',
};

const ACTION_COLOR = {
  submitted: '#2563EB',
  approved:  '#2D6A4F',
  rejected:  '#DC2626',
  forwarded: '#D97706',
  completed: '#40916C',
  returned:  '#D97706',
};

export default function DashboardScreen({ navigation }) {
  const { user } = useAuth();
  const C = useTheme();
  const [data, setData] = useState(null);
  const [activity, setActivity] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [loadError, setLoadError] = useState('');

  const STATUS_META = [
    { key:'pending',   label:'Pending',  color:C.amber },
    { key:'in_review', label:'Review',   color:C.blue  },
    { key:'approved',  label:'Approved', color:C.g700  },
    { key:'completed', label:'Done',     color:C.ink3  },
  ];

  const load = useCallback(async () => {
    setLoadError('');
    try {
      const [sum, act] = await Promise.all([dashAPI.summary(), dashAPI.activity()]);
      setData(sum.data);
      setActivity(act.data.slice(0, 5));
    } catch (e) {
      setLoadError(e?.response?.data?.detail || 'Could not load dashboard. Pull down to retry.');
    }
  }, []);

  useEffect(() => { load().finally(() => setLoading(false)); }, []);
  const onRefresh = async () => { setRefreshing(true); await load(); setRefreshing(false); };

  if (loading) return <LoadingOverlay />;

  const byS   = data?.by_status || {};
  const total = data?.total || 0;
  const labels = data?.by_ai_label || [];
  const maxL   = Math.max(...labels.map(l => l.count), 1);

  const isAdmin = ['superadmin','records_officer'].includes(user?.role);
  const s = makeStyles(C);

  return (
    <ScrollView style={s.screen} contentContainerStyle={s.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={C.g800} />}
      showsVerticalScrollIndicator={false}
    >
      <View style={s.hero}>
        <View style={s.heroTop}>
          <View style={{ flex:1 }}>
            <Text style={s.greet}>Good day,</Text>
            <Text style={s.name}>{user?.first_name || user?.username} 👋</Text>
            <Text style={s.office}>{user?.office?.name || 'ASC Luna Campus'} · {user?.role?.replace('_',' ')}</Text>
          </View>
          <View style={s.avatar}><Text style={s.avatarTxt}>{(user?.first_name?.[0]||user?.username?.[0]||'U').toUpperCase()}</Text></View>
        </View>
        <View style={s.kpiRow}>
          <KPITile value={total} label="Total docs" highlight />
          <KPITile value={byS.pending||0} label="Pending" />
          <KPITile value={data?.avg_processing_hrs!=null?data.avg_processing_hrs+'h':'—'} label="Avg time" />
        </View>
      </View>

      {/* Error banner */}
      {loadError ? (
        <View style={s.errorBanner}>
          <Text style={s.errorTxt}>⚠️ {loadError}</Text>
        </View>
      ) : null}

      {/* Analytics shortcut for admins */}
      {isAdmin && (
        <TouchableOpacity style={s.analyticsCard} onPress={() => navigation.navigate('Analytics')} activeOpacity={0.8}>
          <View style={{ flex:1 }}>
            <Text style={s.analyticsTitle}>📈 View detailed analytics</Text>
            <Text style={s.analyticsSub}>Turnaround time, approval rates, bottlenecks</Text>
          </View>
          <Text style={s.analyticsArrow}>→</Text>
        </TouchableOpacity>
      )}

      <View style={s.section}>
        <Text style={s.sTitle}>Status overview</Text>
        <View style={s.chipRow}>
          {STATUS_META.map(sm => (
            <TouchableOpacity key={sm.key} style={s.chip} onPress={() => navigation.navigate('DocumentList',{status:sm.key})} activeOpacity={0.7}>
              <Text style={[s.chipNum,{color:sm.color}]}>{byS[sm.key]||0}</Text>
              <Text style={s.chipLbl}>{sm.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      {labels.length > 0 && (
        <View style={s.section}>
          <Text style={s.sTitle}>AI document types</Text>
          <View style={s.card}>
            {labels.slice(0,5).map((l,i) => (
              <MiniBar key={i} label={l.ai_label} value={l.count} max={maxL} color={i<3?C.g600:C.amber} />
            ))}
          </View>
        </View>
      )}

      <View style={s.section}>
        <View style={{ flexDirection:'row', justifyContent:'space-between', alignItems:'center', marginBottom:10 }}>
          <Text style={s.sTitle}>Recent activity</Text>
          <TouchableOpacity onPress={() => navigation.navigate('DocumentList')}><Text style={s.seeAll}>See all</Text></TouchableOpacity>
        </View>
        {activity.length === 0
          ? <EmptyState icon="📋" title="No activity yet" />
          : activity.map((log,i) => {
              const actionColor = ACTION_COLOR[log.action] || C.ink3;
              return (
                <TouchableOpacity key={i} style={s.actItem} onPress={() => navigation.navigate('DocumentDetail',{id:log.document_id})} activeOpacity={0.7}>
                  <View style={s.actIcon}>
                    <Text style={{ fontSize:16 }}>{ACTION_ICON[log.action] || '📄'}</Text>
                  </View>
                  <View style={{ flex:1 }}>
                    <Text style={s.actTitle} numberOfLines={1}>{log.doc_title}</Text>
                    <Text style={s.actMeta}>{log.action.replace('_',' ').toUpperCase()} · {log.actor}</Text>
                  </View>
                  <View style={[s.actBadge, { backgroundColor: actionColor + '18', borderColor: actionColor + '40' }]}>
                    <Text style={[s.actBadgeTxt, { color: actionColor }]}>
                      {log.action.replace('_',' ')}
                    </Text>
                  </View>
                </TouchableOpacity>
              );
            })
        }
      </View>
    </ScrollView>
  );
}

const makeStyles = (C) => StyleSheet.create({
  screen:    { flex:1, backgroundColor:C.surf },
  content:   { paddingBottom:40 },
  hero:      { backgroundColor:C.g900, paddingHorizontal:20, paddingTop:16, paddingBottom:22 },
  heroTop:   { flexDirection:'row', alignItems:'flex-start', marginBottom:18 },
  greet:     { fontSize:12, color:'rgba(255,255,255,.45)', marginBottom:3 },
  name:      { fontSize:22, fontWeight:'700', color:'#fff', letterSpacing:-.5, lineHeight:26 },
  office:    { fontSize:11, color:'rgba(255,255,255,.4)', marginTop:4, textTransform:'capitalize' },
  avatar:    { width:42, height:42, borderRadius:21, backgroundColor:C.g700, alignItems:'center', justifyContent:'center', borderWidth:2, borderColor:'rgba(255,255,255,.15)' },
  avatarTxt: { fontSize:16, fontWeight:'700', color:'#fff' },
  kpiRow:    { flexDirection:'row', gap:8 },
  errorBanner: { backgroundColor:'#FEF2F2', borderBottomWidth:1, borderBottomColor:'#FECACA', padding:12, paddingHorizontal:18 },
  errorTxt:    { fontSize:12, fontWeight:'600', color:'#991B1B' },
  analyticsCard: { flexDirection:'row', alignItems:'center', backgroundColor:C.g50, marginHorizontal:18, marginTop:16, padding:16, borderRadius:RADIUS.lg, borderWidth:1, borderColor:C.g200 },
  analyticsTitle:{ fontSize:14, fontWeight:'700', color:C.g800 },
  analyticsSub:  { fontSize:11, color:C.g700, marginTop:2 },
  analyticsArrow:{ fontSize:18, color:C.g700 },
  section:   { paddingHorizontal:18, paddingTop:20 },
  sTitle:    { fontSize:14, fontWeight:'600', color:C.ink2, marginBottom:10, letterSpacing:-.2 },
  seeAll:    { fontSize:12, color:C.g700, fontWeight:'600' },
  chipRow:   { flexDirection:'row', gap:8 },
  chip:      { flex:1, backgroundColor:C.card, borderRadius:14, padding:12, alignItems:'center', gap:3, borderWidth:1, borderColor:C.brd2, ...SHADOW.sm },
  chipNum:   { fontSize:22, fontWeight:'700', lineHeight:26, letterSpacing:-.5 },
  chipLbl:   { fontSize:9, color:C.ink3, fontWeight:'500' },
  card:      { backgroundColor:C.card, borderRadius:RADIUS.lg, padding:14, borderWidth:1, borderColor:C.brd2, gap:10, ...SHADOW.sm },
  actItem:   { flexDirection:'row', alignItems:'center', gap:12, backgroundColor:C.card, borderRadius:16, padding:12, marginBottom:8, borderWidth:1, borderColor:C.brd2, ...SHADOW.sm },
  actIcon:   { width:36, height:36, borderRadius:10, backgroundColor:C.g50, alignItems:'center', justifyContent:'center' },
  actTitle:  { fontSize:13, fontWeight:'600', color:C.ink },
  actMeta:   { fontSize:10, color:C.ink3, marginTop:2 },
  actBadge:  { paddingHorizontal:9, paddingVertical:3, borderRadius:99, borderWidth:1 },
  actBadgeTxt:{ fontSize:10, fontWeight:'600', textTransform:'capitalize' },
});
