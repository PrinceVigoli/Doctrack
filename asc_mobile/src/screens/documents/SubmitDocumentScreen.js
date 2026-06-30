/**
 * SubmitDocumentScreen — real file picker, AI analysis, prefill from scanner
 */
import React, { useState, useEffect, useRef } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  Alert, Platform, KeyboardAvoidingView, ActivityIndicator,
} from 'react-native';
import * as DocumentPicker from 'expo-document-picker';
import { docsAPI, authAPI } from '../../api/services';
import { Button, Input } from '../../components';
import { useTheme, RADIUS, SHADOW } from '../../utils/theme';

const PRIORITIES  = ['low','normal','high','urgent'];
const COMM_TYPES  = [
  { key:'n/a',      label:'N/A'      },
  { key:'internal', label:'Internal' },
  { key:'external', label:'External' },
];
const CONF_LEVELS = [
  { key:'public',     label:'Public',     desc:'All employees can view & download' },
  { key:'internal',   label:'Internal',   desc:'Employees can view, not download'  },
  { key:'restricted', label:'Restricted', desc:'Records Office only'               },
];
const PRIORITY_COLOR = { low:'#9CA3AF', normal:'#2563EB', high:'#D97706', urgent:'#DC2626' };

export default function SubmitDocumentScreen({ navigation, route }) {
  const C        = useTheme();
  const prefill  = route?.params?.prefill;
  const [form, setForm] = useState({
    title:         prefill?.title        || '',
    description:   prefill?.description  || '',
    priority:      prefill?.priority     || 'normal',
    comm_type:     prefill?.comm_type    || 'n/a',
    confidentiality: 'internal',
    doc_type_id:   null,
    destination_office_id: null,
    due_date:      '',
  });
  const [file,      setFile]     = useState(null);
  const [offices,   setOffices]  = useState([]);
  const [docTypes,  setDocTypes] = useState([]);
  const [loading,   setLoading]  = useState(false);
  const [errors,    setErrors]   = useState({});
  const [dupResult, setDupResult]= useState(null);
  const [aiLoading, setAiLoading]= useState(false);
  const debRef = useRef(null);

  useEffect(() => {
    (async () => {
      const [off, types] = await Promise.all([authAPI.offices(), docsAPI.types()]);
      setOffices(off.data.results ?? off.data);
      setDocTypes(types.data.results ?? types.data);
    })();
  }, []);

  // Show prefill notice
  useEffect(() => {
    if (prefill?.doc_type_name) {
      const match = docTypes.find(t => t.name === prefill.doc_type_name);
      if (match) set('doc_type_id', match.id);
    }
  }, [docTypes, prefill]);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  // Real file picker
  const pickFile = async () => {
    try {
      const res = await DocumentPicker.getDocumentAsync({
        type: ['application/pdf','application/msword',
               'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
               'image/jpeg','image/png'],
        copyToCacheDirectory: true,
      });
      if (!res.canceled && res.assets?.[0]) {
        setFile(res.assets[0]);
        setErrors(e => ({ ...e, file:'' }));
      }
    } catch { Alert.alert('Error', 'Could not open file picker.'); }
  };

  // Debounced duplicate check
  const onTitleChange = (v) => {
    set('title', v);
    clearTimeout(debRef.current);
    debRef.current = setTimeout(async () => {
      if (!v.trim()) { setDupResult(null); return; }
      setAiLoading(true);
      try {
        const { data } = await docsAPI.checkDuplicate({ title:v, description:form.description });
        setDupResult(data);
      } catch {}
      setAiLoading(false);
    }, 800);
  };

  const validate = () => {
    const e = {};
    if (!form.title.trim()) e.title = 'Title is required.';
    if (!file)              e.file  = 'Please attach a file.';
    setErrors(e);
    return !Object.keys(e).length;
  };

  const handleSubmit = async () => {
    if (!validate()) return;
    if (dupResult?.is_duplicate) {
      return Alert.alert('⚠️ Possible duplicate', dupResult.message, [
        { text:'Cancel', style:'cancel' },
        { text:'Submit anyway', onPress: doSubmit },
      ]);
    }
    await doSubmit();
  };

  const doSubmit = async () => {
    setLoading(true);
    try {
      const fd = new FormData();
      Object.entries(form).forEach(([k, v]) => { if (v) fd.append(k, String(v)); });
      fd.append('file', {
        uri:  file.uri,
        name: file.name,
        type: file.mimeType || 'application/octet-stream',
      });
      const { data } = await docsAPI.submit(fd);
      Alert.alert('✅ Submitted', `Tracking: ${data.tracking_number}\nAI: ${data.ai_label || '—'}\nPriority: ${data.priority}`,
        [{ text:'View', onPress:() => navigation.replace('DocumentDetail', { id: data.id }) }]);
    } catch (e) {
      Alert.alert('Error', e.response?.data ? JSON.stringify(e.response.data) : 'Submission failed.');
    } finally { setLoading(false); }
  };

  const s = makeStyles(C);
  return (
    <KeyboardAvoidingView style={{ flex:1 }} behavior={Platform.OS==='ios'?'padding':undefined}>
      <ScrollView style={s.screen} contentContainerStyle={s.content} keyboardShouldPersistTaps="handled">
        <Text style={s.pageTitle}>Submit document</Text>
        {prefill && (
          <View style={s.prefillBanner}>
            <Text style={s.prefillTxt}>📄 Pre-filled from scanner — review and submit</Text>
          </View>
        )}

        {/* Real file picker */}
        <TouchableOpacity style={[s.filePicker, file&&s.filePickerDone, errors.file&&s.filePickerErr]}
          onPress={pickFile} activeOpacity={0.7}>
          <Text style={s.fileEmoji}>{file ? '📄' : '📎'}</Text>
          <View style={{ flex:1 }}>
            <Text style={[s.fileLabel, file&&{color:C.g700}]}>{file ? file.name : 'Tap to attach a file'}</Text>
            <Text style={s.fileSub}>{file ? `${((file.size||0)/1024).toFixed(0)} KB` : 'PDF, DOCX, JPG, PNG'}</Text>
          </View>
          {file && <Text style={{ fontSize:18, color:C.g700 }}>✓</Text>}
        </TouchableOpacity>
        {errors.file && <Text style={s.errTxt}>{errors.file}</Text>}

        <Input label="Document title *" placeholder="e.g. Research Proposal on AI Integration"
          value={form.title} onChangeText={onTitleChange} error={errors.title} />

        {/* Duplicate warning */}
        {aiLoading && <View style={s.aiRow}><ActivityIndicator size="small" color={C.g700} /><Text style={s.aiTxt}>Checking for duplicates...</Text></View>}
        {dupResult?.is_duplicate && !aiLoading && (
          <View style={s.warnCard}>
            <Text style={s.warnTitle}>⚠️ Possible duplicate</Text>
            <Text style={s.warnTxt}>{dupResult.message}</Text>
          </View>
        )}

        <Input label="Description (optional)" placeholder="Brief description — helps AI classify"
          value={form.description} onChangeText={v => set('description',v)}
          multiline style={{ height:80, textAlignVertical:'top', paddingTop:10 }} />

        <Input label="Due date (optional)" placeholder="YYYY-MM-DD"
          value={form.due_date} onChangeText={v => set('due_date',v)} />

        {/* Priority */}
        <Text style={s.sLbl}>Priority</Text>
        <View style={s.pillRow}>
          {PRIORITIES.map(p => (
            <TouchableOpacity key={p} style={[s.pill, form.priority===p && { backgroundColor:PRIORITY_COLOR[p], borderColor:PRIORITY_COLOR[p] }]}
              onPress={() => set('priority',p)} activeOpacity={0.75}>
              <Text style={[s.pillTxt, form.priority===p && { color:'#fff' }]}>{p}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Communication type */}
        <Text style={s.sLbl}>Communication type</Text>
        <View style={s.pillRow}>
          {COMM_TYPES.map(c => (
            <TouchableOpacity key={c.key} style={[s.pill, form.comm_type===c.key && s.pillOn]}
              onPress={() => set('comm_type',c.key)} activeOpacity={0.75}>
              <Text style={[s.pillTxt, form.comm_type===c.key && s.pillTxtOn]}>{c.label}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Confidentiality */}
        <Text style={s.sLbl}>Confidentiality</Text>
        {CONF_LEVELS.map(c => (
          <TouchableOpacity key={c.key} style={[s.confOpt, form.confidentiality===c.key && s.confOptOn]}
            onPress={() => set('confidentiality',c.key)} activeOpacity={0.75}>
            <View style={[s.radio, form.confidentiality===c.key && s.radioOn]}>
              {form.confidentiality===c.key && <View style={s.radioDot} />}
            </View>
            <View>
              <Text style={s.confLabel}>{c.label}</Text>
              <Text style={s.confDesc}>{c.desc}</Text>
            </View>
          </TouchableOpacity>
        ))}

        {/* Document type */}
        {docTypes.length > 0 && (
          <>
            <Text style={s.sLbl}>Document type</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom:16 }}>
              <View style={s.pillRow}>
                {docTypes.map(t => (
                  <TouchableOpacity key={t.id} style={[s.pill, form.doc_type_id===t.id && s.pillOn]}
                    onPress={() => set('doc_type_id', form.doc_type_id===t.id ? null : t.id)} activeOpacity={0.75}>
                    <Text style={[s.pillTxt, form.doc_type_id===t.id && s.pillTxtOn]}>{t.name}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </ScrollView>
          </>
        )}

        {/* Destination office */}
        {offices.length > 0 && (
          <>
            <Text style={s.sLbl}>Send to office (optional)</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom:16 }}>
              <View style={s.pillRow}>
                {offices.map(o => (
                  <TouchableOpacity key={o.id} style={[s.pill, form.destination_office_id===o.id && s.pillOn, o.is_records_office && { borderColor:C.g700 }]}
                    onPress={() => set('destination_office_id', form.destination_office_id===o.id ? null : o.id)} activeOpacity={0.75}>
                    <Text style={[s.pillTxt, form.destination_office_id===o.id && s.pillTxtOn]}>{o.code}</Text>
                  </TouchableOpacity>
                ))}
              </View>
            </ScrollView>
          </>
        )}

        <Button title="Submit document" onPress={handleSubmit} loading={loading} style={{ marginTop:8 }} />
        <Button title="Cancel" variant="outline" onPress={() => navigation.goBack()} style={{ marginTop:10, marginBottom:40 }} />
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const makeStyles = (C) => StyleSheet.create({
  screen:        { flex:1, backgroundColor:C.surf },
  content:       { padding:20 },
  pageTitle:     { fontSize:22, fontWeight:'700', color:C.ink, letterSpacing:-.5, marginBottom:16 },
  prefillBanner: { backgroundColor:C.g50, borderRadius:RADIUS.md, padding:12, marginBottom:16, borderWidth:1, borderColor:C.g200 },
  prefillTxt:    { fontSize:12, color:C.g700, fontWeight:'500' },
  filePicker:    { flexDirection:'row', alignItems:'center', gap:12, borderWidth:1.5, borderColor:C.brd, borderStyle:'dashed', borderRadius:RADIUS.lg, padding:16, marginBottom:6, backgroundColor:C.card },
  filePickerDone:{ borderColor:C.g600, borderStyle:'solid', backgroundColor:C.g50 },
  filePickerErr: { borderColor:C.red },
  fileEmoji:     { fontSize:28 },
  fileLabel:     { fontSize:14, fontWeight:'600', color:C.ink2 },
  fileSub:       { fontSize:11, color:C.ink4, marginTop:2 },
  errTxt:        { fontSize:11, color:C.red, marginBottom:10 },
  aiRow:         { flexDirection:'row', alignItems:'center', gap:8, marginBottom:10 },
  aiTxt:         { fontSize:12, color:C.g700 },
  warnCard:      { backgroundColor:C.amberBg, borderRadius:RADIUS.md, padding:12, marginBottom:14, borderWidth:1, borderColor:'#FCD34D' },
  warnTitle:     { fontSize:13, fontWeight:'700', color:C.amberDk, marginBottom:4 },
  warnTxt:       { fontSize:12, color:C.amberDk, lineHeight:17 },
  sLbl:          { fontSize:12, fontWeight:'500', color:C.ink2, marginBottom:8, marginTop:4 },
  pillRow:       { flexDirection:'row', flexWrap:'wrap', gap:8, marginBottom:16 },
  pill:          { paddingHorizontal:14, paddingVertical:8, borderRadius:RADIUS.pill, backgroundColor:C.card, borderWidth:1.5, borderColor:C.brd },
  pillOn:        { backgroundColor:C.g900, borderColor:C.g900 },
  pillTxt:       { fontSize:12, color:C.ink3, fontWeight:'500' },
  pillTxtOn:     { color:'#fff', fontWeight:'600' },
  confOpt:       { flexDirection:'row', alignItems:'center', gap:12, padding:12, borderRadius:RADIUS.md, backgroundColor:C.card, borderWidth:1.5, borderColor:C.brd2, marginBottom:8 },
  confOptOn:     { borderColor:C.g700, backgroundColor:C.g50 },
  radio:         { width:18, height:18, borderRadius:9, borderWidth:2, borderColor:C.brd2, alignItems:'center', justifyContent:'center', flexShrink:0 },
  radioOn:       { borderColor:C.g700 },
  radioDot:      { width:8, height:8, borderRadius:4, backgroundColor:C.g700 },
  confLabel:     { fontSize:13, fontWeight:'600', color:C.ink },
  confDesc:      { fontSize:11, color:C.ink3, marginTop:1 },
});
