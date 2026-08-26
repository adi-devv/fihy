import { useRouter } from 'expo-router';
import { Camera, Check, ChevronRight, CircleCheck, MapPin, X } from 'lucide-react-native';
import React, { useState } from 'react';
import {
  Alert, Dimensions, Image, Modal, Pressable, ScrollView, StyleSheet, Text, TextInput, View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useServices } from '../src/data/context';
import { CATEGORIES, SEVERITIES, categoryLabel, severityLabel } from '../src/domain/issue';
import type { Category, Severity } from '../src/domain/issue';
import { CategoryGlyph } from '../src/features/issues/glyphs';
import { metric, type as t, useTone } from '../src/theme/tokens';

const uuid = () =>
  'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
  });

/** The backend still wants a short title; one composer field feeds both, with
 *  the title clipped to the 140-char limit. */
const titleFrom = (caption: string) => {
  const text = caption.trim();
  if (text.length <= 140) return text;
  const cut = text.lastIndexOf(' ', 137);
  return `${text.slice(0, cut > 20 ? cut : 137).trimEnd()}…`;
};

export default function Report() {
  const tone = useTone();
  const router = useRouter();
  const { auth, issues, location, photos } = useServices();
  const [caption, setCaption] = useState('');
  const [category, setCategory] = useState<Category>('pothole_road');
  const [severity, setSeverity] = useState<Severity>('medium');
  const [attached, setAttached] = useState<string[]>([]);
  const [busy, setBusy] = useState(false);
  const [sheet, setSheet] = useState<null | 'category' | 'severity'>(null);

  const addPhoto = async () => {
    try {
      const uri = await photos.capture();
      if (uri) setAttached((prev) => [...prev, uri]);
    } catch (e) {
      Alert.alert('Could not add photo', (e as Error).message);
    }
  };

  const publish = async () => {
    if (!auth.currentUserId()) return router.push('/auth');
    if (!attached.length || caption.trim().length < 3) {
      Alert.alert('Add a photo and describe what is wrong.');
      return;
    }
    setBusy(true);
    try {
      const point = await location.current();
      const created = await issues.create({
        client_report_id: uuid(),
        title: titleFrom(caption),
        description: caption.trim(),
        category,
        severity,
        latitude: point.latitude,
        longitude: point.longitude,
        photos: attached,
      });
      router.replace(`/issues/${created.id}`);
    } catch (e) {
      Alert.alert('Could not publish', (e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const preview = attached.at(-1);
  const wellHeight = Dimensions.get('window').height * 0.44;

  return (
    <SafeAreaView style={{ flex: 1, backgroundColor: tone.bg }}>
      <View style={[styles.bar, { borderBottomColor: tone.hairline }]}>
        <Pressable onPress={() => router.back()} hitSlop={10}>
          <X size={24} color={tone.ink} />
        </Pressable>
        <Text style={[t.display(18, '600'), { color: tone.ink }]}>New report</Text>
        <Pressable
          disabled={busy}
          onPress={publish}
          style={[styles.publish, { backgroundColor: tone.accent, opacity: busy ? 0.5 : 1 }]}>
          <Text style={[t.display(15, '600'), { color: '#000' }]}>
            {busy ? 'Publishing' : 'Publish'}
          </Text>
        </Pressable>
      </View>

      <ScrollView keyboardShouldPersistTaps="handled">
        <Pressable onPress={addPhoto} style={{ height: wellHeight, backgroundColor: tone.surface }}>
          {preview && !preview.startsWith('demo://') ? (
            <Image source={{ uri: preview }} style={{ flex: 1 }} resizeMode="cover" />
          ) : (
            <View style={styles.well}>
              {attached.length ? (
                <CircleCheck size={40} color={tone.accentDeep} />
              ) : (
                <Camera size={40} color={tone.ink} />
              )}
              <Text style={[t.display(15, '500'), { color: tone.ink, marginTop: 12 }]}>
                {attached.length
                  ? `${attached.length} photo${attached.length === 1 ? '' : 's'} attached`
                  : 'Tap to take a photo'}
              </Text>
              <Text style={[t.meta(11, '500', 0.6), { color: tone.chalk, marginTop: 4 }]}>
                {attached.length ? 'Tap to add another' : 'A photo is required'}
              </Text>
            </View>
          )}
        </Pressable>

        <TextInput
          style={[styles.caption, { color: tone.ink }]}
          value={caption}
          onChangeText={setCaption}
          multiline
          maxLength={2000}
          placeholder="What is wrong here?"
          placeholderTextColor={tone.chalk}
        />

        <Divider />
        <Row
          leading={<CategoryGlyph category={category} size={20} color={tone.ink} />}
          label="Category"
          value={categoryLabel[category]}
          onPress={() => setSheet('category')}
        />
        <Divider />
        <Row
          leading={
            <View
              style={[
                styles.dot,
                { backgroundColor: severity === 'high' ? tone.hazard : severity === 'medium' ? tone.ink : tone.chalk },
              ]}
            />
          }
          label="Severity"
          value={severityLabel[severity]}
          onPress={() => setSheet('severity')}
        />
        <Divider />
        <Row
          leading={<MapPin size={20} color={tone.chalk} />}
          label="Location"
          value="Added when you publish"
        />
        <Text style={[t.meta(11, '500', 0.6), { color: tone.chalk, padding: metric.gutter }]}>
          This location will be public.
        </Text>
      </ScrollView>

      <Sheet
        visible={sheet !== null}
        onClose={() => setSheet(null)}
        title={sheet === 'severity' ? 'Severity' : 'Category'}
        options={
          sheet === 'severity'
            ? SEVERITIES.map((v) => ({ value: v, label: severityLabel[v], selected: v === severity }))
            : CATEGORIES.map((v) => ({ value: v, label: categoryLabel[v], selected: v === category }))
        }
        onPick={(value) => {
          if (sheet === 'severity') setSeverity(value as Severity);
          else setCategory(value as Category);
          setSheet(null);
        }}
      />
    </SafeAreaView>
  );
}

function Divider() {
  const tone = useTone();
  return <View style={{ height: 1, backgroundColor: tone.hairline }} />;
}

function Row({
  leading, label, value, onPress,
}: { leading: React.ReactNode; label: string; value: string; onPress?: () => void }) {
  const tone = useTone();
  return (
    <Pressable onPress={onPress} style={styles.row}>
      <View style={{ width: 22, alignItems: 'center' }}>{leading}</View>
      <Text style={[t.display(15, '500'), { color: tone.ink, marginLeft: 12 }]}>{label}</Text>
      <View style={{ flex: 1 }} />
      <Text style={[t.body(15), { color: tone.chalk }]}>{value}</Text>
      {onPress && <ChevronRight size={17} color={tone.chalk} style={{ marginLeft: 6 }} />}
    </Pressable>
  );
}

function Sheet({
  visible, onClose, title, options, onPick,
}: {
  visible: boolean;
  onClose: () => void;
  title: string;
  options: { value: string; label: string; selected: boolean }[];
  onPick: (value: string) => void;
}) {
  const tone = useTone();
  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose} />
      <View style={[styles.sheet, { backgroundColor: tone.bg }]}>
        <Text style={[t.display(16, '600'), { color: tone.ink, textAlign: 'center', marginBottom: 8 }]}>
          {title}
        </Text>
        <ScrollView>
          {options.map((option) => (
            <Pressable key={option.value} style={styles.row} onPress={() => onPick(option.value)}>
              <Text style={[t.body(16), { color: tone.ink, flex: 1 }]}>{option.label}</Text>
              {option.selected && <Check size={18} color={tone.accentDeep} />}
            </Pressable>
          ))}
        </ScrollView>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  bar: {
    flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between',
    paddingHorizontal: metric.gutter, paddingVertical: 10, borderBottomWidth: 1,
  },
  publish: { paddingHorizontal: 20, height: 36, borderRadius: 18, alignItems: 'center', justifyContent: 'center' },
  well: { flex: 1, alignItems: 'center', justifyContent: 'center' },
  caption: {
    paddingHorizontal: metric.gutter, paddingTop: 16, paddingBottom: 8,
    fontSize: 17, minHeight: 72, textAlignVertical: 'top',
  },
  row: { flexDirection: 'row', alignItems: 'center', paddingHorizontal: metric.gutter, paddingVertical: 15 },
  dot: { width: 10, height: 10, borderRadius: 5 },
  backdrop: { flex: 1, backgroundColor: 'rgba(0,0,0,0.4)' },
  sheet: { maxHeight: '60%', paddingTop: 14, borderTopLeftRadius: 18, borderTopRightRadius: 18 },
});
