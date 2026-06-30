/**
 * QRScannerScreen — scan a document's QR code to open it instantly
 */
import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import { Camera, CameraView } from 'expo-camera';
import { useNavigation } from '@react-navigation/native';
import client from '../../api/client';
import { useTheme, RADIUS } from '../../utils/theme';

export default function QRScannerScreen() {
  const C        = useTheme();
  const nav      = useNavigation();
  const [perm,   setPerm]    = useState(null);
  const [scanned,setScanned] = useState(false);
  const [loading,setLoading] = useState(false);

  useEffect(() => {
    Camera.requestCameraPermissionsAsync().then(({ status }) => setPerm(status === 'granted'));
  }, []);

  const handleScan = async ({ data }) => {
    if (scanned || loading) return;
    setScanned(true);
    setLoading(true);

    // QR code can be a tracking number directly or a URL containing it
    let trackingNum = data.trim();
    const match = data.match(/ASC-\d{6}-[A-Z0-9]{6}/);
    if (match) trackingNum = match[0];

    try {
      // Look up by tracking number
      const { data: list } = await client.get('/docs/', { params: { search: trackingNum } });
      const docs = list.results ?? list;
      const doc  = docs.find(d => d.tracking_number === trackingNum);
      if (doc) {
        nav.replace('DocumentDetail', { id: doc.id });
      } else {
        Alert.alert('Not found', `No document found with tracking number:\n${trackingNum}`, [
          { text: 'Scan again', onPress: () => setScanned(false) },
        ]);
      }
    } catch {
      Alert.alert('Error', 'Could not look up document.', [
        { text: 'Try again', onPress: () => setScanned(false) },
      ]);
    } finally { setLoading(false); }
  };

  const s = makeStyles(C);

  if (perm === null) return <View style={s.screen}><Text style={s.msg}>Requesting camera...</Text></View>;
  if (!perm)         return (
    <View style={s.screen}>
      <Text style={s.msg}>📷</Text>
      <Text style={s.msgTxt}>Camera access denied.{'\n'}Please enable in Settings.</Text>
    </View>
  );

  return (
    <View style={s.screen}>
      <CameraView
        style={StyleSheet.absoluteFillObject}
        barcodeScannerSettings={{ barcodeTypes: ['qr'] }}
        onBarcodeScanned={scanned ? undefined : handleScan}
      />
      {/* Overlay */}
      <View style={s.overlay}>
        <Text style={s.hint}>Point camera at a document QR code</Text>
        <View style={s.frame} />
        {loading && <Text style={s.loading}>Looking up document...</Text>}
        {scanned && !loading && (
          <TouchableOpacity style={s.rescanBtn} onPress={() => setScanned(false)}>
            <Text style={s.rescanTxt}>Scan again</Text>
          </TouchableOpacity>
        )}
      </View>
    </View>
  );
}

const makeStyles = (C) => StyleSheet.create({
  screen:    { flex:1, backgroundColor:'#000', alignItems:'center', justifyContent:'center' },
  msg:       { fontSize:48, color:'#fff', marginBottom:12, textAlign:'center' },
  msgTxt:    { fontSize:14, color:'rgba(255,255,255,.7)', textAlign:'center', lineHeight:22 },
  overlay:   { ...StyleSheet.absoluteFillObject, alignItems:'center', justifyContent:'center', gap:20 },
  hint:      { fontSize:14, color:'rgba(255,255,255,.85)', fontWeight:'600', backgroundColor:'rgba(0,0,0,.5)', paddingHorizontal:18, paddingVertical:8, borderRadius:RADIUS.pill },
  frame:     { width:240, height:240, borderRadius:20, borderWidth:3, borderColor:'rgba(255,255,255,.8)', backgroundColor:'transparent' },
  loading:   { fontSize:14, color:'#fff', fontWeight:'600' },
  rescanBtn: { backgroundColor:C.g800, paddingHorizontal:24, paddingVertical:12, borderRadius:RADIUS.md },
  rescanTxt: { fontSize:14, color:'#fff', fontWeight:'600' },
});
