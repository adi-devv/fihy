import React, { createContext, useContext, useMemo } from 'react';
import { ApiIssuesRepository } from './apiRepository';
import {
  FakeAuthGateway,
  FakeIssuesRepository,
  FixedLocationService,
  StubPhotoSource,
} from './fakeIssues';
import type { AuthGateway, IssuesRepository, LocationService, PhotoSource } from './repository';
import { ApiAuthGateway, CameraPhotoSource, DeviceLocationService } from './services';

export type Services = {
  issues: IssuesRepository;
  auth: AuthGateway;
  location: LocationService;
  photos: PhotoSource;
};

/** Demo mode runs the whole app on in-memory data: no API, no SMS, no camera. */
export const DEMO = process.env.EXPO_PUBLIC_DEMO === 'true';

export const demoServices = (over: Partial<Services> = {}): Services => {
  const auth = over.auth ?? new FakeAuthGateway();
  return {
    auth,
    issues: over.issues ?? new FakeIssuesRepository(undefined, auth),
    location: over.location ?? new FixedLocationService(),
    photos: over.photos ?? new StubPhotoSource(),
  };
};

export const liveServices = (): Services => ({
  issues: new ApiIssuesRepository(),
  auth: new ApiAuthGateway(),
  location: new DeviceLocationService(),
  photos: new CameraPhotoSource(process.env.EXPO_PUBLIC_PHOTO_SOURCE === 'library' ? 'library' : 'camera'),
});

const ServicesContext = createContext<Services | null>(null);

export function ServicesProvider({
  children,
  value,
}: {
  children: React.ReactNode;
  value?: Services;
}) {
  const services = useMemo(() => value ?? (DEMO ? demoServices() : liveServices()), [value]);
  return <ServicesContext.Provider value={services}>{children}</ServicesContext.Provider>;
}

export function useServices(): Services {
  const services = useContext(ServicesContext);
  if (!services) throw new Error('useServices must be used inside ServicesProvider');
  return services;
}
