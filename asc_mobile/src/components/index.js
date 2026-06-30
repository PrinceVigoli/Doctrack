import React from 'react';
import {
  View, Text, TouchableOpacity, ActivityIndicator,
  StyleSheet, TextInput,
} from 'react-native';
import { COLORS, RADIUS, SHADOW, STATUS } from '../utils/theme';

/* ── Button ─────────────────────────────────────────── */
export function Button({ title, onPress, loading, variant='primary', style, disabled, icon }) {
  const styles = btnStyles(variant);
  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={loading || disabled}
      activeOpacity={0.75}
      style={[styles.btn, style, (loading||disabled) && { opacity:.55 }]}
    >
      {loading
        ? <ActivityIndicator color={variant==='outline' ? COLORS.g800 : '#fff'} size="small" />
        : <>
            {icon && <Text style={styles.icon}>{icon}</Text>}
            <Text style={styles.label}>{title}</Text>
          </>
      }
    </TouchableOpacity>
  );
}
const btnStyles = (v) => StyleSheet.create({
  btn: {
    height: 48, borderRadius: RADIUS.md,
    alignItems:'center', justifyContent:'center',
    flexDirection:'row', gap: 8, paddingHorizontal: 20,
    backgroundColor:
      v==='primary'  ? COLORS.g900 :
      v==='outline'  ? 'transparent' :
      v==='danger'   ? COLORS.red :
      v==='ghost'    ? COLORS.surf : COLORS.amber,
    borderWidth:  v==='outline' ? 1.5 : 0,
    borderColor:  v==='outline' ? COLORS.g800 : 'transparent',
  },
  label: {
    fontSize:14, fontWeight:'600', letterSpacing:-.1,
    color: v==='outline' ? COLORS.g800 : '#fff',
  },
  icon: { fontSize:16, color: v==='outline' ? COLORS.g800 : '#fff' },
});

/* ── Input ──────────────────────────────────────────── */
export function Input({ label, error, hint, style, ...props }) {
  return (
    <View style={{ marginBottom:16 }}>
      {label && <Text style={s.lbl}>{label}</Text>}
      <TextInput
        style={[s.input, error && { borderColor: COLORS.red }, style]}
        placeholderTextColor={COLORS.ink4}
        {...props}
      />
      {error  && <Text style={s.err}>{error}</Text>}
      {hint   && <Text style={s.hint}>{hint}</Text>}
    </View>
  );
}

/* ── Card ───────────────────────────────────────────── */
export function Card({ children, style, padding=16 }) {
  return (
    <View style={[s.card, { padding }, style]}>{children}</View>
  );
}

/* ── StatusBadge ────────────────────────────────────── */
export function StatusBadge({ status }) {
  const meta = STATUS[status] || { bg:'#F3F4F6', text:'#6B7280', label: status };
  return (
    <View style={[s.badge, { backgroundColor: meta.bg }]}>
      <Text style={[s.badgeTxt, { color: meta.text }]}>
        {meta.label}
      </Text>
    </View>
  );
}

