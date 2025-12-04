import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    StyleSheet,
    TouchableOpacity,
    Modal,
    ActivityIndicator,
    Alert,
} from 'react-native';
import { useAuth, API_URL } from '../contexts/AuthContext';
import axios from 'axios';
import { Ionicons } from '@expo/vector-icons';
import { usePathname } from 'expo-router';

interface EmergencyAlert {
    _id: string;
    type: string;
    title: string;
    message: string;
    severity: string;
    instructions?: string;
}

export const EmergencyOverlay = () => {
    const { token, user } = useAuth();
    const [activeAlert, setActiveAlert] = useState<EmergencyAlert | null>(null);
    const [checkInStatus, setCheckInStatus] = useState<'safe' | 'need_help' | null>(null);
    const [loading, setLoading] = useState(false);
    const pathname = usePathname();

    // Poll for active alerts
    useEffect(() => {
        if (!token) return;

        const checkAlerts = async () => {
            try {
                const response = await axios.get(`${API_URL}/api/emergency/active`, {
                    headers: { Authorization: `Bearer ${token}` },
                });
                setActiveAlert(response.data);
            } catch (error) {
                console.error('Error checking alerts:', error);
            }
        };

        checkAlerts(); // Initial check
        const interval = setInterval(checkAlerts, 10000); // Check every 10 seconds

        return () => clearInterval(interval);
    }, [token]);

    const handleCheckIn = async (status: 'safe' | 'need_help') => {
        if (!activeAlert || !token) return;
        setLoading(true);
        try {
            await axios.post(
                `${API_URL}/api/emergency/check-in`,
                {
                    alert_id: activeAlert._id,
                    user_id: user?._id, // Ideally backend handles this from token
                    status: status,
                    location: 'Unknown', // Could implement geolocation here
                },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setCheckInStatus(status);
            Alert.alert('Status Sent', `You have marked yourself as ${status === 'safe' ? 'Safe' : 'Needing Help'}.`);
        } catch (error) {
            console.error('Check-in error:', error);
            Alert.alert('Error', 'Failed to send status.');
        } finally {
            setLoading(false);
        }
    };

    if (!activeAlert) return null;

    // Don't block admin console if implemented
    if (pathname?.includes('/admin/emergency')) return null;

    const isCritical = activeAlert.severity === 'critical';

    return (
        <Modal visible={true} transparent={true} animationType="slide">
            <View style={[styles.container, isCritical ? styles.criticalBg : styles.warningBg]}>
                <View style={styles.content}>
                    <Ionicons
                        name={isCritical ? "warning" : "alert-circle"}
                        size={64}
                        color="#FFFFFF"
                        style={styles.icon}
                    />

                    <Text style={styles.title}>{activeAlert.title.toUpperCase()}</Text>
                    <Text style={styles.message}>{activeAlert.message}</Text>

                    {activeAlert.instructions && (
                        <View style={styles.instructionsContainer}>
                            <Text style={styles.instructionsTitle}>INSTRUCTIONS:</Text>
                            <Text style={styles.instructionsText}>{activeAlert.instructions}</Text>
                        </View>
                    )}

                    <View style={styles.actions}>
                        <TouchableOpacity
                            style={[styles.button, styles.safeButton, checkInStatus === 'safe' && styles.selectedButton]}
                            onPress={() => handleCheckIn('safe')}
                            disabled={loading}
                        >
                            <Ionicons name="checkmark-circle" size={24} color="#FFFFFF" />
                            <Text style={styles.buttonText}>I'M SAFE</Text>
                        </TouchableOpacity>

                        <TouchableOpacity
                            style={[styles.button, styles.helpButton, checkInStatus === 'need_help' && styles.selectedButton]}
                            onPress={() => handleCheckIn('need_help')}
                            disabled={loading}
                        >
                            <Ionicons name="hand-left" size={24} color="#FFFFFF" />
                            <Text style={styles.buttonText}>NEED HELP</Text>
                        </TouchableOpacity>
                    </View>

                    {loading && <ActivityIndicator color="#FFFFFF" style={{ marginTop: 20 }} />}
                </View>
            </View>
        </Modal>
    );
};

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        padding: 24,
    },
    criticalBg: {
        backgroundColor: 'rgba(220, 38, 38, 0.95)', // Red
    },
    warningBg: {
        backgroundColor: 'rgba(245, 158, 11, 0.95)', // Orange
    },
    content: {
        width: '100%',
        alignItems: 'center',
    },
    icon: {
        marginBottom: 24,
    },
    title: {
        fontSize: 32,
        fontWeight: '900',
        color: '#FFFFFF',
        textAlign: 'center',
        marginBottom: 16,
        letterSpacing: 2,
    },
    message: {
        fontSize: 20,
        fontWeight: '600',
        color: '#FFFFFF',
        textAlign: 'center',
        marginBottom: 32,
    },
    instructionsContainer: {
        backgroundColor: 'rgba(0,0,0,0.2)',
        padding: 16,
        borderRadius: 8,
        width: '100%',
        marginBottom: 32,
    },
    instructionsTitle: {
        color: '#FFFFFF',
        fontWeight: 'bold',
        marginBottom: 8,
    },
    instructionsText: {
        color: '#FFFFFF',
        fontSize: 16,
    },
    actions: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        width: '100%',
        gap: 16,
    },
    button: {
        flex: 1,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        padding: 16,
        borderRadius: 12,
        elevation: 4,
    },
    safeButton: {
        backgroundColor: '#10B981', // Green
    },
    helpButton: {
        backgroundColor: '#374151', // Dark Gray (to contrast with red bg)
    },
    selectedButton: {
        borderWidth: 4,
        borderColor: '#FFFFFF',
    },
    buttonText: {
        color: '#FFFFFF',
        fontWeight: 'bold',
        fontSize: 16,
        marginLeft: 8,
    },
});
