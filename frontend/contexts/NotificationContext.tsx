/**
 * Notification Context Provider
 *
 * Manages push notification registration, permissions, and handling.
 * Integrates with Expo notifications and the backend push service.
 */

import React, { createContext, useContext, useEffect, useState, useCallback, ReactNode, useRef } from 'react';
import { Platform, Alert } from 'react-native';
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import Constants from 'expo-constants';
import { useAuth } from './AuthContext';
import {
    registerDevice,
    unregisterDevice,
    getStoredPushToken,
} from '../api/pushNotifications';

// Configure notification behavior
Notifications.setNotificationHandler({
    handleNotification: async () => ({
        shouldShowAlert: true,
        shouldPlaySound: true,
        shouldSetBadge: true,
        shouldShowBanner: true,
        shouldShowList: true,
    }),
});

interface NotificationContextType {
    expoPushToken: string | null;
    notification: Notifications.Notification | null;
    isRegistered: boolean;
    isLoading: boolean;
    error: string | null;
    registerForPushNotifications: () => Promise<boolean>;
    unregisterFromPushNotifications: () => Promise<void>;
}

const NotificationContext = createContext<NotificationContextType | null>(null);

interface NotificationProviderProps {
    children: ReactNode;
}

export function NotificationProvider({ children }: NotificationProviderProps) {
    const [expoPushToken, setExpoPushToken] = useState<string | null>(null);
    const [notification, setNotification] = useState<Notifications.Notification | null>(null);
    const [isRegistered, setIsRegistered] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const { isAuthenticated, user } = useAuth();
    const notificationListener = useRef<Notifications.EventSubscription>();
    const responseListener = useRef<Notifications.EventSubscription>();

    // Get Expo push token
    const getExpoPushToken = async (): Promise<string | null> => {
        // Check if physical device
        if (!Device.isDevice) {
            console.log('[Push] Must use physical device for Push Notifications');
            return null;
        }

        // Check permissions
        const { status: existingStatus } = await Notifications.getPermissionsAsync();
        let finalStatus = existingStatus;

        if (existingStatus !== 'granted') {
            const { status } = await Notifications.requestPermissionsAsync();
            finalStatus = status;
        }

        if (finalStatus !== 'granted') {
            console.log('[Push] Failed to get push notification permissions');
            return null;
        }

        // Get the token
        try {
            const projectId = Constants.expoConfig?.extra?.eas?.projectId ?? Constants.easConfig?.projectId;

            if (!projectId) {
                console.log('[Push] No project ID found for Expo push token');
                // In development, generate a mock token
                return `ExpoMockToken-${Date.now()}`;
            }

            const token = await Notifications.getExpoPushTokenAsync({
                projectId,
            });

            return token.data;
        } catch (err) {
            console.error('[Push] Error getting Expo push token:', err);
            return null;
        }
    };

    // Configure Android channel
    const configureAndroidChannel = async () => {
        if (Platform.OS === 'android') {
            await Notifications.setNotificationChannelAsync('default', {
                name: 'Default',
                importance: Notifications.AndroidImportance.MAX,
                vibrationPattern: [0, 250, 250, 250],
                lightColor: '#FF231F7C',
            });

            // Emergency channel with max importance
            await Notifications.setNotificationChannelAsync('emergency', {
                name: 'Emergency Alerts',
                importance: Notifications.AndroidImportance.MAX,
                vibrationPattern: [0, 500, 250, 500, 250, 500],
                lightColor: '#FF0000',
                sound: 'emergency.wav',
            });

            // Pass notifications channel
            await Notifications.setNotificationChannelAsync('passes', {
                name: 'Pass Notifications',
                importance: Notifications.AndroidImportance.HIGH,
                vibrationPattern: [0, 250, 250, 250],
            });
        }
    };

    // Register for push notifications
    const registerForPushNotifications = useCallback(async (): Promise<boolean> => {
        setIsLoading(true);
        setError(null);

        try {
            await configureAndroidChannel();

            const token = await getExpoPushToken();
            if (!token) {
                setError('Failed to get push token');
                setIsLoading(false);
                return false;
            }

            setExpoPushToken(token);

            // Register with backend if authenticated
            if (isAuthenticated) {
                try {
                    await registerDevice(
                        token,
                        Device.deviceName || undefined,
                        Constants.expoConfig?.version
                    );
                    setIsRegistered(true);
                    console.log('[Push] Successfully registered device with backend');
                } catch (err: any) {
                    console.error('[Push] Failed to register with backend:', err);
                    // Token is still valid locally
                }
            }

            setIsLoading(false);
            return true;
        } catch (err: any) {
            console.error('[Push] Registration error:', err);
            setError(err.message || 'Registration failed');
            setIsLoading(false);
            return false;
        }
    }, [isAuthenticated]);

    // Unregister from push notifications
    const unregisterFromPushNotifications = useCallback(async (): Promise<void> => {
        setIsLoading(true);

        try {
            if (expoPushToken) {
                await unregisterDevice(expoPushToken);
            }
            setExpoPushToken(null);
            setIsRegistered(false);
            console.log('[Push] Successfully unregistered');
        } catch (err) {
            console.error('[Push] Unregister error:', err);
        } finally {
            setIsLoading(false);
        }
    }, [expoPushToken]);

    // Handle notification received while app is foregrounded
    const handleNotificationReceived = useCallback((notification: Notifications.Notification) => {
        console.log('[Push] Notification received:', notification);
        setNotification(notification);

        const data = notification.request.content.data;

        // Handle emergency notifications with high priority
        if (data?.type === 'emergency') {
            Alert.alert(
                notification.request.content.title || 'Emergency Alert',
                notification.request.content.body || 'Please check for emergency instructions.',
                [{ text: 'OK' }],
                { cancelable: false }
            );
        }
    }, []);

    // Handle notification response (user tapped notification)
    const handleNotificationResponse = useCallback((response: Notifications.NotificationResponse) => {
        console.log('[Push] Notification response:', response);

        const data = response.notification.request.content.data;
        const notificationType = data?.type as string;

        // Navigate based on notification type
        // Note: Navigation would be implemented based on the app's routing structure
        switch (notificationType) {
            case 'pass_approved':
            case 'pass_rejected':
            case 'pass_overtime':
                // Navigate to smart pass screen
                console.log('[Push] Navigate to smart pass');
                break;
            case 'emergency':
            case 'emergency_ended':
                // Navigate to emergency screen
                console.log('[Push] Navigate to emergency');
                break;
            case 'visitor_arrival':
                // Navigate to visitor screen
                console.log('[Push] Navigate to visitors');
                break;
            case 'announcement':
                // Navigate to messages
                console.log('[Push] Navigate to messages');
                break;
            default:
                console.log('[Push] Unknown notification type:', notificationType);
        }
    }, []);

    // Auto-register when authenticated
    useEffect(() => {
        if (isAuthenticated && user && !isRegistered) {
            registerForPushNotifications();
        }
    }, [isAuthenticated, user, isRegistered, registerForPushNotifications]);

    // Setup notification listeners
    useEffect(() => {
        // Check for stored token on mount
        getStoredPushToken().then(token => {
            if (token) {
                setExpoPushToken(token);
                setIsRegistered(true);
            }
        });

        // Listen for notifications received while app is foregrounded
        notificationListener.current = Notifications.addNotificationReceivedListener(
            handleNotificationReceived
        );

        // Listen for notification responses (user interaction)
        responseListener.current = Notifications.addNotificationResponseReceivedListener(
            handleNotificationResponse
        );

        return () => {
            if (notificationListener.current) {
                Notifications.removeNotificationSubscription(notificationListener.current);
            }
            if (responseListener.current) {
                Notifications.removeNotificationSubscription(responseListener.current);
            }
        };
    }, [handleNotificationReceived, handleNotificationResponse]);

    const value: NotificationContextType = {
        expoPushToken,
        notification,
        isRegistered,
        isLoading,
        error,
        registerForPushNotifications,
        unregisterFromPushNotifications,
    };

    return (
        <NotificationContext.Provider value={value}>
            {children}
        </NotificationContext.Provider>
    );
}

export function useNotifications(): NotificationContextType {
    const context = useContext(NotificationContext);
    if (!context) {
        throw new Error('useNotifications must be used within a NotificationProvider');
    }
    return context;
}

// Helper hook for listening to specific notification types
export function useNotificationType(
    type: string,
    callback: (notification: Notifications.Notification) => void
): void {
    const { notification } = useNotifications();

    useEffect(() => {
        if (notification?.request.content.data?.type === type) {
            callback(notification);
        }
    }, [notification, type, callback]);
}

export default NotificationContext;
