# Deployment Guide
## AISJ Connect - App Store & Play Store Submission

---

## Pre-Deployment Checklist

### Backend Deployment

- [ ] Set production environment variables
- [ ] Configure MongoDB Atlas or production database
- [ ] Enable HTTPS/SSL certificates
- [ ] Set up domain and DNS
- [ ] Configure CORS for production domains
- [ ] Set up logging and monitoring (Datadog, Sentry)
- [ ] Configure backup strategy
- [ ] Run database migrations
- [ ] Create initial admin accounts

### Mobile App Preparation

- [ ] Update `app.json` with production values
- [ ] Generate production signing keys
- [ ] Configure push notification credentials
- [ ] Test all features in release mode
- [ ] Verify biometric authentication works
- [ ] Test offline functionality
- [ ] Verify QR code scanning

---

## Environment Configuration

### Backend Environment Variables

```env
# Production Environment
ENVIRONMENT=production
DEBUG=false

# Database
MONGODB_URL=mongodb+srv://user:password@cluster.mongodb.net/aisj_connect
DATABASE_NAME=aisj_connect

# JWT Security
JWT_SECRET_KEY=<generate-secure-256-bit-key>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_HOURS=24

# Admin Whitelist
SUPER_ADMIN_EMAILS=admin@school.edu,security@school.edu

# Rate Limiting
RATE_LIMIT_ENABLED=true

# CORS
ALLOWED_ORIGINS=https://app.school.edu,https://admin.school.edu

# Push Notifications
FIREBASE_PROJECT_ID=your-project-id
FIREBASE_PRIVATE_KEY=<base64-encoded-key>
FIREBASE_CLIENT_EMAIL=firebase-adminsdk@project.iam.gserviceaccount.com

APNS_KEY_ID=your-key-id
APNS_TEAM_ID=your-team-id
APNS_BUNDLE_ID=com.school.aisjconnect
```

### Frontend Environment (app.json)

```json
{
  "expo": {
    "name": "AISJ Connect",
    "slug": "aisj-connect",
    "version": "1.0.0",
    "orientation": "portrait",
    "icon": "./assets/images/icon.png",
    "scheme": "aisjconnect",
    "splash": {
      "image": "./assets/images/splash.png",
      "resizeMode": "contain",
      "backgroundColor": "#1E3A5F"
    },
    "ios": {
      "supportsTablet": true,
      "bundleIdentifier": "com.school.aisjconnect",
      "buildNumber": "1",
      "infoPlist": {
        "NSCameraUsageDescription": "Camera is used to scan QR codes on ID cards",
        "NSFaceIDUsageDescription": "Face ID is used to protect your digital ID card"
      }
    },
    "android": {
      "adaptiveIcon": {
        "foregroundImage": "./assets/images/adaptive-icon.png",
        "backgroundColor": "#1E3A5F"
      },
      "package": "com.school.aisjconnect",
      "versionCode": 1,
      "permissions": [
        "CAMERA",
        "USE_BIOMETRIC",
        "USE_FINGERPRINT",
        "RECEIVE_BOOT_COMPLETED",
        "VIBRATE"
      ]
    },
    "plugins": [
      "expo-camera",
      "expo-local-authentication",
      [
        "expo-notifications",
        {
          "icon": "./assets/images/notification-icon.png",
          "color": "#1E3A5F"
        }
      ]
    ],
    "extra": {
      "apiUrl": "https://api.school.edu",
      "eas": {
        "projectId": "your-eas-project-id"
      }
    }
  }
}
```

---

## Build Commands

### Development Build

```bash
# iOS Simulator
npx expo run:ios

# Android Emulator
npx expo run:android
```

### Production Build with EAS

```bash
# Install EAS CLI
npm install -g eas-cli

# Login to Expo
eas login

# Configure project
eas build:configure

# Build for iOS App Store
eas build --platform ios --profile production

# Build for Google Play Store
eas build --platform android --profile production
```

### EAS Build Configuration (eas.json)

