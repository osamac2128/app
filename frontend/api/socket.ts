/**
 * Socket.IO Client for Real-Time Communications
 *
 * This module provides WebSocket connectivity for real-time updates
 * including pass notifications, emergency alerts, and live monitoring.
 */

import { io, Socket } from 'socket.io-client';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';

const SOCKET_URL = Constants.expoConfig?.extra?.EXPO_PUBLIC_BACKEND_URL ||
    process.env.EXPO_PUBLIC_BACKEND_URL ||
    'http://localhost:8000';

// Socket event types
export interface PassEventData {
    type: 'pass_created' | 'pass_approved' | 'pass_rejected' | 'pass_completed' | 'pass_overtime';
    pass: {
        _id: string;
        student_id: string;
        student?: {
            name: string;
            email: string;
        };
        origin_location_id?: string;
        origin_name?: string;
        destination_location_id?: string;
        destination_name?: string;
        status: string;
        created_at: string;
        expected_return_time?: string;
    };
    reason?: string;
    minutes_overtime?: number;
    timestamp: string;
}

export interface EmergencyEventData {
    type: 'emergency_triggered' | 'emergency_updated' | 'emergency_ended';
    alert: {
        _id: string;
        alert_type: string;
        severity: string;
        message: string;
        instructions?: string;
        status: string;
        triggered_by: string;
        created_at: string;
    };
    timestamp: string;
}

export interface CheckinEventData {
    type: 'checkin_update';
    checkin: {
        student_id: string;
        student_name: string;
        location: string;
        checked_in_by: string;
        timestamp: string;
    };
    timestamp: string;
}

export interface VisitorEventData {
    type: 'visitor_checkin' | 'visitor_checkout';
    visitor: {
        _id: string;
        name: string;
        purpose: string;
        host_name?: string;
        timestamp: string;
    };
    timestamp: string;
}

export type SocketEventData = PassEventData | EmergencyEventData | CheckinEventData | VisitorEventData;

// Event listeners type
type EventListener<T> = (data: T) => void;

class SocketService {
    private socket: Socket | null = null;
    private listeners: Map<string, Set<EventListener<any>>> = new Map();
    private reconnectAttempts: number = 0;
    private maxReconnectAttempts: number = 5;
    private isConnecting: boolean = false;

    /**
     * Connect to the WebSocket server
     */
    async connect(): Promise<boolean> {
        if (this.socket?.connected) {
            console.log('[Socket] Already connected');
            return true;
        }

        if (this.isConnecting) {
            console.log('[Socket] Connection already in progress');
            return false;
        }

        this.isConnecting = true;

        try {
            const token = await AsyncStorage.getItem('auth_token');
            if (!token) {
                console.log('[Socket] No auth token available');
                this.isConnecting = false;
                return false;
            }

            this.socket = io(SOCKET_URL, {
                auth: { token },
                transports: ['websocket', 'polling'],
                reconnection: true,
                reconnectionAttempts: this.maxReconnectAttempts,
                reconnectionDelay: 1000,
                reconnectionDelayMax: 5000,
                timeout: 10000,
            });

            this.setupEventHandlers();
            this.isConnecting = false;

            return new Promise((resolve) => {
                const timeout = setTimeout(() => {
                    console.log('[Socket] Connection timeout');
                    resolve(false);
                }, 10000);

                this.socket!.once('connected', () => {
                    clearTimeout(timeout);
                    console.log('[Socket] Connected successfully');
                    this.reconnectAttempts = 0;
                    resolve(true);
                });

                this.socket!.once('connect_error', (error) => {
                    clearTimeout(timeout);
                    console.log('[Socket] Connection error:', error.message);
                    resolve(false);
                });
            });
        } catch (error) {
            console.error('[Socket] Connection failed:', error);
            this.isConnecting = false;
            return false;
        }
    }

