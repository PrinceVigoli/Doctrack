/**
 * DocumentListScreen — search, filter by status/office/type, offline cache
 */
import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View, Text, StyleSheet, FlatList, TextInput,
  TouchableOpacity, RefreshControl, ScrollView,
} from 'react-native';
import { docsAPI, authAPI } from '../../api/services';
import { StatusBadge, AiBadge, EmptyState, LoadingOverlay } from '../../components';
import { useTheme, RADIUS, SHADOW } from '../../utils/theme';
import { useOffline } from '../../hooks/useOffline';
import { useAuth } from '../../context/AuthContext';
import { useNavigation } from '@react-navigation/native';

const STATUS_FILTERS = [
  { key:'',          label:'All'      },
  { key:'pending',   label:'Pending'  },
  { key:'in_review', label:'Review'   },
  { key:'approved',  label:'Approved' },
  { key:'completed', label:'Done'     },
  { key:'rejected',  label:'Rejected' },
];

export default function DocumentListScreen({ navigation, route }) {
  const C       = useTheme();
  const { user }= useAuth();
  const offline = useOffline();

  const initStatus = route?.params?.status || '';
  const [docs,       setDocs]       = useState([]);
  const [loading,    setLoading]    = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [search,     setSearch]     = useState('');
  const [statusF,    setStatusF]    = useState(initStatus);
  const [officeF,    setOfficeF]    = useState('');
  const [typeF,      setTypeF]      = useState('');
  const [offices,    setOffices]    = useState([]);
  const [docTypes,   setDocTypes]   = useState([]);
  const [page,       setPage]       = useState(1);
  const [hasMore,    setHasMore]    = useState(true);
  const [showFilters,setShowFilters]= useState(false);
  const [isOffline,  setIsOffline]  = useState(false);

  const debounceRef = useRef(null);

  useEffect(() => {
    (async () => {
      const [off, types] = await Promise.all([authAPI.offices(), docsAPI.types()]);
      setOffices(off.data.results ?? off.data);
      setDocTypes(types.data.results ?? types.data);
    })();
  }, []);

  const load = useCallback(async (reset = false) => {
    const p = reset ? 1 : page;
    const params = { page: p };
    if (search.trim()) params.search  = search.trim();
    if (statusF)       params.status  = statusF;
    if (officeF)       params.office  = officeF;
    if (typeF)         params.doc_type= typeF;

    try {
      const { data } = await docsAPI.list(params);
      const results  = data.results ?? data;
      if (reset) {
        setDocs(results);
        offline.saveCache(results);
        setPage(2);
      } else {
        setDocs(prev => [...prev, ...results]);
        setPage(p + 1);
      }
      setHasMore(!!data.next);
      setIsOffline(false);
    } catch {
      // Load from cache when offline
      const cached = await offline.loadCache();
      if (reset && cached.length) { setDocs(cached); setIsOffline(true); }
    }
  }, [page, search, statusF, officeF, typeF]);

  useEffect(() => {
    setLoading(true);
    load(true).finally(() => setLoading(false));
  }, [statusF, officeF, typeF]);

  const onSearchChange = (v) => {
    setSearch(v);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => load(true), 400);
  };

  const onRefresh = async () => { setRefreshing(true); await load(true); setRefreshing(false); };

  const s = makeStyles(C);
  const renderItem = ({ item }) => (
    <TouchableOpacity
      style={s.doc}
      activeOpacity={0.75}
      onPress={() => navigation.navigate('DocumentDetail', { id: item.id })}
    >
      <View style={s.docTop}>
        <Text style={s.trackNum}>{item.tracking_number}</Text>
        <StatusBadge status={item.status} />
      </View>
      <Text style={s.docTitle} numberOfLines={2}>{item.title}</Text>
      <View style={s.docMeta}>
        <View style={s.officeTag}>
          <Text style={s.officeIcon}>🏢</Text>
          <Text style={s.officeName} numberOfLines={1}>{item.current_office?.name || '—'}</Text>
        </View>
        <Text style={s.docDate}>
          {new Date(item.created_at).toLocaleDateString('en-PH',{month:'short',day:'numeric'})}
        </Text>
      </View>
      {item.ai_label && (
        <AiBadge label={item.ai_label} confidence={item.ai_confidence} />
      )}
    </TouchableOpacity>
  );

  if (loading) return <LoadingOverlay />;

  return (
    <View style={s.screen}>
      {/* Offline banner */}
      {isOffline && (
        <View style={s.offlineBanner}>
          <Text style={s.offlineTxt}>⚠️ Offline — showing cached documents</Text>
        </View>
      )}

      {/* Top bar */}
      <View style={s.topbar}>
        <View style={s.topbarRow}>
          <Text style={s.pageTitle}>Documents</Text>
          <View style={s.topbarRight}>
            <TouchableOpacity style={s.filterToggle} onPress={() => setShowFilters(v=>!v)}>
              <Text style={s.filterToggleIcon}>⚙️</Text>
              {(officeF || typeF) && <View style={s.filterBadge} />}
            </TouchableOpacity>
            <TouchableOpacity style={s.addBtn} onPress={() => navigation.navigate('SubmitDocument')}>
              <Text style={s.addIcon}>＋</Text>
            </TouchableOpacity>
          </View>
        </View>
        <View style={s.search}>
          <Text style={s.searchIcon}>🔍</Text>
          <TextInput style={s.searchInput} placeholder="Search documents..."
            placeholderTextColor={C.ink4} value={search} onChangeText={onSearchChange} returnKeyType="search" />
          {search.length > 0 && (
            <TouchableOpacity onPress={() => { setSearch(''); load(true); }}>
              <Text style={{ color:C.ink4, fontSize:16 }}>✕</Text>
            </TouchableOpacity>
          )}
        </View>
      </View>

      {/* Expanded filters */}
      {showFilters && (
        <View style={s.filterPanel}>
          <Text style={s.filterLabel}>Office</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom:10 }}>
            <View style={{ flexDirection:'row', gap:6 }}>
              <TouchableOpacity style={[s.fpill, !officeF && s.fpillOn]} onPress={() => setOfficeF('')}>
                <Text style={[s.fpillTxt, !officeF && s.fpillTxtOn]}>All</Text>
              </TouchableOpacity>
              {offices.map(o => (
                <TouchableOpacity key={o.id} style={[s.fpill, officeF===String(o.id) && s.fpillOn]}
                  onPress={() => setOfficeF(officeF===String(o.id) ? '' : String(o.id))}>
                  <Text style={[s.fpillTxt, officeF===String(o.id) && s.fpillTxtOn]}>{o.code}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </ScrollView>
          <Text style={s.filterLabel}>Document type</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            <View style={{ flexDirection:'row', gap:6 }}>
              <TouchableOpacity style={[s.fpill, !typeF && s.fpillOn]} onPress={() => setTypeF('')}>
                <Text style={[s.fpillTxt, !typeF && s.fpillTxtOn]}>All</Text>
              </TouchableOpacity>
              {docTypes.map(t => (
                <TouchableOpacity key={t.id} style={[s.fpill, typeF===String(t.id) && s.fpillOn]}
                  onPress={() => setTypeF(typeF===String(t.id) ? '' : String(t.id))}>
                  <Text style={[s.fpillTxt, typeF===String(t.id) && s.fpillTxtOn]}>{t.name}</Text>
                </TouchableOpacity>
              ))}
            </View>
          </ScrollView>
        </View>
      )}

      {/* Status pills */}
      <FlatList
        data={STATUS_FILTERS} horizontal showsHorizontalScrollIndicator={false}
        keyExtractor={f => f.key} contentContainerStyle={s.filterRow}
        renderItem={({ item: f }) => (
          <TouchableOpacity style={[s.pill, statusF===f.key && s.pillOn]}
            onPress={() => setStatusF(f.key)} activeOpacity={0.75}>
            <Text style={[s.pillTxt, statusF===f.key && s.pillTxtOn]}>{f.label}</Text>
          </TouchableOpacity>
        )}
      />

      {/* Doc list */}
      <FlatList
        data={docs} keyExtractor={d => String(d.id)} renderItem={renderItem}
        contentContainerStyle={s.list}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={C.g800} />}
        onEndReached={() => hasMore && !isOffline && load()}
        onEndReachedThreshold={0.4}
        showsVerticalScrollIndicator={false}
        ListEmptyComponent={
          <EmptyState icon="📭" title="No documents found" subtitle="Try adjusting your search or filters." />
        }
      />

      {/* QR scan FAB */}
      <TouchableOpacity style={s.qrFab} onPress={() => navigation.navigate('QRScanner')} activeOpacity={0.85}>
        <Text style={s.qrFabIcon}>⊞</Text>
      </TouchableOpacity>
    </View>
  );
}

