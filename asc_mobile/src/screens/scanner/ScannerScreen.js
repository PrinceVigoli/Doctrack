/**
 * ScannerScreen.js
 * ─────────────────────────────────────────────────────────────
 * Step 1: Camera/gallery → capture document image
 * Step 2: Send to /api/docs/scan/ → HuggingFace OCR + TF-IDF classifier
 * Step 3: Show results → pre-fill SubmitDocument form
 */
import React, { useState, useRef } from 'react';
import {
  View, Text, StyleSheet, TouchableOpacity,
  ScrollView, Alert, ActivityIndicator, Image,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import * as FileSystem from 'expo-file-system/legacy';
import client from '../../api/client';
import { COLORS, RADIUS, SHADOW } from '../../utils/theme';
import { Button, StatusBadge } from '../../components';

const PRIORITY_COLOR = {
  low:'#9CA3AF', normal:COLORS.blue, high:COLORS.amber, urgent:COLORS.red,
};

const COMM_LABELS = {
  internal: '🏛 Internal',
  external: '🌐 External',
  'n/a':    '—',
};

export default function ScannerScreen({ navigation }) {
  const [image,    setImage]    = useState(null);   // { uri, base64 }
  const [scanning, setScanning] = useState(false);
  const [result,   setResult]   = useState(null);
  const [error,    setError]    = useState('');

  // ── Pick from gallery ──────────────────────────────────────
  const pickFromGallery = async () => {
    try {
      const perm = await ImagePicker.requestMediaLibraryPermissionsAsync();
      if (!perm.granted) {
        Alert.alert('Permission needed', 'Allow access to your photos to pick a document.');
        return;
      }
      const res = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ['images'],
        quality:    0.85,
        base64:     true,
      });
      if (!res.canceled && res.assets?.[0]) {
        setImage({ uri: res.assets[0].uri, base64: res.assets[0].base64 });
        setResult(null);
        setError('');
      }
    } catch (e) {
      Alert.alert('Could not open gallery', e?.message || 'Something went wrong. Please try again.');
    }
  };

  // ── Take photo with camera ─────────────────────────────────
  const takePhoto = async () => {
    try {
      const perm = await ImagePicker.requestCameraPermissionsAsync();
      if (!perm.granted) {
        Alert.alert('Permission needed', 'Allow camera access to scan documents.');
        return;
      }
      const res = await ImagePicker.launchCameraAsync({
        mediaTypes: ['images'],
        quality:    0.85,
        base64:     true,
      });
      if (!res.canceled && res.assets?.[0]) {
        setImage({ uri: res.assets[0].uri, base64: res.assets[0].base64 });
        setResult(null);
        setError('');
      }
    } catch (e) {
      Alert.alert('Could not open camera', e?.message || 'Something went wrong. Please try again.');
    }
  };

  // ── Run scan ───────────────────────────────────────────────
  const runScan = async () => {
    if (!image?.base64) return;
    setScanning(true);
    setError('');
    try {
      const { data } = await client.post('/docs/scan/', {
        image:      image.base64,
        media_type: 'image/jpeg',
      });
      setResult(data);
      if (!data.is_readable) {
        setError(data.low_quality_note || 'Image may be too blurry. Try again with better lighting.');
      }
    } catch (e) {
      const msg = e.response?.data?.error || 'Scan failed. Check your connection.';
      setError(msg);
    } finally {
      setScanning(false);
    }
  };

  // ── Pre-fill submit form with scan results ─────────────────
  const useResult = () => {
    if (!result) return;
    navigation.navigate('SubmitDocument', {
      prefill: {
        title:       result.suggested_title || '',
        description: result.summary || result.extracted_text?.slice(0, 300) || '',
        comm_type:   result.comm_type || 'n/a',
        priority:    result.priority  || 'normal',
        doc_type_name: result.doc_type || '',
      },
    });
  };

  return (
    <ScrollView style={s.screen} contentContainerStyle={s.content} showsVerticalScrollIndicator={false}>

      <Text style={s.pageTitle}>Document scanner</Text>
      <Text style={s.pageSub}>
        Take a photo or upload an image of any document — the AI will read it, identify its type, and pre-fill the submission form for you.
      </Text>

      {/* ── Image preview ── */}
      {image ? (
        <View style={s.previewWrap}>
          <Image source={{ uri: image.uri }} style={s.preview} resizeMode="contain" />
          <TouchableOpacity style={s.retakeBtn} onPress={() => { setImage(null); setResult(null); }}>
            <Text style={s.retakeTxt}>✕ Remove</Text>
          </TouchableOpacity>
        </View>
      ) : (
        <View style={s.placeholder}>
          <Text style={s.placeholderIcon}>📄</Text>
          <Text style={s.placeholderTitle}>No document selected</Text>
          <Text style={s.placeholderSub}>Take a photo or pick from your gallery</Text>
        </View>
      )}

      {/* ── Camera / gallery buttons ── */}
      <View style={s.captureRow}>
        <TouchableOpacity style={s.captureBtn} onPress={takePhoto} activeOpacity={0.75}>
          <Text style={s.captureIcon}>📷</Text>
          <Text style={s.captureLbl}>Camera</Text>
        </TouchableOpacity>
        <TouchableOpacity style={s.captureBtn} onPress={pickFromGallery} activeOpacity={0.75}>
          <Text style={s.captureIcon}>🖼️</Text>
          <Text style={s.captureLbl}>Gallery</Text>
        </TouchableOpacity>
      </View>

      {/* ── Scan button ── */}
      {image && !result && (
        <Button
          title={scanning ? 'Reading document...' : 'Scan with AI'}
          onPress={runScan}
          loading={scanning}
          icon={scanning ? null : '🤖'}
          style={{ marginBottom: 16 }}
        />
      )}

      {/* ── Error ── */}
      {error ? (
        <View style={s.errorCard}>
          <Text style={s.errorIcon}>⚠️</Text>
          <Text style={s.errorTxt}>{error}</Text>
        </View>
      ) : null}

      {/* ── Loading ── */}
      {scanning && (
        <View style={s.loadingCard}>
          <ActivityIndicator color={COLORS.g700} />
          <Text style={s.loadingTitle}>AI is reading your document...</Text>
          <Text style={s.loadingSub}>Extracting text · Identifying type · Detecting metadata</Text>
        </View>
      )}

      {/* ── Results ── */}
      {result && !scanning && (
        <View style={s.results}>

          {/* Confidence + type */}
          <View style={s.resultHeader}>
            <View style={s.resultTypeBox}>
              <Text style={s.resultTypeLabel}>Document type</Text>
              <Text style={s.resultType}>{result.doc_type}</Text>
            </View>
            <View style={s.confBox}>
              <Text style={s.confPct}>{Math.round((result.confidence || 0) * 100)}%</Text>
              <Text style={s.confLabel}>confident</Text>
            </View>
          </View>

          {/* Key tags row */}
          <View style={s.tagRow}>
            {result.comm_type && result.comm_type !== 'n/a' && (
              <View style={s.tag}><Text style={s.tagTxt}>{COMM_LABELS[result.comm_type]}</Text></View>
            )}
            <View style={[s.tag, { borderColor: PRIORITY_COLOR[result.priority] }]}>
              <Text style={[s.tagTxt, { color: PRIORITY_COLOR[result.priority] }]}>
                ⚡ {result.priority} priority
              </Text>
            </View>
            {result.local_ai_label && result.local_ai_label !== result.doc_type && (
              <View style={[s.tag, { borderColor: COLORS.ink4 }]}>
                <Text style={[s.tagTxt, { color: COLORS.ink3 }]}>
                  Also: {result.local_ai_label}
                </Text>
              </View>
            )}
          </View>

          {/* Classification note */}
          {result.classification_note && (
            <View style={s.noteCard}>
              <Text style={s.noteIcon}>ℹ️</Text>
              <Text style={s.noteTxt}>{result.classification_note}</Text>
            </View>
          )}

          {/* Summary */}
          {result.summary && (
            <View style={s.section}>
              <Text style={s.sectionTitle}>Summary</Text>
              <Text style={s.summaryTxt}>{result.summary}</Text>
            </View>
          )}

          {/* Metadata */}
          {result.metadata && Object.values(result.metadata).some(Boolean) && (
            <View style={s.section}>
              <Text style={s.sectionTitle}>Extracted details</Text>
              {[
                ['📅 Date',      result.metadata.date],
                ['✉️ From',      result.metadata.from],
                ['📬 To',        result.metadata.to],
                ['📌 Subject',   result.metadata.subject],
                ['🔢 Ref. no.',  result.metadata.reference_number],
              ].filter(([, v]) => v).map(([label, value], i) => (
                <View key={i} style={s.metaRow}>
                  <Text style={s.metaLabel}>{label}</Text>
                  <Text style={s.metaValue}>{value}</Text>
                </View>
              ))}
              {result.metadata.signatories?.length > 0 && (
                <View style={s.metaRow}>
                  <Text style={s.metaLabel}>✍️ Signed by</Text>
                  <Text style={s.metaValue}>{result.metadata.signatories.join(', ')}</Text>
                </View>
              )}
            </View>
          )}

          {/* Extracted text preview */}
          {result.extracted_text && (
            <View style={s.section}>
              <Text style={s.sectionTitle}>Extracted text</Text>
              <View style={s.textBox}>
                <Text style={s.textContent} numberOfLines={8}>{result.extracted_text}</Text>
              </View>
            </View>
          )}

          {/* Suggested title */}
          {result.suggested_title && (
            <View style={s.titlePreview}>
              <Text style={s.titlePreviewLabel}>Suggested title</Text>
              <Text style={s.titlePreviewVal}>{result.suggested_title}</Text>
            </View>
          )}

          {/* CTA */}
          <Button
            title="Use this — fill submit form"
            onPress={useResult}
            icon="→"
            style={{ marginTop: 8 }}
          />
          <Button
            title="Scan another document"
            variant="outline"
            onPress={() => { setImage(null); setResult(null); setError(''); }}
            style={{ marginTop: 10, marginBottom: 20 }}
          />
        </View>
      )}

      {/* Tips */}
      {!image && (
        <View style={s.tips}>
          <Text style={s.tipsTitle}>Tips for best results</Text>
          {[
            'Lay the document flat on a dark surface',
            'Make sure all 4 corners are visible',
            'Good lighting — no shadows across the text',
            'Hold the camera directly above, not at an angle',
            'Works with printed letters, memos, forms, and handwritten notes',
          ].map((tip, i) => (
            <View key={i} style={s.tipRow}>
              <Text style={s.tipDot}>✦</Text>
              <Text style={s.tipTxt}>{tip}</Text>
            </View>
          ))}
        </View>
      )}
    </ScrollView>
  );
}

