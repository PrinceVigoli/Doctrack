/**
 * DocumentDetailScreen
 * Features: Forward modal, role-based UI, pull-to-refresh,
 * real-time WS tracking, document preview, status update, comments
 */
import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  Alert, TextInput, Modal, RefreshControl, Linking,
} from 'react-native';
const WebView = () => null;
import { docsAPI, authAPI } from '../../api/services';
import { BASE_HOST } from '../../api/client';
import { StatusBadge, Button, LoadingOverlay } from '../../components';
import { useTheme, RADIUS, SHADOW, STATUS, PRIORITY_COLOR } from '../../utils/theme';
import { useAuth } from '../../context/AuthContext';
import { useDocumentTracking } from '../../utils/useDocumentTracking';
import * as secureStorage from '../../utils/secureStorage';
import SignaturePad from '../../components/signature/SignaturePad';

const STATUSES = ['in_review','approved','rejected','returned','completed'];

export default function DocumentDetailScreen({ route, navigation }) {
  const { id }   = route.params;
  const { user } = useAuth();
  const C        = useTheme();

  const [doc,       setDoc]       = useState(null);
  const [loading,   setLoading]   = useState(true);
  const [refreshing,setRefreshing]= useState(false);
  const [modal,     setModal]     = useState(null); // 'status'|'forward'|'comment'|'preview'
  const [note,      setNote]      = useState('');
  const [busy,      setBusy]      = useState(false);
  const [showSignPad, setShowSignPad] = useState(false);
  const [signature,   setSignature]   = useState(null);
  const [pendingApproval, setPendingApproval] = useState(false);

  // Forward modal state
  const [offices,     setOffices]     = useState([]);
  const [toOfficeId,  setToOfficeId]  = useState(null);
  const [officesLoaded,setOfficesLoaded]=useState(false);

  // WS real-time tracking
  const [accessToken, setAccessToken] = useState('');
  useEffect(() => { secureStorage.getItem('access_token').then(t => setAccessToken(t||'')); }, []);
  const { logs: wsLogs, connected } = useDocumentTracking(doc?.tracking_number, accessToken);

  const load = useCallback(async () => {
    try {
      const { data } = await docsAPI.get(id);
      setDoc(data);
    } catch {
      Alert.alert('Error', 'Could not load document.');
      navigation.goBack();
    } finally { setLoading(false); setRefreshing(false); }
  }, [id]);

  useEffect(() => { load(); }, [id]);
  const onRefresh = () => { setRefreshing(true); load(); };

  // Load offices when forward modal opens
  const openForward = async () => {
    setModal('forward');
    if (!officesLoaded) {
      const { data } = await authAPI.offices();
      setOffices(data.results ?? data);
      setOfficesLoaded(true);
    }
  };

  // Role-based permissions
  const canForward      = user?.role === 'superadmin' || user?.role === 'records_officer' || user?.role === 'program_chair';
  const canChangeStatus = user?.role === 'superadmin' || user?.role === 'records_officer';
  const canComment      = true; // all roles

  const handleStatus = async (newStatus) => {
    // Require a signature for approvals
    if (newStatus === 'approved' && !signature) {
      setPendingApproval(true);
      setShowSignPad(true);
      return;
    }
    setBusy(true);
    try {
      const { data } = await docsAPI.updateStatus(id, newStatus, note);
      setDoc(data); setModal(null); setNote(''); setSignature(null); setPendingApproval(false);
    } catch { Alert.alert('Error', 'Could not update status.'); }
    finally { setBusy(false); }
  };

  const onSignatureSaved = (dataUrl) => {
    setSignature(dataUrl);
    setShowSignPad(false);
    if (pendingApproval) {
      // Re-trigger approval now that signature exists
      setTimeout(() => handleStatusWithSignature(dataUrl), 200);
    }
  };

  const handleStatusWithSignature = async (sig) => {
    setBusy(true);
    try {
      const { data } = await docsAPI.updateStatus(id, 'approved', note ? `${note} [Signed]` : '[Signed electronically]');
      setDoc(data); setModal(null); setNote(''); setSignature(null); setPendingApproval(false);
    } catch { Alert.alert('Error', 'Could not update status.'); }
    finally { setBusy(false); }
  };

  const handleForward = async () => {
    if (!toOfficeId) { Alert.alert('Select office', 'Please choose a destination office.'); return; }
    setBusy(true);
    try {
      const { data } = await docsAPI.forward(id, toOfficeId, note);
      setDoc(data); setModal(null); setNote(''); setToOfficeId(null);
      Alert.alert('✅ Forwarded', `Document sent to ${data.current_office?.name}`);
    } catch { Alert.alert('Error', 'Could not forward document.'); }
    finally { setBusy(false); }
  };

  const handleComment = async () => {
    if (!note.trim()) return;
    setBusy(true);
    try {
      await docsAPI.comment(id, note.trim());
      setNote(''); setModal(null); await load();
    } catch { Alert.alert('Error', 'Could not post comment.'); }
    finally { setBusy(false); }
  };

  if (loading) return <LoadingOverlay />;
  if (!doc)    return null;

  const pct  = Math.round((doc.ai_confidence || 0) * 100);
  const logs = wsLogs.length > 0 ? wsLogs : (doc.logs || []);
  const s    = makeStyles(C);

  return (
    <>
      <ScrollView
        style={s.screen}
        contentContainerStyle={s.content}
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={C.g800} />}
      >
        {/* WS connection indicator */}
        {connected && (
          <View style={s.wsBar}>
            <View style={s.wsLive} /><Text style={s.wsTxt}>Live updates active</Text>
          </View>
        )}

        {/* Hero */}
        <View style={s.hero}>
          <Text style={s.trackNum}>{doc.tracking_number}</Text>
          <Text style={s.title}>{doc.title}</Text>
          <View style={s.pills}>
            {doc.priority && (
              <View style={s.pill}>
                <Text style={[s.pillTxt, { color: PRIORITY_COLOR[doc.priority] }]}>
                  ● {doc.priority}
                </Text>
              </View>
            )}
            {doc.current_office && (
              <View style={s.pill}><Text style={s.pillTxt}>🏢 {doc.current_office.name}</Text></View>
            )}
            {doc.comm_type && doc.comm_type !== 'n/a' && (
              <View style={s.pill}>
                <Text style={s.pillTxt}>
                  {doc.comm_type === 'internal' ? '🏛 Internal' : '🌐 External'}
                </Text>
              </View>
            )}
            <StatusBadge status={doc.status} />
          </View>
        </View>

        {/* AI classification */}
        {doc.ai_label && (
          <View style={s.aiCard}>
            <Text style={s.aiTag}>🤖 AI CLASSIFICATION</Text>
            <Text style={s.aiVal}>{doc.ai_label}</Text>
            <View style={s.confRow}>
              <View style={s.confTrack}><View style={[s.confFill, { width:`${pct}%` }]} /></View>
              <Text style={s.confPct}>{pct}% confidence</Text>
            </View>
          </View>
        )}

        {/* File preview */}
        {doc.file && (
          <TouchableOpacity style={s.fileRow} onPress={() => setModal('preview')} activeOpacity={0.75}>
            <Text style={s.fileIcon}>📄</Text>
            <View style={{ flex:1 }}>
              <Text style={s.fileName} numberOfLines={1}>{doc.file.split('/').pop()}</Text>
              <Text style={s.fileSize}>{doc.file_size ? `${(doc.file_size/1024).toFixed(0)} KB` : 'Tap to preview'}</Text>
            </View>
            <Text style={s.fileArrow}>›</Text>
          </TouchableOpacity>
        )}

        {/* Meta */}
        <View style={s.metaGrid}>
          {[
            ['📁', 'Type',      doc.doc_type?.name || '—'],
            ['👤', 'Submitted', doc.submitted_by?.full_name || '—'],
            ['📅', 'Date',      new Date(doc.created_at).toLocaleDateString('en-PH',{month:'short',day:'numeric',year:'numeric'})],
            doc.due_date && ['⏰', 'Due', doc.due_date],
            doc.completed_at && ['✅', 'Completed', new Date(doc.completed_at).toLocaleDateString()],
          ].filter(Boolean).map(([icon, label, value], i) => (
            <View key={i} style={s.metaItem}>
              <Text style={s.metaIcon}>{icon}</Text>
              <View>
                <Text style={s.metaLbl}>{label}</Text>
                <Text style={s.metaVal}>{value}</Text>
              </View>
            </View>
          ))}
        </View>

        {/* Role-based action buttons */}
        {doc.status !== 'completed' && (
          <View style={s.actions}>
            {canForward && (
              <TouchableOpacity style={s.actionBtn} onPress={openForward} activeOpacity={0.7}>
                <Text style={s.actionIcon}>➡️</Text>
                <Text style={s.actionLbl}>Forward</Text>
              </TouchableOpacity>
            )}
            {canChangeStatus && (
              <TouchableOpacity style={s.actionBtn} onPress={() => setModal('status')} activeOpacity={0.7}>
                <Text style={s.actionIcon}>🔄</Text>
                <Text style={s.actionLbl}>Status</Text>
              </TouchableOpacity>
            )}
            {canComment && (
              <TouchableOpacity style={s.actionBtn} onPress={() => setModal('comment')} activeOpacity={0.7}>
                <Text style={s.actionIcon}>💬</Text>
                <Text style={s.actionLbl}>Comment</Text>
              </TouchableOpacity>
            )}
            {doc.can_download && (
              <TouchableOpacity style={s.actionBtn}
                onPress={() => Linking.openURL(`${doc.file}`)} activeOpacity={0.7}>
                <Text style={s.actionIcon}>⬇️</Text>
                <Text style={s.actionLbl}>Download</Text>
              </TouchableOpacity>
            )}
          </View>
        )}

        {/* Tracking timeline */}
        <Text style={s.sectionTitle}>Tracking history</Text>
        <View style={s.timeline}>
          {logs.length === 0
            ? <Text style={s.emptyTxt}>No tracking history yet.</Text>
            : logs.map((log, i) => (
              <View key={log.id || i} style={s.tlRow}>
                <View style={s.tlSpine}>
                  <View style={[s.tlDot, i===0 && { backgroundColor:C.g700 }]} />
                  {i < logs.length - 1 && <View style={s.tlLine} />}
                </View>
                <View style={s.tlBody}>
                  <Text style={[s.tlAction, i===0 && { color:C.g700 }]}>
                    {(log.action||'').replace('_',' ').replace(/\b\w/g,c=>c.toUpperCase())}
                  </Text>
                  <Text style={s.tlMeta}>
                    by {log.actor?.full_name || log.actor || '—'} ·{' '}
                    {new Date(log.timestamp).toLocaleString('en-PH',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'})}
                  </Text>
                  {log.from_office && (
                    <Text style={s.tlRoute}>
                      {log.from_office?.name||log.from_office} → {log.to_office?.name||log.to_office||'—'}
                    </Text>
                  )}
                  {log.note ? <Text style={s.tlNote}>"{log.note}"</Text> : null}
                </View>
              </View>
            ))
          }
        </View>

        {/* Comments */}
        {(doc.comments||[]).length > 0 && (
          <>
            <Text style={s.sectionTitle}>Comments</Text>
            {doc.comments.map((c,i) => (
              <View key={i} style={s.comment}>
                <View style={s.commentHeader}>
                  <Text style={s.commentAuthor}>{c.author?.full_name||'—'}</Text>
                  <Text style={s.commentTime}>{new Date(c.created_at).toLocaleDateString('en-PH',{month:'short',day:'numeric'})}</Text>
                </View>
                <Text style={s.commentBody}>{c.body}</Text>
              </View>
            ))}
          </>
        )}
      </ScrollView>

      {/* ══ FORWARD MODAL ══ */}
      <Modal visible={modal==='forward'} transparent animationType="slide">
        <View style={s.overlay}>
          <View style={s.sheet}>
            <View style={s.sheetHandle} />
            <Text style={s.sheetTitle}>Forward document</Text>
            <Text style={s.sheetSub}>Select destination office</Text>
            <ScrollView style={{ maxHeight:260, marginBottom:12 }} showsVerticalScrollIndicator={false}>
              {offices.map(o => (
                <TouchableOpacity
                  key={o.id}
                  style={[s.officeOpt, toOfficeId===o.id && s.officeOptOn]}
                  onPress={() => setToOfficeId(o.id)}
                  activeOpacity={0.7}
                >
                  <View style={[s.officeRadio, toOfficeId===o.id && s.officeRadioOn]}>
                    {toOfficeId===o.id && <View style={s.officeRadioDot} />}
                  </View>
                  <View style={{ flex:1 }}>
                    <Text style={[s.officeName, toOfficeId===o.id && { color:C.g800, fontWeight:'700' }]}>{o.name}</Text>
                    <Text style={s.officeCode}>{o.code}</Text>
                  </View>
                  {o.is_records_office && <Text style={{ fontSize:10, color:C.g700 }}>📌</Text>}
                </TouchableOpacity>
              ))}
            </ScrollView>
            <TextInput style={s.noteInput} placeholder="Note / instructions (optional)"
              placeholderTextColor={C.ink4} value={note} onChangeText={setNote} multiline />
            <Button title="Forward document" onPress={handleForward} loading={busy} style={{ marginTop:10 }} />
            <Button title="Cancel" variant="outline" onPress={() => { setModal(null); setNote(''); setToOfficeId(null); }} style={{ marginTop:8 }} />
          </View>
        </View>
      </Modal>

      {/* ══ STATUS MODAL ══ */}
      <Modal visible={modal==='status'} transparent animationType="slide">
        <View style={s.overlay}>
          <View style={s.sheet}>
            <View style={s.sheetHandle} />
            <Text style={s.sheetTitle}>Update status</Text>
            {STATUSES.map(st => {
              const meta = STATUS[st] || { bg:'#F3F4F6', text:'#6B7280', label:st };
              return (
                <TouchableOpacity key={st} style={s.statusOpt} onPress={() => handleStatus(st)}>
                  <View style={[s.statusDot, { backgroundColor: meta.text }]} />
                  <Text style={[s.statusLbl, { color: meta.text }]}>
                    {meta.label}
                  </Text>
                </TouchableOpacity>
              );
            })}
            <TextInput style={s.noteInput} placeholder="Note (optional)"
              placeholderTextColor={C.ink4} value={note} onChangeText={setNote} multiline />
            <Button title="Cancel" variant="outline" onPress={() => { setModal(null); setNote(''); }} style={{ marginTop:8 }} />
          </View>
        </View>
      </Modal>

      {/* ══ COMMENT MODAL ══ */}
      <Modal visible={modal==='comment'} transparent animationType="slide">
        <View style={s.overlay}>
          <View style={s.sheet}>
            <View style={s.sheetHandle} />
            <Text style={s.sheetTitle}>Add comment</Text>
            <TextInput style={[s.noteInput, { height:100 }]} placeholder="Write your comment..."
              placeholderTextColor={C.ink4} value={note} onChangeText={setNote} multiline />
            <Button title="Post comment" onPress={handleComment} loading={busy} style={{ marginTop:10 }} />
            <Button title="Cancel" variant="outline" onPress={() => { setModal(null); setNote(''); }} style={{ marginTop:8 }} />
          </View>
        </View>
      </Modal>

      {/* ══ DOCUMENT PREVIEW MODAL ══ */}
      <Modal visible={modal==='preview'} animationType="slide">
        <View style={{ flex:1, backgroundColor:C.g900 }}>
          <View style={{ flexDirection:'row', alignItems:'center', padding:16, paddingTop:50 }}>
            <TouchableOpacity onPress={() => setModal(null)} style={{ marginRight:16 }}>
              <Text style={{ fontSize:16, color:'#fff', fontWeight:'600' }}>✕ Close</Text>
            </TouchableOpacity>
            <Text style={{ fontSize:15, color:'#fff', fontWeight:'600', flex:1 }} numberOfLines={1}>
              {doc.file?.split('/').pop()}
            </Text>
          </View>
          {doc.file ? (
            <WebView
              source={{ uri: doc.file.startsWith('http') ? doc.file : `${BASE_HOST}${doc.file}` }}
              style={{ flex:1 }}
              startInLoadingState
            />
          ) : (
            <View style={{ flex:1, alignItems:'center', justifyContent:'center' }}>
              <Text style={{ color:'#fff', fontSize:16 }}>No file attached</Text>
            </View>
          )}
        </View>
      </Modal>

      {/* ══ SIGNATURE PAD ══ */}
      <SignaturePad
        visible={showSignPad}
        onClose={() => { setShowSignPad(false); setPendingApproval(false); }}
        onSave={onSignatureSaved}
      />
    </>
  );
}

const makeStyles = (C) => StyleSheet.create({
  screen:        { flex:1, backgroundColor:C.surf },
  content:       { paddingBottom:50 },
  wsBar:         { flexDirection:'row', alignItems:'center', gap:6, backgroundColor:C.g50, padding:10, paddingHorizontal:16, borderBottomWidth:1, borderBottomColor:C.brd2 },
  wsLive:        { width:7, height:7, borderRadius:4, backgroundColor:C.g600 },
  wsTxt:         { fontSize:11, color:C.g700, fontWeight:'500' },
  hero:          { backgroundColor:C.g900, padding:20, paddingTop:16 },
  trackNum:      { fontSize:10, color:'rgba(255,255,255,.35)', fontFamily:'monospace', fontWeight:'600', letterSpacing:.08, marginBottom:6 },
  title:         { fontSize:18, fontWeight:'700', color:'#fff', lineHeight:26, letterSpacing:-.4, marginBottom:14 },
  pills:         { flexDirection:'row', flexWrap:'wrap', gap:8, alignItems:'center' },
  pill:          { flexDirection:'row', alignItems:'center', gap:4, backgroundColor:'rgba(255,255,255,.1)', borderRadius:20, paddingHorizontal:10, paddingVertical:5, borderWidth:1, borderColor:'rgba(255,255,255,.12)' },
  pillTxt:       { fontSize:10, fontWeight:'500', color:'rgba(255,255,255,.8)', textTransform:'capitalize' },
  aiCard:        { margin:16, backgroundColor:C.g50, borderRadius:18, padding:16, borderWidth:1, borderColor:C.g200 },
  aiTag:         { fontSize:9, fontWeight:'700', color:C.g700, letterSpacing:.1, marginBottom:6 },
  aiVal:         { fontSize:18, fontWeight:'700', color:C.g800, letterSpacing:-.3, marginBottom:8 },
  confRow:       { flexDirection:'row', alignItems:'center', gap:10 },
  confTrack:     { flex:1, height:5, backgroundColor:C.g200, borderRadius:3, overflow:'hidden' },
  confFill:      { height:5, borderRadius:3, backgroundColor:C.g700 },
  confPct:       { fontSize:11, fontWeight:'700', color:C.g700 },
  fileRow:       { flexDirection:'row', alignItems:'center', gap:12, backgroundColor:C.card, marginHorizontal:16, marginBottom:4, borderRadius:RADIUS.lg, padding:14, borderWidth:1, borderColor:C.brd2, ...SHADOW.sm },
  fileIcon:      { fontSize:28 },
  fileName:      { fontSize:13, fontWeight:'600', color:C.ink },
  fileSize:      { fontSize:11, color:C.ink3, marginTop:2 },
  fileArrow:     { fontSize:22, color:C.ink4 },
  metaGrid:      { marginHorizontal:16, marginBottom:16, gap:12 },
  metaItem:      { flexDirection:'row', alignItems:'flex-start', gap:12 },
  metaIcon:      { fontSize:18, marginTop:1 },
  metaLbl:       { fontSize:10, color:C.ink4, fontWeight:'600', marginBottom:1 },
  metaVal:       { fontSize:14, fontWeight:'500', color:C.ink },
  actions:       { flexDirection:'row', gap:10, marginHorizontal:16, marginBottom:20, flexWrap:'wrap' },
  actionBtn:     { flex:1, minWidth:70, backgroundColor:C.card, borderRadius:14, padding:12, alignItems:'center', gap:5, borderWidth:1, borderColor:C.brd2, ...SHADOW.sm },
  actionIcon:    { fontSize:22 },
  actionLbl:     { fontSize:10, color:C.ink3, fontWeight:'500', textAlign:'center' },
  sectionTitle:  { fontSize:15, fontWeight:'600', color:C.ink2, paddingHorizontal:16, marginBottom:12 },
  timeline:      { paddingHorizontal:16, marginBottom:20 },
  tlRow:         { flexDirection:'row', gap:12 },
  tlSpine:       { width:16, alignItems:'center' },
  tlDot:         { width:12, height:12, borderRadius:6, backgroundColor:C.blue, marginTop:3, flexShrink:0 },
  tlLine:        { flex:1, width:1.5, backgroundColor:C.brd2, marginVertical:3 },
  tlBody:        { flex:1, backgroundColor:C.card, borderRadius:14, padding:12, marginBottom:8, borderWidth:1, borderColor:C.brd2, ...SHADOW.sm },
  tlAction:      { fontSize:13, fontWeight:'600', color:C.blue, letterSpacing:-.1 },
  tlMeta:        { fontSize:11, color:C.ink3, marginTop:3 },
  tlRoute:       { fontSize:11, color:C.ink4, marginTop:2 },
  tlNote:        { fontSize:12, color:C.ink2, fontStyle:'italic', marginTop:5, borderLeftWidth:2, borderLeftColor:C.brd2, paddingLeft:8 },
  emptyTxt:      { fontSize:13, color:C.ink4, paddingHorizontal:16 },
  comment:       { backgroundColor:C.card, borderRadius:14, padding:14, marginHorizontal:16, marginBottom:8, borderWidth:1, borderColor:C.brd2 },
  commentHeader: { flexDirection:'row', justifyContent:'space-between', marginBottom:6 },
  commentAuthor: { fontSize:13, fontWeight:'600', color:C.ink },
  commentTime:   { fontSize:11, color:C.ink4 },
  commentBody:   { fontSize:13, color:C.ink2, lineHeight:19 },
  overlay:       { flex:1, backgroundColor:'rgba(0,0,0,.45)', justifyContent:'flex-end' },
  sheet:         { backgroundColor:C.card, borderTopLeftRadius:28, borderTopRightRadius:28, padding:24, paddingBottom:48, maxHeight:'85%' },
  sheetHandle:   { width:40, height:4, borderRadius:2, backgroundColor:C.brd, alignSelf:'center', marginBottom:16 },
  sheetTitle:    { fontSize:18, fontWeight:'700', color:C.ink, letterSpacing:-.3, marginBottom:4 },
  sheetSub:      { fontSize:13, color:C.ink3, marginBottom:16 },
  officeOpt:     { flexDirection:'row', alignItems:'center', gap:12, padding:12, borderRadius:RADIUS.md, borderWidth:1.5, borderColor:C.brd2, marginBottom:8, backgroundColor:C.surf },
  officeOptOn:   { borderColor:C.g700, backgroundColor:C.g50 },
  officeRadio:   { width:18, height:18, borderRadius:9, borderWidth:2, borderColor:C.brd2, alignItems:'center', justifyContent:'center', flexShrink:0 },
  officeRadioOn: { borderColor:C.g700 },
  officeRadioDot:{ width:8, height:8, borderRadius:4, backgroundColor:C.g700 },
  officeName:    { fontSize:13, color:C.ink, fontWeight:'500' },
  officeCode:    { fontSize:10, color:C.ink4, fontFamily:'monospace', marginTop:1 },
  noteInput:     { borderWidth:1.5, borderColor:C.brd, borderRadius:RADIUS.md, padding:12, fontSize:14, color:C.ink, marginTop:4, minHeight:50, backgroundColor:C.surf },
  statusOpt:     { flexDirection:'row', alignItems:'center', gap:12, paddingVertical:14, borderBottomWidth:1, borderBottomColor:C.brd2 },
  statusDot:     { width:10, height:10, borderRadius:5 },
  statusLbl:     { fontSize:15, fontWeight:'600' },
});