const makeStyles = (C) => StyleSheet.create({
  screen:         { flex:1, backgroundColor:C.surf },
  offlineBanner:  { backgroundColor:C.amberBg, padding:10, alignItems:'center', borderBottomWidth:1, borderBottomColor:'#FCD34D' },
  offlineTxt:     { fontSize:12, fontWeight:'600', color:C.amberDk },
  topbar:         { backgroundColor:C.card, paddingHorizontal:18, paddingTop:16, paddingBottom:12, borderBottomWidth:1, borderBottomColor:C.brd2 },
  topbarRow:      { flexDirection:'row', alignItems:'center', justifyContent:'space-between', marginBottom:12 },
  pageTitle:      { fontSize:22, fontWeight:'700', color:C.ink, letterSpacing:-.5 },
  topbarRight:    { flexDirection:'row', gap:8 },
  filterToggle:   { width:34, height:34, borderRadius:10, backgroundColor:C.surf, borderWidth:1.5, borderColor:C.brd, alignItems:'center', justifyContent:'center' },
  filterToggleIcon:{ fontSize:16 },
  filterBadge:    { position:'absolute', top:5, right:5, width:7, height:7, borderRadius:4, backgroundColor:C.red },
  addBtn:         { width:34, height:34, borderRadius:10, backgroundColor:C.g900, alignItems:'center', justifyContent:'center' },
  addIcon:        { fontSize:20, color:'#fff', lineHeight:24 },
  search:         { flexDirection:'row', alignItems:'center', gap:8, backgroundColor:C.surf, borderWidth:1, borderColor:C.brd, borderRadius:RADIUS.md, paddingHorizontal:12, height:40 },
  searchIcon:     { fontSize:15 },
  searchInput:    { flex:1, fontSize:14, color:C.ink },
  filterPanel:    { backgroundColor:C.card, padding:14, borderBottomWidth:1, borderBottomColor:C.brd2 },
  filterLabel:    { fontSize:11, fontWeight:'600', color:C.ink3, textTransform:'uppercase', letterSpacing:.06, marginBottom:8 },
  fpill:          { paddingHorizontal:12, paddingVertical:5, borderRadius:RADIUS.pill, backgroundColor:C.surf, borderWidth:1.5, borderColor:C.brd },
  fpillOn:        { backgroundColor:C.g900, borderColor:C.g900 },
  fpillTxt:       { fontSize:11, color:C.ink3, fontWeight:'500' },
  fpillTxtOn:     { color:'#fff', fontWeight:'600' },
  filterRow:      { paddingHorizontal:16, paddingVertical:10, gap:7 },
  pill:           { paddingHorizontal:16, paddingVertical:7, borderRadius:RADIUS.pill, backgroundColor:C.card, borderWidth:1.5, borderColor:C.brd },
  pillOn:         { backgroundColor:C.g900, borderColor:C.g900 },
  pillTxt:        { fontSize:12, color:C.ink3, fontWeight:'500', letterSpacing:.02 },
  pillTxtOn:      { color:'#fff', fontWeight:'600' },
  list:           { padding:16, paddingBottom:100, gap:10 },
  doc:            { backgroundColor:C.card, borderRadius:18, padding:16, borderWidth:1, borderColor:C.brd2, ...SHADOW.sm },
  docTop:         { flexDirection:'row', justifyContent:'space-between', alignItems:'center', marginBottom:8 },
  trackNum:       { fontSize:10, color:C.ink4, fontFamily:'monospace', fontWeight:'600', letterSpacing:.06 },
  docTitle:       { fontSize:14, fontWeight:'600', color:C.ink, lineHeight:20, letterSpacing:-.2, marginBottom:8 },
  docMeta:        { flexDirection:'row', alignItems:'center', justifyContent:'space-between', marginBottom:6 },
  officeTag:      { flexDirection:'row', alignItems:'center', gap:5, flex:1, marginRight:8 },
  officeIcon:     { fontSize:12 },
  officeName:     { fontSize:11, color:C.ink3, flex:1 },
  docDate:        { fontSize:11, color:C.ink4 },
  qrFab:          { position:'absolute', bottom:20, right:20, width:54, height:54, borderRadius:27, backgroundColor:C.g900, alignItems:'center', justifyContent:'center', ...SHADOW.lg },
  qrFabIcon:      { fontSize:24, color:'#fff' },
});
