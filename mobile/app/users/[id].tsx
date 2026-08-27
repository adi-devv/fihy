import { useLocalSearchParams } from 'expo-router';
import React from 'react';
import { ProfileScreen } from '../../src/features/profile/ProfileScreen';

export default function UserProfile() {
  const { id } = useLocalSearchParams<{ id: string }>();
  return <ProfileScreen userId={id!} />;
}