/* ── SectionHeader ──────────────────────────────────── */
export function SectionHeader({ title, action, onAction }) {
  return (
    <View style={s.secHead}>
      <Text style={s.secTitle}>{title}</Text>
      {action && (
        <TouchableOpacity onPress={onAction}>
          <Text style={s.secAction}>{action}</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

/* ── EmptyState ─────────────────────────────────────── */
export function EmptyState({ icon='📄', title, subtitle }) {
  return (
    <View style={s.empty}>
      <Text style={s.emptyIcon}>{icon}</Text>
      <Text style={s.emptyTitle}>{title}</Text>
      {subtitle && <Text style={s.emptySub}>{subtitle}</Text>}
    </View>
  );
}

/* ── LoadingOverlay ─────────────────────────────────── */
export function LoadingOverlay() {
  return (
    <View style={s.overlay}>
      <ActivityIndicator color={COLORS.g800} size="large" />
    </View>
  );
}

/* ── StatTile ───────────────────────────────────────── */
export function StatTile({ label, value, color, style }) {
  return (
    <View style={[s.statTile, { borderLeftColor: color||COLORS.g700 }, style]}>
      <Text style={[s.statVal, { color: color||COLORS.g800 }]}>{value??'—'}</Text>
      <Text style={s.statLbl}>{label}</Text>
    </View>
  );
}

/* ── KPIStrip tile (for dashboard hero) ─────────────── */
export function KPITile({ value, label, highlight }) {
  return (
    <View style={[s.kpi, highlight && s.kpiHi]}>
      <Text style={s.kpiVal}>{value}</Text>
      <Text style={s.kpiLbl}>{label}</Text>
    </View>
  );
}

/* ── AiBadge ────────────────────────────────────────── */
export function AiBadge({ label, confidence }) {
  const pct = Math.round((confidence||0)*100);
  return (
    <View style={s.aiBadge}>
      <Text style={s.aiBadgeTxt}>🤖 {label}{pct>0?` · ${pct}%`:''}</Text>
    </View>
  );
}

/* ── Mini bar row ───────────────────────────────────── */
export function MiniBar({ label, value, max, color }) {
  const pct = max ? Math.round((value/max)*100) : 0;
  return (
    <View style={s.mbRow}>
      <Text style={s.mbLbl} numberOfLines={1}>{label}</Text>
      <View style={s.mbTrack}>
        <View style={[s.mbFill, { width:`${pct}%`, backgroundColor: color||COLORS.g600 }]} />
      </View>
      <Text style={s.mbN}>{value}</Text>
    </View>
  );
}

const s = StyleSheet.create({
  lbl:        { fontSize:12, fontWeight:'500', color:COLORS.ink2, marginBottom:6, letterSpacing:-.1 },
  input:      { height:44, borderWidth:1.5, borderColor:COLORS.brd, borderRadius:RADIUS.md, paddingHorizontal:14, fontSize:14, color:COLORS.ink, backgroundColor:COLORS.surf },
  err:        { fontSize:11, color:COLORS.red, marginTop:4 },
  hint:       { fontSize:11, color:COLORS.ink3, marginTop:4 },
  card:       { backgroundColor:COLORS.card, borderRadius:RADIUS.lg, borderWidth:1, borderColor:COLORS.brd2, ...SHADOW.sm },
  badge:      { paddingHorizontal:10, paddingVertical:4, borderRadius:RADIUS.pill, alignSelf:'flex-start' },
  badgeTxt:   { fontSize:11, fontWeight:'600', letterSpacing:.02 },
  secHead:    { flexDirection:'row', justifyContent:'space-between', alignItems:'center', marginBottom:10 },
  secTitle:   { fontSize:14, fontWeight:'600', color:COLORS.ink2, letterSpacing:-.2 },
  secAction:  { fontSize:12, color:COLORS.g700, fontWeight:'600' },
  empty:      { alignItems:'center', paddingVertical:40 },
  emptyIcon:  { fontSize:40, marginBottom:12 },
  emptyTitle: { fontSize:16, fontWeight:'600', color:COLORS.ink3 },
  emptySub:   { fontSize:13, color:COLORS.ink4, marginTop:6, textAlign:'center' },
  overlay:    { flex:1, alignItems:'center', justifyContent:'center', backgroundColor:COLORS.surf },
  statTile:   { backgroundColor:COLORS.card, borderRadius:RADIUS.md, padding:14, borderLeftWidth:3, borderWidth:1, borderColor:COLORS.brd2, flex:1, ...SHADOW.sm },
  statVal:    { fontSize:26, fontWeight:'700', marginBottom:2, letterSpacing:-.5 },
  statLbl:    { fontSize:11, color:COLORS.ink3, fontWeight:'500' },
  kpi:        { flex:1, backgroundColor:'rgba(255,255,255,.08)', borderRadius:14, padding:10, borderWidth:1, borderColor:'rgba(255,255,255,.08)' },
  kpiHi:      { backgroundColor:'rgba(255,255,255,.16)', borderColor:'rgba(255,255,255,.2)' },
  kpiVal:     { fontSize:22, fontWeight:'700', color:'#fff', lineHeight:26, letterSpacing:-.5 },
  kpiLbl:     { fontSize:10, color:'rgba(255,255,255,.45)', marginTop:3, fontWeight:'500' },
  aiBadge:    { backgroundColor:COLORS.g50, borderWidth:1, borderColor:COLORS.g200, borderRadius:RADIUS.pill, paddingHorizontal:9, paddingVertical:3, alignSelf:'flex-start' },
  aiBadgeTxt: { fontSize:10, fontWeight:'600', color:COLORS.g700 },
  mbRow:      { flexDirection:'row', alignItems:'center', gap:10 },
  mbLbl:      { fontSize:11, color:COLORS.ink3, width:72, flexShrink:0 },
  mbTrack:    { flex:1, height:6, backgroundColor:COLORS.brd, borderRadius:3, overflow:'hidden' },
  mbFill:     { height:6, borderRadius:3 },
  mbN:        { fontSize:11, fontWeight:'600', color:COLORS.ink2, width:18, textAlign:'right' },
});
