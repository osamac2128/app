import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    StyleSheet,
    TouchableOpacity,
    ScrollView,
    Alert,
    ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth, API_URL } from '../../contexts/AuthContext';
import axios from 'axios';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';

interface EmergencyAlert {
    _id: string;
    type: string;
    title: string;
    message: string;
    severity: string;
    triggered_at: string;
}

export default function EmergencyAdminScreen() {
    const { token, user } = useAuth();
    const router = useRouter();
    const [activeAlert, setActiveAlert] = useState<EmergencyAlert | null>(null);
    const [loading, setLoading] = useState(true);
    const [actionLoading, setActionLoading] = useState(false);

    useEffect(() => {
        if (user?.role !== 'admin') {
            Alert.alert('Access Denied', 'Only admins can access this page.');
            router.back();
            return;
        }
        fetchActiveAlert();
    }, []);

    const fetchActiveAlert = async () => {
        setLoading(true);
        try {
            const response = await axios.get(`${API_URL}/api/emergency/active`, {
                headers: { Authorization: `Bearer ${token}` },
            });
            setActiveAlert(response.data);
        } catch (error) {
            console.error('Error fetching active alert:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleTriggerAlert = async (type: string, title: string, message: string, severity: string) => {
        setActionLoading(true);
        try {
            const response = await axios.post(
                `${API_URL}/api/emergency/trigger`,
                {
                    type,
                    title,
                    message,
                    severity,
                    triggered_by: user?._id,
                    is_drill: false,
                },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setActiveAlert(response.data);
            Alert.alert('Alert Triggered', 'The emergency alert has been broadcasted.');
        } catch (error: any) {
            Alert.alert('Error', error.response?.data?.detail || 'Failed to trigger alert.');
        } finally {
            setActionLoading(false);
        }
    };

    const handleResolveAlert = async () => {
        if (!activeAlert) return;
        setActionLoading(true);
        try {
            await axios.post(
                `${API_URL}/api/emergency/resolve/${activeAlert._id}`,
                { resolution_notes: 'Resolved by admin console' },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setActiveAlert(null);
            Alert.alert('Alert Resolved', 'The emergency alert has been cleared.');
        } catch (error: any) {
            Alert.alert('Error', 'Failed to resolve alert.');
        } finally {
            setActionLoading(false);
        }
    };

    if (loading) {
        return (
            <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#EF4444" />
            </View>
        );
    }

    return (
        <SafeAreaView style={styles.container}>
            <ScrollView contentContainerStyle={styles.content}>
                <Text style={styles.headerTitle}>Emergency Console</Text>
                <Text style={styles.headerSubtitle}>Authorized Personnel Only</Text>

                {activeAlert ? (
                    <View style={styles.activeAlertCard}>
                        <View style={styles.alertHeader}>
                            <Ionicons name="warning" size={32} color="#FFFFFF" />
                            <Text style={styles.alertTitle}>ACTIVE: {activeAlert.title}</Text>
                        </View>
                        <Text style={styles.alertMessage}>{activeAlert.message}</Text>
                        <Text style={styles.alertTime}>Triggered: {new Date(activeAlert.triggered_at).toLocaleTimeString()}</Text>

                        <TouchableOpacity
                            style={styles.resolveButton}
                            onPress={handleResolveAlert}
                            disabled={actionLoading}
                        >
                            {actionLoading ? (
                                <ActivityIndicator color="#FFFFFF" />
                            ) : (
                                <Text style={styles.resolveButtonText}>RESOLVE ALERT</Text>
                            )}
                        </TouchableOpacity>
                    </View>
                ) : (
                    <View style={styles.grid}>
                        <TouchableOpacity
                            style={[styles.triggerCard, { backgroundColor: '#EF4444' }]}
                            onPress={() => Alert.alert(
                                'Confirm Lockdown',
                                'Are you sure you want to trigger a LOCKDOWN?',
                                [
                                    { text: 'Cancel', style: 'cancel' },
                                    { text: 'TRIGGER', style: 'destructive', onPress: () => handleTriggerAlert('lockdown', 'Lockdown', 'Locks, Lights, Out of Sight.', 'critical') }
                                ]
                            )}
                        >
                            <Ionicons name="lock-closed" size={40} color="#FFFFFF" />
                            <Text style={styles.triggerText}>LOCKDOWN</Text>
                        </TouchableOpacity>

                        <TouchableOpacity
                            style={[styles.triggerCard, { backgroundColor: '#F59E0B' }]}
                            onPress={() => handleTriggerAlert('fire', 'Fire Alarm', 'Evacuate to nearest exit.', 'high')}
                        >
                            <Ionicons name="flame" size={40} color="#FFFFFF" />
                            <Text style={styles.triggerText}>FIRE</Text>
                        </TouchableOpacity>

                        <TouchableOpacity
                            style={[styles.triggerCard, { backgroundColor: '#3B82F6' }]}
                            onPress={() => handleTriggerAlert('weather', 'Severe Weather', 'Shelter in place.', 'medium')}
                        >
                            <Ionicons name="thunderstorm" size={40} color="#FFFFFF" />
                            <Text style={styles.triggerText}>WEATHER</Text>
                        </TouchableOpacity>

                        <TouchableOpacity
                            style={[styles.triggerCard, { backgroundColor: '#10B981' }]}
                            onPress={() => handleTriggerAlert('drill', 'Drill', 'This is a drill.', 'low')}
                        >
                            <Ionicons name="construct" size={40} color="#FFFFFF" />
                            <Text style={styles.triggerText}>DRILL</Text>
                        </TouchableOpacity>
                    </View>
                )}
            </ScrollView>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#1F2937', // Dark background for serious tone
    },
    loadingContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#1F2937',
    },
    content: {
        padding: 24,
    },
    headerTitle: {
        fontSize: 28,
        fontWeight: 'bold',
        color: '#FFFFFF',
        marginBottom: 4,
    },
    headerSubtitle: {
        fontSize: 14,
        color: '#9CA3AF',
        marginBottom: 32,
    },
    activeAlertCard: {
        backgroundColor: '#DC2626',
        borderRadius: 16,
        padding: 24,
        alignItems: 'center',
    },
    alertHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 16,
    },
    alertTitle: {
        color: '#FFFFFF',
        fontSize: 24,
        fontWeight: 'bold',
        marginLeft: 12,
    },
    alertMessage: {
        color: '#FFFFFF',
        fontSize: 18,
        textAlign: 'center',
        marginBottom: 8,
    },
    alertTime: {
        color: 'rgba(255,255,255,0.8)',
        fontSize: 14,
        marginBottom: 24,
    },
    resolveButton: {
        backgroundColor: '#FFFFFF',
        paddingHorizontal: 32,
        paddingVertical: 16,
        borderRadius: 8,
        width: '100%',
        alignItems: 'center',
    },
    resolveButtonText: {
        color: '#DC2626',
        fontSize: 18,
        fontWeight: 'bold',
    },
    grid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        justifyContent: 'space-between',
        gap: 16,
    },
    triggerCard: {
        width: '47%',
        aspectRatio: 1,
        borderRadius: 16,
        justifyContent: 'center',
        alignItems: 'center',
        elevation: 4,
        marginBottom: 16,
    },
    triggerText: {
        color: '#FFFFFF',
        fontSize: 16,
        fontWeight: 'bold',
        marginTop: 12,
    },
});