const s = StyleSheet.create({
  screen:           { flex:1, backgroundColor:COLORS.surf },
  content:          { padding:20, paddingBottom:50 },
  pageTitle:        { fontSize:22, fontWeight:'700', color:COLORS.ink, letterSpacing:-.5, marginBottom:4 },
  pageSub:          { fontSize:13, color:COLORS.ink3, lineHeight:19, marginBottom:20 },
  previewWrap:      { borderRadius:RADIUS.lg, overflow:'hidden', marginBottom:14, ...SHADOW.md, position:'relative' },
  preview:          { width:'100%', height:260, backgroundColor:COLORS.g900 },
  retakeBtn:        { position:'absolute', top:10, right:10, backgroundColor:'rgba(0,0,0,.55)', borderRadius:20, paddingHorizontal:12, paddingVertical:5 },
  retakeTxt:        { fontSize:12, color:'#fff', fontWeight:'600' },
  placeholder:      { height:220, borderRadius:RADIUS.lg, borderWidth:1.5, borderColor:COLORS.brd, borderStyle:'dashed', alignItems:'center', justifyContent:'center', marginBottom:14, backgroundColor:COLORS.card },
  placeholderIcon:  { fontSize:44, marginBottom:10 },
  placeholderTitle: { fontSize:15, fontWeight:'600', color:COLORS.ink3 },
  placeholderSub:   { fontSize:12, color:COLORS.ink4, marginTop:4 },
  captureRow:       { flexDirection:'row', gap:10, marginBottom:14 },
  captureBtn:       { flex:1, flexDirection:'row', alignItems:'center', justifyContent:'center', gap:8, backgroundColor:COLORS.card, borderRadius:RADIUS.md, padding:14, borderWidth:1.5, borderColor:COLORS.brd, ...SHADOW.sm },
  captureIcon:      { fontSize:22 },
  captureLbl:       { fontSize:13, fontWeight:'600', color:COLORS.ink2 },
  errorCard:        { flexDirection:'row', gap:10, alignItems:'flex-start', backgroundColor:'#FEF2F2', borderRadius:RADIUS.md, padding:12, marginBottom:14, borderWidth:1, borderColor:'#FECACA' },
  errorIcon:        { fontSize:18 },
  errorTxt:         { flex:1, fontSize:12, color:COLORS.redDk, lineHeight:18 },
  loadingCard:      { alignItems:'center', backgroundColor:COLORS.g50, borderRadius:RADIUS.lg, padding:24, marginBottom:14, gap:10, borderWidth:1, borderColor:COLORS.g200 },
  loadingTitle:     { fontSize:15, fontWeight:'600', color:COLORS.g800 },
  loadingSub:       { fontSize:12, color:COLORS.g700, textAlign:'center' },
  results:          { gap:0 },
  resultHeader:     { flexDirection:'row', backgroundColor:COLORS.card, borderRadius:RADIUS.lg, padding:16, marginBottom:10, borderWidth:1, borderColor:COLORS.brd2, alignItems:'center', justifyContent:'space-between', ...SHADOW.sm },
  resultTypeBox:    { flex:1 },
  resultTypeLabel:  { fontSize:10, fontWeight:'600', color:COLORS.ink4, textTransform:'uppercase', letterSpacing:.08, marginBottom:4 },
  resultType:       { fontSize:18, fontWeight:'700', color:COLORS.g800, letterSpacing:-.3 },
  confBox:          { alignItems:'center', backgroundColor:COLORS.g50, borderRadius:RADIUS.md, padding:10, borderWidth:1, borderColor:COLORS.g200 },
  confPct:          { fontSize:20, fontWeight:'700', color:COLORS.g700 },
  confLabel:        { fontSize:10, color:COLORS.g700, fontWeight:'500' },
  tagRow:           { flexDirection:'row', flexWrap:'wrap', gap:7, marginBottom:10 },
  tag:              { paddingHorizontal:12, paddingVertical:5, borderRadius:20, borderWidth:1.5, borderColor:COLORS.brd2, backgroundColor:COLORS.card },
  tagTxt:           { fontSize:11, fontWeight:'600', color:COLORS.ink2 },
  noteCard:         { flexDirection:'row', gap:10, backgroundColor:COLORS.blueBg, borderRadius:RADIUS.md, padding:12, marginBottom:10, borderWidth:1, borderColor:'#BFDBFE' },
  noteIcon:         { fontSize:16 },
  noteTxt:          { flex:1, fontSize:12, color:COLORS.blueDk, lineHeight:18 },
  section:          { backgroundColor:COLORS.card, borderRadius:RADIUS.lg, padding:14, marginBottom:10, borderWidth:1, borderColor:COLORS.brd2, ...SHADOW.sm },
  sectionTitle:     { fontSize:12, fontWeight:'600', color:COLORS.ink3, textTransform:'uppercase', letterSpacing:.06, marginBottom:10 },
  summaryTxt:       { fontSize:13, color:COLORS.ink2, lineHeight:20 },
  metaRow:          { flexDirection:'row', gap:12, alignItems:'flex-start', marginBottom:8 },
  metaLabel:        { fontSize:12, color:COLORS.ink3, width:80, flexShrink:0, fontWeight:'500' },
  metaValue:        { fontSize:13, color:COLORS.ink, flex:1, fontWeight:'500' },
  textBox:          { backgroundColor:COLORS.surf, borderRadius:RADIUS.md, padding:12, borderWidth:1, borderColor:COLORS.brd },
  textContent:      { fontSize:12, color:COLORS.ink3, lineHeight:18, fontFamily:'monospace' },
  titlePreview:     { backgroundColor:COLORS.g50, borderRadius:RADIUS.md, padding:14, marginBottom:14, borderWidth:1, borderColor:COLORS.g200 },
  titlePreviewLabel:{ fontSize:10, fontWeight:'700', color:COLORS.g700, textTransform:'uppercase', letterSpacing:.08, marginBottom:6 },
  titlePreviewVal:  { fontSize:15, fontWeight:'600', color:COLORS.g800 },
  tips:             { backgroundColor:COLORS.card, borderRadius:RADIUS.lg, padding:16, borderWidth:1, borderColor:COLORS.brd2, marginTop:8 },
  tipsTitle:        { fontSize:13, fontWeight:'700', color:COLORS.ink2, marginBottom:12 },
  tipRow:           { flexDirection:'row', gap:10, marginBottom:7 },
  tipDot:           { fontSize:11, color:COLORS.g700, marginTop:1 },
  tipTxt:           { fontSize:12, color:COLORS.ink3, flex:1, lineHeight:18 },
});