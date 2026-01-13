/**
 * Push Notification API Client
 *
 * Handles device registration and push notification management.
 */

import client from './client';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Types
export type DevicePlatform = 'ios' | 'android' | 'web';

export interface RegisterDeviceRequest {
    token: string;
    platform: DevicePlatform;
    device_name?: string;
    app_version?: string;
}

export interface RegisterDeviceResponse {
    status: 'created' | 'updated';
    token_id: string;
}

export interface DeviceInfo {
    _id: string;
    user_id: string;
    token: string;
    platform: DevicePlatform;
    device_name?: string;
    app_version?: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export interface SendNotificationRequest {
    title: string;
    body: string;
    user_ids?: string[];
    role?: string;
    priority?: 'low' | 'normal' | 'high' | 'critical';
    data?: Record<string, any>;
}

export interface SendNotificationResponse {
    sent: number;
    failed: number;
    users_notified?: number;
    errors?: string[];
}

export interface PushStatus {
    fcm_initialized: boolean;
    apns_initialized: boolean;
    note: string;
}

// Storage key for push token
const PUSH_TOKEN_KEY = 'push_notification_token';

/**
 * Get the current device platform
 */
function getDevicePlatform(): DevicePlatform {
    if (Platform.OS === 'ios') return 'ios';
    if (Platform.OS === 'android') return 'android';
    return 'web';
}

/**
 * Register a device for push notifications
 */
export async function registerDevice(
    token: string,
    deviceName?: string,
    appVersion?: string
): Promise<RegisterDeviceResponse> {
    const response = await client.post<RegisterDeviceResponse>('/api/push/register', {
        token,
        platform: getDevicePlatform(),
        device_name: deviceName,
        app_version: appVersion,
    });

    // Store token locally
    await AsyncStorage.setItem(PUSH_TOKEN_KEY, token);

    return response.data;
}

/**
 * Unregister a device from push notifications
 */
export async function unregisterDevice(token: string): Promise<void> {
    await client.post('/api/push/unregister', { token });

    // Remove stored token
    await AsyncStorage.removeItem(PUSH_TOKEN_KEY);
}

/**
 * Get all registered devices for current user
 */
export async function getRegisteredDevices(): Promise<DeviceInfo[]> {
    const response = await client.get<{ devices: DeviceInfo[] }>('/api/push/devices');
    return response.data.devices;
}

/**
 * Send a notification (Admin only)
 */
export async function sendNotification(
    request: SendNotificationRequest
): Promise<SendNotificationResponse> {
    const response = await client.post<SendNotificationResponse>('/api/push/send', request);
    return response.data;
}

/**
 * Send notification to all users with a specific role (Admin only)
 */
export async function sendToRole(
    role: string,
    request: SendNotificationRequest
): Promise<SendNotificationResponse> {
    const response = await client.post<SendNotificationResponse>(
        `/api/push/send/role/${role}`,
        request
    );
    return response.data;
}

/**
 * Broadcast notification to all users (Admin only)
 */
export async function broadcastNotification(
    request: SendNotificationRequest
): Promise<SendNotificationResponse> {
    const response = await client.post<SendNotificationResponse>('/api/push/broadcast', request);
    return response.data;
}

/**
 * Get push notification service status (Admin only)
 */
export async function getPushStatus(): Promise<PushStatus> {
    const response = await client.get<PushStatus>('/api/push/status');
    return response.data;
}

/**
 * Get stored push token
 */
export async function getStoredPushToken(): Promise<string | null> {
    return await AsyncStorage.getItem(PUSH_TOKEN_KEY);
}

/**
 * Check if push notifications are enabled
 */
export async function isPushEnabled(): Promise<boolean> {
    const token = await getStoredPushToken();
    return token !== null;
}

export default {
    registerDevice,
    unregisterDevice,
    getRegisteredDevices,
    sendNotification,
    sendToRole,
    broadcastNotification,
    getPushStatus,
    getStoredPushToken,
    isPushEnabled,
};
