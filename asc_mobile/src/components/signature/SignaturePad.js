/**
 * SignaturePad — draw a signature for approvals
 * Pure HTML5 canvas inside a WebView (works on iOS + Android without native modules)
 */
import React, { useRef, useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Modal } from 'react-native';
import { WebView } from 'react-native-webview';
import { useTheme, RADIUS } from '../../utils/theme';
import { Button } from '../index';

const SIGNATURE_HTML = `
<!DOCTYPE html>
<html><head><meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
<style>
  * { margin:0; padding:0; touch-action:none; }
  body { background:#fff; }
  canvas { display:block; width:100vw; height:100vh; }
</style></head>
<body>
<canvas id="pad"></canvas>
<script>
  const canvas = document.getElementById('pad');
  const ctx = canvas.getContext('2d');
  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    ctx.lineWidth = 3;
    ctx.lineCap = 'round';
    ctx.strokeStyle = '#1B4332';
  }
  resize();
  window.addEventListener('resize', resize);

  let drawing = false, lastX = 0, lastY = 0;
  function pos(e) {
    const t = e.touches ? e.touches[0] : e;
    const rect = canvas.getBoundingClientRect();
    return { x: t.clientX - rect.left, y: t.clientY - rect.top };
  }
  function start(e) { drawing = true; const p = pos(e); lastX = p.x; lastY = p.y; }
  function move(e) {
    if (!drawing) return;
    const p = pos(e);
    ctx.beginPath(); ctx.moveTo(lastX, lastY); ctx.lineTo(p.x, p.y); ctx.stroke();
    lastX = p.x; lastY = p.y;
    e.preventDefault();
  }
  function end() { drawing = false; }

  canvas.addEventListener('touchstart', start);
  canvas.addEventListener('touchmove', move);
  canvas.addEventListener('touchend', end);
  canvas.addEventListener('mousedown', start);
  canvas.addEventListener('mousemove', move);
  canvas.addEventListener('mouseup', end);

  function clearPad() { ctx.clearRect(0, 0, canvas.width, canvas.height); }
  function getSignature() {
    window.ReactNativeWebView.postMessage(canvas.toDataURL('image/png'));
  }
  window.clearPad = clearPad;
  window.getSignature = getSignature;
</script>
</body></html>
`;

export default function SignaturePad({ visible, onClose, onSave }) {
  const C = useTheme();
  const webRef = useRef(null);
  const [hasSignature, setHasSignature] = useState(false);

  const handleClear = () => {
    webRef.current?.injectJavaScript('window.clearPad(); true;');
    setHasSignature(false);
  };

  const handleSave = () => {
    webRef.current?.injectJavaScript('window.getSignature(); true;');
  };

  const handleMessage = (event) => {
    const dataUrl = event.nativeEvent.data;
    onSave(dataUrl);
    onClose();
  };

  const s = makeStyles(C);
  return (
    <Modal visible={visible} animationType="slide">
      <View style={s.container}>
        <View style={s.header}>
          <Text style={s.title}>Draw your signature</Text>
          <TouchableOpacity onPress={onClose}><Text style={s.close}>✕</Text></TouchableOpacity>
        </View>
        <Text style={s.hint}>Use your finger to sign in the box below</Text>
        <View style={s.padWrap}>
          <WebView
            ref={webRef}
            source={{ html: SIGNATURE_HTML }}
            onMessage={handleMessage}
            scrollEnabled={false}
            onTouchStart={() => setHasSignature(true)}
            style={{ flex:1 }}
          />
        </View>
        <View style={s.actions}>
          <Button title="Clear" variant="outline" onPress={handleClear} style={{ flex:1 }} />
          <Button title="Save signature" onPress={handleSave} style={{ flex:1 }} />
        </View>
      </View>
    </Modal>
  );
}

const makeStyles = (C) => StyleSheet.create({
  container: { flex:1, backgroundColor:C.surf, paddingTop:50 },
  header:    { flexDirection:'row', justifyContent:'space-between', alignItems:'center', paddingHorizontal:20, marginBottom:6 },
  title:     { fontSize:18, fontWeight:'700', color:C.ink, letterSpacing:-.3 },
  close:     { fontSize:18, color:C.ink3 },
  hint:      { fontSize:12, color:C.ink3, paddingHorizontal:20, marginBottom:14 },
  padWrap:   { flex:1, marginHorizontal:20, borderRadius:RADIUS.lg, borderWidth:2, borderColor:C.brd, borderStyle:'dashed', overflow:'hidden', backgroundColor:'#fff', marginBottom:14 },
  actions:   { flexDirection:'row', gap:10, paddingHorizontal:20, paddingBottom:30 },
});