```json
{
  "cli": {
    "version": ">= 3.0.0"
  },
  "build": {
    "development": {
      "developmentClient": true,
      "distribution": "internal",
      "ios": {
        "simulator": true
      }
    },
    "preview": {
      "distribution": "internal"
    },
    "production": {
      "autoIncrement": true,
      "ios": {
        "resourceClass": "m-medium"
      },
      "android": {
        "buildType": "app-bundle"
      }
    }
  },
  "submit": {
    "production": {
      "ios": {
        "appleId": "developer@school.edu",
        "ascAppId": "1234567890",
        "appleTeamId": "TEAM_ID"
      },
      "android": {
        "serviceAccountKeyPath": "./google-play-key.json",
        "track": "internal"
      }
    }
  }
}
```

---

## App Store Submission (iOS)

### Requirements

1. **Apple Developer Account** ($99/year)
2. **App Store Connect** account setup
3. **Signing certificates** and provisioning profiles

### App Store Information

```
App Name: AISJ Connect
Subtitle: School Digital ID & Safety
Category: Education
Age Rating: 4+
Privacy Policy URL: https://school.edu/privacy
Support URL: https://school.edu/support
```

### Screenshots Required

- iPhone 6.7" (1290 x 2796)
- iPhone 6.5" (1284 x 2778)
- iPhone 5.5" (1242 x 2208)
- iPad Pro 12.9" (2048 x 2732)

### App Review Notes

```
Demo Account:
Email: demo@school.edu
Password: DemoPass123!

Testing Notes:
1. Login with demo account to view Digital ID
2. ID card can be flipped to see barcode
3. Biometric protection can be enabled in settings
4. Emergency alerts are admin-only (not testable with demo)

The app requires school network for full functionality.
Push notifications require device tokens.
```

---

## Google Play Submission (Android)

### Requirements

1. **Google Play Console** account ($25 one-time)
2. **App signing** key generated
3. **Privacy policy** published online

### Play Store Listing

```
App Name: AISJ Connect
Short Description: Digital ID cards, hall passes, and emergency alerts for school
Full Description:
AISJ Connect is your all-in-one school app for:

✓ Digital ID Cards - Display your school ID on your phone
✓ Smart Pass - Request and manage hall passes
✓ Emergency Alerts - Receive critical safety notifications
✓ Visitor Check-in - Register campus visitors

Features:
• Secure biometric protection for ID cards
• QR code scanning for ID verification
• Real-time pass tracking
• Push notifications for announcements
• Multi-language support

Category: Education
Content Rating: Everyone
```

### Required Assets

- Feature Graphic (1024 x 500)
- App Icon (512 x 512)
- Screenshots (minimum 2, maximum 8)
- Phone screenshots (16:9 or 9:16)
- Tablet screenshots (optional)

---

## Push Notification Setup

### Firebase Cloud Messaging (FCM)

1. Create Firebase project
2. Download `google-services.json` (Android)
3. Download `GoogleService-Info.plist` (iOS)
4. Configure in `app.json`

### Apple Push Notification Service (APNs)

1. Create APNs key in Apple Developer
2. Download `.p8` key file
3. Note Key ID and Team ID
4. Configure in backend

---

## Post-Deployment

### Monitoring

1. **Crash Reporting** - Sentry or Firebase Crashlytics
2. **Analytics** - Firebase Analytics or Amplitude
3. **Performance** - Firebase Performance Monitoring
4. **Backend** - Datadog or New Relic

### Update Strategy

1. **Phased Rollout** - Start with 10%, increase gradually
2. **Force Update** - For critical security patches
3. **Feature Flags** - Control feature availability remotely

### Support Channels

- In-app feedback form
- Email: support@school.edu
- Help documentation in app
- Status page for service outages

---

## Rollback Plan

If critical issues are discovered:

1. **iOS** - Request expedited review for fix, or remove from sale
2. **Android** - Halt rollout, publish fixed version
3. **Backend** - Revert to previous deployment using CI/CD

---

**Document Version:** 1.0
**Last Updated:** January 2026
