# fihy

Fix India, Heck Yeah — report and independently confirm public civic issues.

## Layout

```
mobile/    React Native (Expo) app
backend/   FastAPI service
```

Each side is developed independently against the API contract in
`docs/api-contract.md`.

## Running the app

```bash
cd mobile
npm run demo     # in-memory data, no backend, no SMS, no camera
npm start        # against EXPO_PUBLIC_API_URL
```

Press `i` for the iOS simulator, or scan the QR code with Expo Go to run on a
physical device — Expo Go ships from the App Store, so it needs no local Xcode
toolchain and works on current iOS.