    /**
     * Disconnect from the WebSocket server
     */
    disconnect(): void {
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
            console.log('[Socket] Disconnected');
        }
    }

    /**
     * Check if connected
     */
    isConnected(): boolean {
        return this.socket?.connected ?? false;
    }

    /**
     * Setup event handlers for the socket
     */
    private setupEventHandlers(): void {
        if (!this.socket) return;

        // Connection events
        this.socket.on('connect', () => {
            console.log('[Socket] Connected');
            this.reconnectAttempts = 0;
        });

        this.socket.on('disconnect', (reason) => {
            console.log('[Socket] Disconnected:', reason);
        });

        this.socket.on('connect_error', (error) => {
            console.log('[Socket] Connection error:', error.message);
            this.reconnectAttempts++;
        });

        this.socket.on('reconnect', (attempt) => {
            console.log('[Socket] Reconnected after', attempt, 'attempts');
        });

        this.socket.on('reconnect_failed', () => {
            console.log('[Socket] Reconnection failed');
        });

        // Pass events
        this.socket.on('pass_created', (data: PassEventData) => {
            this.emit('pass_created', data);
        });

        this.socket.on('pass_approved', (data: PassEventData) => {
            this.emit('pass_approved', data);
        });

        this.socket.on('pass_rejected', (data: PassEventData) => {
            this.emit('pass_rejected', data);
        });

        this.socket.on('pass_completed', (data: PassEventData) => {
            this.emit('pass_completed', data);
        });

        this.socket.on('pass_overtime', (data: PassEventData) => {
            this.emit('pass_overtime', data);
        });

        // Emergency events
        this.socket.on('emergency_triggered', (data: EmergencyEventData) => {
            this.emit('emergency_triggered', data);
        });

        this.socket.on('emergency_updated', (data: EmergencyEventData) => {
            this.emit('emergency_updated', data);
        });

        this.socket.on('emergency_ended', (data: EmergencyEventData) => {
            this.emit('emergency_ended', data);
        });

        // Checkin events
        this.socket.on('checkin_update', (data: CheckinEventData) => {
            this.emit('checkin_update', data);
        });

        // Visitor events
        this.socket.on('visitor_checkin', (data: VisitorEventData) => {
            this.emit('visitor_checkin', data);
        });

        this.socket.on('visitor_checkout', (data: VisitorEventData) => {
            this.emit('visitor_checkout', data);
        });
    }

    /**
     * Join a room
     */
    joinRoom(room: string): void {
        if (this.socket?.connected) {
            this.socket.emit('join_room', { room });
            console.log('[Socket] Joined room:', room);
        }
    }

    /**
     * Leave a room
     */
    leaveRoom(room: string): void {
        if (this.socket?.connected) {
            this.socket.emit('leave_room', { room });
            console.log('[Socket] Left room:', room);
        }
    }

    /**
     * Subscribe to an event
     */
    on<T extends SocketEventData>(event: string, listener: EventListener<T>): () => void {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, new Set());
        }
        this.listeners.get(event)!.add(listener);

        // Return unsubscribe function
        return () => {
            this.listeners.get(event)?.delete(listener);
        };
    }

    /**
     * Unsubscribe from an event
     */
    off<T extends SocketEventData>(event: string, listener: EventListener<T>): void {
        this.listeners.get(event)?.delete(listener);
    }

    /**
     * Emit to internal listeners
     */
    private emit<T>(event: string, data: T): void {
        const eventListeners = this.listeners.get(event);
        if (eventListeners) {
            eventListeners.forEach((listener) => {
                try {
                    listener(data);
                } catch (error) {
                    console.error(`[Socket] Error in listener for ${event}:`, error);
                }
            });
        }
    }
}

// Export singleton instance
export const socketService = new SocketService();

// React hooks for socket events
export function useSocketEvent<T extends SocketEventData>(
    event: string,
    callback: (data: T) => void
): void {
    // Note: In a real implementation, this would use useEffect
    // to properly manage the subscription lifecycle
    const unsubscribe = socketService.on<T>(event, callback);
    // Return cleanup would be handled by useEffect in actual usage
}

export default socketService;
