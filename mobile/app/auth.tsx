import { useRouter } from 'expo-router';
import React, { useState } from 'react';
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import { useServices } from '../src/data/context';
import { metric, type as t, useTone } from '../src/theme/tokens';

export default function Auth() {
  const tone = useTone();
  const router = useRouter();
  const { auth } = useServices();
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      if (sent) {
        await auth.verifyOtp(phone.trim(), code.trim());
        router.back();
      } else {
        await auth.requestOtp(phone.trim());
        setSent(true);
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  const field = [styles.field, { backgroundColor: tone.surface, color: tone.ink, borderColor: tone.hairline }];

  return (
    <View style={{ flex: 1, padding: metric.gutter }}>
      <Text style={[t.meta(12, '600', 0), { color: tone.chalk }]}>
        {sent ? 'Enter the code we sent' : 'A phone number is needed to report or confirm'}
      </Text>
      <TextInput
        style={field}
        value={phone}
        onChangeText={setPhone}
        keyboardType="phone-pad"
        placeholder="+91"
        placeholderTextColor={tone.chalk}
        editable={!sent}
      />
      {sent && (
        <TextInput
          style={field}
          value={code}
          onChangeText={setCode}
          keyboardType="number-pad"
          placeholder="SMS code"
          placeholderTextColor={tone.chalk}
        />
      )}
      {error && <Text style={[t.body(14), { color: tone.hazard, marginTop: 12 }]}>{error}</Text>}
      <Pressable
        disabled={busy}
        onPress={submit}
        style={[styles.cta, { backgroundColor: tone.accent, opacity: busy ? 0.5 : 1 }]}>
        <Text style={[t.display(16, '600'), { color: '#000' }]}>{sent ? 'Verify' : 'Send code'}</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  field: {
    height: 52, borderRadius: metric.radius, borderWidth: 1,
    paddingHorizontal: 14, marginTop: 12, fontSize: 18,
  },
  cta: { height: 50, borderRadius: metric.radius, alignItems: 'center', justifyContent: 'center', marginTop: 24 },
});
