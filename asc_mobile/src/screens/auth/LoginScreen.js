import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  KeyboardAvoidingView, Platform, Alert, TextInput,
} from 'react-native';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components';
import { COLORS, RADIUS, SHADOW, useTheme } from '../../utils/theme';
import { useBiometric } from '../../hooks/useBiometric';

export default function LoginScreen() {
  const { login }  = useAuth();
  const C          = useTheme();
  const bio        = useBiometric();
  const [form,     setForm]     = useState({ username:'', password:'' });
  const [loading,  setLoading]  = useState(false);
  const [showPass, setShowPass] = useState(false);
  const [bioType,  setBioType]  = useState('Biometrics');
  const [errors,   setErrors]   = useState({});

  useEffect(() => {
    bio.getType().then(setBioType);
  }, []);

  const set = (k, v) => { setForm(f=>({...f,[k]:v})); setErrors(e=>({...e,[k]:''})); };

  const validate = () => {
    const e = {};
    if (!form.username.trim()) e.username = 'Username is required';
    if (!form.password)        e.password = 'Password is required';
    setErrors(e); return !Object.keys(e).length;
  };

  const submit = async (username, password) => {
    setLoading(true);
    try {
      await login(username, password);
      // Save creds for biometric on success
      if (bio.supported && bio.enrolled) await bio.saveCreds(username, password);
    } catch (err) {
      Alert.alert('Sign in failed', err.response?.data?.detail || 'Invalid username or password.');
    } finally { setLoading(false); }
  };

  const handleSubmit = () => { if (validate()) submit(form.username.trim(), form.password); };

  const handleBiometric = async () => {
    const creds = await bio.authenticate();
    if (creds) await submit(creds.username, creds.password);
    else Alert.alert('Authentication failed', 'Please sign in with your password.');
  };

  const s = makeStyles(C);
  return (
    <KeyboardAvoidingView style={{ flex:1 }} behavior={Platform.OS==='ios'?'padding':undefined}>
      <ScrollView style={s.screen} contentContainerStyle={s.scroll} keyboardShouldPersistTaps="handled">
        <View style={s.hero}>
          <View style={s.logoBox}><Text style={s.logoIcon}>📄</Text></View>
          <Text style={s.wordmark}>DocTrack</Text>
          <Text style={s.tagline}>Apayao State College{'\n'}Luna Campus</Text>
        </View>
        <View style={s.sheet}>
          <Text style={s.heading}>Welcome back</Text>
          <Text style={s.sub}>Sign in to your account</Text>

          <View style={s.field}>
            <Text style={s.fieldLabel}>Username</Text>
            <View style={[s.inputWrap, errors.username && s.inputError]}>
              <Text style={s.fieldIcon}>👤</Text>
              <TextInput style={s.textIn} placeholder="e.g. msantos" placeholderTextColor={C.ink4}
                autoCapitalize="none" autoCorrect={false}
                value={form.username} onChangeText={v => set('username', v)} onSubmitEditing={handleSubmit} />
            </View>
            {errors.username ? <Text style={s.errTxt}>{errors.username}</Text> : null}
          </View>

          <View style={s.field}>
            <Text style={s.fieldLabel}>Password</Text>
            <View style={[s.inputWrap, errors.password && s.inputError]}>
              <Text style={s.fieldIcon}>🔒</Text>
              <TextInput style={s.textIn} placeholder="Enter your password" placeholderTextColor={C.ink4}
                secureTextEntry={!showPass} value={form.password}
                onChangeText={v => set('password', v)} onSubmitEditing={handleSubmit} />
              <TouchableOpacity onPress={() => setShowPass(p=>!p)} style={{ padding:4 }}>
                <Text style={{ fontSize:16 }}>{showPass ? '🙈' : '👁️'}</Text>
              </TouchableOpacity>
            </View>
            {errors.password ? <Text style={s.errTxt}>{errors.password}</Text> : null}
          </View>

          <Button title="Sign in" onPress={handleSubmit} loading={loading} icon="→" style={{ marginTop:8 }} />

          {/* Biometric login */}
          {bio.enabled && (
            <TouchableOpacity style={s.bioBtn} onPress={handleBiometric} activeOpacity={0.75}>
              <Text style={s.bioIcon}>{bioType === 'Face ID' ? '🔑' : '👆'}</Text>
              <Text style={s.bioTxt}>Sign in with {bioType}</Text>
            </TouchableOpacity>
          )}

          <Text style={s.footer}>ASC DocTrack v1.0 · For official use only</Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const makeStyles = (C) => StyleSheet.create({
  screen:     { flex:1, backgroundColor:C.g900 },
  scroll:     { flexGrow:1 },
  hero:       { alignItems:'center', paddingTop:52, paddingBottom:36, paddingHorizontal:24 },
  logoBox:    { width:64, height:64, borderRadius:20, backgroundColor:'rgba(255,255,255,.12)', borderWidth:1.5, borderColor:'rgba(255,255,255,.18)', alignItems:'center', justifyContent:'center', marginBottom:14 },
  logoIcon:   { fontSize:30 },
  wordmark:   { fontSize:26, fontWeight:'700', color:'#fff', letterSpacing:-.5, marginBottom:6 },
  tagline:    { fontSize:12, color:'rgba(255,255,255,.4)', textAlign:'center', lineHeight:18 },
  sheet:      { backgroundColor:C.card, borderRadius:28, margin:16, padding:26, ...SHADOW.lg },
  heading:    { fontSize:22, fontWeight:'700', color:C.ink, letterSpacing:-.5, marginBottom:4 },
  sub:        { fontSize:13, color:C.ink3, marginBottom:24 },
  field:      { marginBottom:14 },
  fieldLabel: { fontSize:12, fontWeight:'500', color:C.ink2, marginBottom:6, letterSpacing:-.1 },
  inputWrap:  { flexDirection:'row', alignItems:'center', height:46, borderWidth:1.5, borderColor:C.brd, borderRadius:RADIUS.md, paddingHorizontal:12, backgroundColor:C.surf, gap:10 },
  inputError: { borderColor:C.red },
  fieldIcon:  { fontSize:16 },
  textIn:     { flex:1, fontSize:14, color:C.ink },
  errTxt:     { fontSize:11, color:C.red, marginTop:5 },
  bioBtn:     { flexDirection:'row', alignItems:'center', justifyContent:'center', gap:10, marginTop:14, padding:12, borderRadius:RADIUS.md, borderWidth:1.5, borderColor:C.brd },
  bioIcon:    { fontSize:22 },
  bioTxt:     { fontSize:14, fontWeight:'600', color:C.g800 },
  footer:     { fontSize:10, color:C.ink4, textAlign:'center', marginTop:18 },
});
