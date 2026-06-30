/**
 * AnalyticsScreen — turnaround time, approval rates, bottlenecks
 * Visible only to superadmin / records_officer (enforced via navigation)
 */
import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, RefreshControl } from 'react-native';
import { dashAPI } from '../../api/services';
import { LoadingOverlay, MiniBar } from '../../components';
import { useTheme, RADIUS, SHADOW } from '../../utils/theme';

export default function AnalyticsScreen() {
  const C = useTheme();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = async () => {
    setError('');
    try {
      const { data: d } = await dashAPI.summary();
      setData(d);
    } catch (e) {
      setError(e?.response?.data?.detail || 'Could not load analytics. Pull down to retry.');
    }
  };
  useEffect(() => { load().finally(() => setLoading(false)); }, []);
  const onRefresh = async () => { setRefreshing(true); await load(); setRefreshing(false); };

  if (loading) return <LoadingOverlay />;

  if (error) {
    const s = makeStyles(C);
    return (
      <ScrollView style={s.screen} contentContainerStyle={s.content}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={C.g800} />}>
        <Text style={s.pageTitle}>Analytics</Text>
        <View style={s.warnCard}>
          <Text style={s.warnTxt}>⚠️ {error}</Text>
        </View>
      </ScrollView>
    );
  }

  const byS = data?.by_status || {};
  const total = data?.total || 0;
  const approvalRate = total ? Math.round(((byS.approved||0)+(byS.completed||0)) / total * 100) : 0;
  const rejectionRate = total ? Math.round((byS.rejected||0) / total * 100) : 0;
  const office = data?.office_workload || [];
  const maxOff = Math.max(...office.map(o=>o.count), 1);

  const s = makeStyles(C);
  return (
    <ScrollView style={s.screen} contentContainerStyle={s.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={C.g800} />}>

      <Text style={s.pageTitle}>Analytics</Text>
      <Text style={s.pageSub}>Office-wide document performance metrics</Text>

      {/* Big number cards */}
      <View style={s.bigRow}>
        <View style={[s.bigCard, { borderTopColor:C.g700 }]}>
          <Text style={[s.bigVal,{color:C.g700}]}>{data?.avg_processing_hrs!=null?data.avg_processing_hrs:'—'}h</Text>
          <Text style={s.bigLbl}>Avg turnaround</Text>
        </View>
        <View style={[s.bigCard, { borderTopColor:C.blue }]}>
          <Text style={[s.bigVal,{color:C.blue}]}>{approvalRate}%</Text>
          <Text style={s.bigLbl}>Approval rate</Text>
        </View>
      </View>
      <View style={s.bigRow}>
        <View style={[s.bigCard, { borderTopColor:C.red }]}>
          <Text style={[s.bigVal,{color:C.red}]}>{rejectionRate}%</Text>
          <Text style={s.bigLbl}>Rejection rate</Text>
        </View>
        <View style={[s.bigCard, { borderTopColor:C.amber }]}>
          <Text style={[s.bigVal,{color:C.amber}]}>{byS.pending||0}</Text>
          <Text style={s.bigLbl}>Awaiting action</Text>
        </View>
      </View>

      {/* Office bottleneck chart */}
      <Text style={s.sTitle}>Office workload — bottleneck indicator</Text>
      <View style={s.card}>
        {office.length === 0
          ? <Text style={s.emptyTxt}>No data yet.</Text>
          : office.slice(0,8).map((o,i) => {
              const isBottleneck = o.count / maxOff > 0.7;
              return (
                <View key={i} style={s.bnRow}>
                  <View style={{ flexDirection:'row', alignItems:'center', flex:1 }}>
                    {isBottleneck && <Text style={s.bnFlag}>🔴</Text>}
                    <MiniBar label={o.office} value={o.count} max={maxOff} color={isBottleneck?C.red:C.g600} />
                  </View>
                </View>
              );
            })
        }
      </View>
      {office.some(o => o.count/maxOff > 0.7) && (
        <View style={s.warnCard}>
          <Text style={s.warnTxt}>⚠️ Offices marked 🔴 are holding significantly more documents than average — possible bottleneck.</Text>
        </View>
      )}

      {/* Status distribution */}
      <Text style={s.sTitle}>Status distribution</Text>
      <View style={s.card}>
        {Object.entries(byS).map(([key, count], i) => (
          <MiniBar key={i} label={key.replace('_',' ')} value={count} max={total||1} color={C.g600} />
        ))}
      </View>

    </ScrollView>
  );
}

const makeStyles = (C) => StyleSheet.create({
  screen:   { flex:1, backgroundColor:C.surf },
  content:  { padding:20, paddingBottom:50 },
  pageTitle:{ fontSize:22, fontWeight:'700', color:C.ink, letterSpacing:-.5, marginBottom:4 },
  pageSub:  { fontSize:13, color:C.ink3, marginBottom:20 },
  bigRow:   { flexDirection:'row', gap:10, marginBottom:10 },
  bigCard:  { flex:1, backgroundColor:C.card, borderRadius:RADIUS.lg, padding:16, borderTopWidth:3, borderWidth:1, borderColor:C.brd2, ...SHADOW.sm },
  bigVal:   { fontSize:28, fontWeight:'700', letterSpacing:-.5 },
  bigLbl:   { fontSize:11, color:C.ink3, marginTop:4, fontWeight:'500' },
  sTitle:   { fontSize:14, fontWeight:'600', color:C.ink2, marginTop:20, marginBottom:10, letterSpacing:-.2 },
  card:     { backgroundColor:C.card, borderRadius:RADIUS.lg, padding:14, borderWidth:1, borderColor:C.brd2, gap:10, ...SHADOW.sm },
  emptyTxt: { fontSize:13, color:C.ink4 },
  bnRow:    { },
  bnFlag:   { fontSize:10, marginRight:4 },
  warnCard: { backgroundColor:C.redBg, borderRadius:RADIUS.md, padding:12, marginTop:10, borderWidth:1, borderColor:'#FECACA' },
  warnTxt:  { fontSize:12, color:C.redDk, lineHeight:18 },
});
