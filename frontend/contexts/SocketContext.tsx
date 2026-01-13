/**
 * Socket Context Provider
 *
 * Provides WebSocket connectivity throughout the app with
 * automatic connection management based on authentication state.
 */

import React, { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { socketService, PassEventData, EmergencyEventData, SocketEventData } from '../api/socket';
import { useAuth } from './AuthContext';

interface SocketContextType {
    isConnected: boolean;
    connect: () => Promise<boolean>;
    disconnect: () => void;
    joinRoom: (room: string) => void;
    leaveRoom: (room: string) => void;
    onPassEvent: (callback: (data: PassEventData) => void) => () => void;
    onEmergencyEvent: (callback: (data: EmergencyEventData) => void) => () => void;
}

const SocketContext = createContext<SocketContextType | null>(null);

interface SocketProviderProps {
    children: ReactNode;
}

export function SocketProvider({ children }: SocketProviderProps) {
    const [isConnected, setIsConnected] = useState(false);
    const { isAuthenticated, user } = useAuth();

    // Connect to socket when authenticated
    useEffect(() => {
        let mounted = true;

        const initConnection = async () => {
            if (isAuthenticated && user) {
                const connected = await socketService.connect();
                if (mounted) {
                    setIsConnected(connected);
                }
            } else {
                socketService.disconnect();
                if (mounted) {
                    setIsConnected(false);
                }
            }
        };

        initConnection();

        return () => {
            mounted = false;
        };
    }, [isAuthenticated, user]);

    // Manual connect
    const connect = useCallback(async (): Promise<boolean> => {
        const connected = await socketService.connect();
        setIsConnected(connected);
        return connected;
    }, []);

    // Manual disconnect
    const disconnect = useCallback(() => {
        socketService.disconnect();
        setIsConnected(false);
    }, []);

    // Join room
    const joinRoom = useCallback((room: string) => {
        socketService.joinRoom(room);
    }, []);

    // Leave room
    const leaveRoom = useCallback((room: string) => {
        socketService.leaveRoom(room);
    }, []);

    // Subscribe to pass events
    const onPassEvent = useCallback((callback: (data: PassEventData) => void): () => void => {
        const unsubscribers = [
            socketService.on<PassEventData>('pass_created', callback),
            socketService.on<PassEventData>('pass_approved', callback),
            socketService.on<PassEventData>('pass_rejected', callback),
            socketService.on<PassEventData>('pass_completed', callback),
            socketService.on<PassEventData>('pass_overtime', callback),
        ];

        return () => {
            unsubscribers.forEach(unsub => unsub());
        };
    }, []);

    // Subscribe to emergency events
    const onEmergencyEvent = useCallback((callback: (data: EmergencyEventData) => void): () => void => {
        const unsubscribers = [
            socketService.on<EmergencyEventData>('emergency_triggered', callback),
            socketService.on<EmergencyEventData>('emergency_updated', callback),
            socketService.on<EmergencyEventData>('emergency_ended', callback),
        ];

        return () => {
            unsubscribers.forEach(unsub => unsub());
        };
    }, []);

    const value: SocketContextType = {
        isConnected,
        connect,
        disconnect,
        joinRoom,
        leaveRoom,
        onPassEvent,
        onEmergencyEvent,
    };

    return (
        <SocketContext.Provider value={value}>
            {children}
        </SocketContext.Provider>
    );
}

export function useSocket(): SocketContextType {
    const context = useContext(SocketContext);
    if (!context) {
        throw new Error('useSocket must be used within a SocketProvider');
    }
    return context;
}

// Custom hook for pass events
export function usePassEvents(callback: (data: PassEventData) => void): void {
    const { onPassEvent } = useSocket();

    useEffect(() => {
        const unsubscribe = onPassEvent(callback);
        return unsubscribe;
    }, [callback, onPassEvent]);
}

// Custom hook for emergency events
export function useEmergencyEvents(callback: (data: EmergencyEventData) => void): void {
    const { onEmergencyEvent } = useSocket();

    useEffect(() => {
        const unsubscribe = onEmergencyEvent(callback);
        return unsubscribe;
    }, [callback, onEmergencyEvent]);
}

export default SocketContext;
