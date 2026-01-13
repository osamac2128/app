/**
 * Hall Monitor Live Dashboard
 *
 * Real-time dashboard for monitoring active hall passes, overtime alerts,
 * and location capacity. Uses WebSocket for live updates.
 */

import React, { useState, useEffect, useCallback } from 'react';
import {
    View,
    Text,
    StyleSheet,
    ScrollView,
    RefreshControl,
    TouchableOpacity,
    Alert,
    ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import client from '../../api/client';
import { socketService, PassEventData } from '../../api/socket';

interface ActivePass {
    _id: string;
    student_id: string;
    student?: {
        name: string;
        email: string;
    };
    origin_name?: string;
    destination_name?: string;
    status: string;
    created_at: string;
    approved_at?: string;
    expected_return_time?: string;
    time_limit_minutes: number;
    is_overtime?: boolean;
    minutes_remaining?: number;
    minutes_overtime?: number;
}

interface LocationCapacity {
    location_id: string;
    name: string;
    max_capacity: number;
    current_count: number;
    is_full: boolean;
}

interface ConnectionStatus {
    connected: boolean;
    lastUpdate: Date | null;
}

export default function HallMonitorDashboard() {
    const router = useRouter();
    const [activePasses, setActivePasses] = useState<ActivePass[]>([]);
    const [overtimePasses, setOvertimePasses] = useState<ActivePass[]>([]);
    const [capacities, setCapacities] = useState<LocationCapacity[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
        connected: false,
        lastUpdate: null,
    });
    const [error, setError] = useState<string | null>(null);

    // Fetch all data
    const fetchData = useCallback(async () => {
        try {
            setError(null);

            // Fetch active passes, overtime passes, and capacities in parallel
            const [passesRes, overtimeRes, capacitiesRes] = await Promise.all([
                client.get('/api/passes/hall-monitor'),
                client.get('/api/passes/overtime'),
                client.get('/api/passes/advanced/capacity/status'),
            ]);

            // Process active passes with time calculations
            const now = new Date();
            const processedPasses = passesRes.data.map((pass: ActivePass) => {
                if (pass.expected_return_time) {
                    const returnTime = new Date(pass.expected_return_time);
                    const diffMs = returnTime.getTime() - now.getTime();
                    const diffMins = Math.round(diffMs / 60000);

                    return {
                        ...pass,
                        is_overtime: diffMins < 0,
                        minutes_remaining: diffMins > 0 ? diffMins : 0,
                        minutes_overtime: diffMins < 0 ? Math.abs(diffMins) : 0,
                    };
                }
                return pass;
            });

            setActivePasses(processedPasses);
            setOvertimePasses(overtimeRes.data);
            setCapacities(capacitiesRes.data);
            setConnectionStatus(prev => ({ ...prev, lastUpdate: new Date() }));
        } catch (err: any) {
            console.error('Error fetching hall monitor data:', err);
            setError(err.response?.data?.error || 'Failed to load data');
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    }, []);

    // Handle pass events from WebSocket
    const handlePassEvent = useCallback((data: PassEventData) => {
        console.log('[HallMonitor] Received pass event:', data.type);
        setConnectionStatus({ connected: true, lastUpdate: new Date() });

        // Refresh data on any pass event
        fetchData();
    }, [fetchData]);

    // Initial fetch and socket setup
    useEffect(() => {
        fetchData();

        // Connect to socket and subscribe to pass events
        const connectSocket = async () => {
            const connected = await socketService.connect();
            setConnectionStatus(prev => ({ ...prev, connected }));
        };

        connectSocket();

        // Subscribe to pass events
        const unsubscribers = [
            socketService.on<PassEventData>('pass_created', handlePassEvent),
            socketService.on<PassEventData>('pass_approved', handlePassEvent),
            socketService.on<PassEventData>('pass_completed', handlePassEvent),
            socketService.on<PassEventData>('pass_overtime', handlePassEvent),
        ];

        // Auto-refresh every 30 seconds
        const refreshInterval = setInterval(fetchData, 30000);

        return () => {
            unsubscribers.forEach(unsub => unsub());
            clearInterval(refreshInterval);
        };
    }, [fetchData, handlePassEvent]);

    // Pull to refresh
    const onRefresh = useCallback(() => {
        setRefreshing(true);
        fetchData();
    }, [fetchData]);

    // End a pass
    const handleEndPass = async (passId: string) => {
        Alert.alert(
            'End Pass',
            'Are you sure you want to end this pass?',
            [
                { text: 'Cancel', style: 'cancel' },
                {
                    text: 'End Pass',
                    style: 'destructive',
                    onPress: async () => {
                        try {
                            await client.post(`/api/passes/end/${passId}`);
                            fetchData();
                        } catch (err) {
                            Alert.alert('Error', 'Failed to end pass');
                        }
                    },
                },
            ]
        );
    };

    // Extend a pass
    const handleExtendPass = async (passId: string) => {
        Alert.alert(
            'Extend Pass',
            'Add 5 more minutes to this pass?',
            [
                { text: 'Cancel', style: 'cancel' },
                {
                    text: 'Extend',
                    onPress: async () => {
                        try {
                            await client.post(`/api/passes/extend/${passId}?additional_minutes=5`);
                            fetchData();
                            Alert.alert('Success', 'Pass extended by 5 minutes');
                        } catch (err) {
                            Alert.alert('Error', 'Failed to extend pass');
                        }
                    },
                },
            ]
        );
    };

    // Format time
    const formatTime = (dateString: string) => {
        const date = new Date(dateString);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    if (loading) {
        return (
            <View style={styles.centered}>
                <ActivityIndicator size="large" color="#007AFF" />
                <Text style={styles.loadingText}>Loading Hall Monitor...</Text>
            </View>
        );
    }

    return (
        <ScrollView
            style={styles.container}
            refreshControl={
                <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
            }
        >
            {/* Connection Status */}
            <View style={[styles.statusBar, connectionStatus.connected ? styles.connected : styles.disconnected]}>
                <View style={[styles.statusDot, connectionStatus.connected ? styles.dotConnected : styles.dotDisconnected]} />
                <Text style={styles.statusText}>
                    {connectionStatus.connected ? 'Live Updates Active' : 'Connecting...'}
                </Text>
                {connectionStatus.lastUpdate && (
                    <Text style={styles.lastUpdateText}>
                        Updated: {formatTime(connectionStatus.lastUpdate.toISOString())}
                    </Text>
                )}
            </View>

            {error && (
                <View style={styles.errorBanner}>
                    <Text style={styles.errorText}>{error}</Text>
                </View>
            )}

            {/* Summary Stats */}
            <View style={styles.statsRow}>
                <View style={styles.statCard}>
                    <Text style={styles.statNumber}>{activePasses.length}</Text>
                    <Text style={styles.statLabel}>Active Passes</Text>
                </View>
                <View style={[styles.statCard, overtimePasses.length > 0 && styles.alertCard]}>
                    <Text style={[styles.statNumber, overtimePasses.length > 0 && styles.alertText]}>
                        {overtimePasses.length}
                    </Text>
                    <Text style={styles.statLabel}>Overtime</Text>
                </View>
                <View style={styles.statCard}>
                    <Text style={styles.statNumber}>
                        {capacities.filter(c => c.is_full).length}
                    </Text>
                    <Text style={styles.statLabel}>Full Locations</Text>
                </View>
            </View>

            {/* Overtime Passes Alert */}
            {overtimePasses.length > 0 && (
                <View style={styles.section}>
                    <View style={styles.sectionHeaderAlert}>
                        <Text style={styles.sectionTitleAlert}>OVERTIME ALERTS</Text>
                    </View>
                    {overtimePasses.map(pass => (
                        <View key={pass._id} style={styles.overtimeCard}>
                            <View style={styles.passHeader}>
                                <Text style={styles.studentName}>{pass.student?.name || 'Unknown'}</Text>
                                <Text style={styles.overtimeTime}>+{pass.minutes_overtime} min</Text>
                            </View>
                            <Text style={styles.passLocation}>
                                {pass.origin_name} → {pass.destination_name}
                            </Text>
                            <View style={styles.passActions}>
                                <TouchableOpacity
                                    style={styles.extendButton}
                                    onPress={() => handleExtendPass(pass._id)}
                                >
                                    <Text style={styles.extendButtonText}>Extend +5</Text>
                                </TouchableOpacity>
                                <TouchableOpacity
                                    style={styles.endButton}
                                    onPress={() => handleEndPass(pass._id)}
                                >
                                    <Text style={styles.endButtonText}>End Pass</Text>
                                </TouchableOpacity>
                            </View>
                        </View>
                    ))}
                </View>
            )}

            {/* Active Passes */}
            <View style={styles.section}>
                <Text style={styles.sectionTitle}>Active Passes</Text>
                {activePasses.length === 0 ? (
                    <View style={styles.emptyState}>
                        <Text style={styles.emptyText}>No active passes</Text>
                    </View>
                ) : (
                    activePasses.map(pass => (
                        <View
                            key={pass._id}
                            style={[styles.passCard, pass.is_overtime && styles.overtimePassCard]}
                        >
                            <View style={styles.passHeader}>
                                <Text style={styles.studentName}>{pass.student?.name || 'Unknown'}</Text>
                                <Text style={pass.is_overtime ? styles.overtimeTime : styles.remainingTime}>
                                    {pass.is_overtime
                                        ? `+${pass.minutes_overtime} min`
                                        : `${pass.minutes_remaining} min left`}
                                </Text>
                            </View>
                            <Text style={styles.passLocation}>
                                {pass.origin_name || 'Unknown'} → {pass.destination_name || 'Unknown'}
                            </Text>
                            <View style={styles.passFooter}>
                                <Text style={styles.passTime}>Started: {formatTime(pass.approved_at || pass.created_at)}</Text>
                                <TouchableOpacity
                                    style={styles.actionButton}
                                    onPress={() => handleEndPass(pass._id)}
                                >
                                    <Text style={styles.actionButtonText}>End</Text>
                                </TouchableOpacity>
                            </View>
                        </View>
                    ))
                )}
            </View>

            {/* Location Capacities */}
            <View style={styles.section}>
                <Text style={styles.sectionTitle}>Location Capacities</Text>
                <View style={styles.capacityGrid}>
                    {capacities.map(loc => (
                        <View
                            key={loc.location_id}
                            style={[styles.capacityCard, loc.is_full && styles.fullCapacityCard]}
                        >
                            <Text style={styles.capacityName}>{loc.name}</Text>
                            <Text style={[styles.capacityCount, loc.is_full && styles.fullCapacityText]}>
                                {loc.current_count}/{loc.max_capacity}
                            </Text>
                            {loc.is_full && <Text style={styles.fullBadge}>FULL</Text>}
                        </View>
                    ))}
                    {capacities.length === 0 && (
                        <Text style={styles.emptyText}>No capacity data configured</Text>
                    )}
                </View>
            </View>

            {/* Footer Spacer */}
            <View style={styles.footerSpacer} />
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f5f5f5',
    },
    centered: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#f5f5f5',
    },
    loadingText: {
        marginTop: 16,
        fontSize: 16,
        color: '#666',
    },
    statusBar: {
        flexDirection: 'row',
        alignItems: 'center',
        padding: 12,
        marginHorizontal: 16,
        marginTop: 16,
        borderRadius: 8,
    },
    connected: {
        backgroundColor: '#e8f5e9',
    },
    disconnected: {
        backgroundColor: '#fff3e0',
    },
    statusDot: {
        width: 8,
        height: 8,
        borderRadius: 4,
        marginRight: 8,
    },
    dotConnected: {
        backgroundColor: '#4caf50',
    },
    dotDisconnected: {
        backgroundColor: '#ff9800',
    },
    statusText: {
        fontSize: 14,
        fontWeight: '600',
        flex: 1,
    },
    lastUpdateText: {
        fontSize: 12,
        color: '#666',
    },
    errorBanner: {
        backgroundColor: '#ffebee',
        padding: 12,
        marginHorizontal: 16,
        marginTop: 8,
        borderRadius: 8,
    },
    errorText: {
        color: '#c62828',
        textAlign: 'center',
    },
    statsRow: {
        flexDirection: 'row',
        padding: 16,
        gap: 12,
    },
    statCard: {
        flex: 1,
        backgroundColor: '#fff',
        padding: 16,
        borderRadius: 12,
        alignItems: 'center',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
        elevation: 3,
    },
    alertCard: {
        backgroundColor: '#ffebee',
    },
    statNumber: {
        fontSize: 28,
        fontWeight: 'bold',
        color: '#333',
    },
    alertText: {
        color: '#c62828',
    },
    statLabel: {
        fontSize: 12,
        color: '#666',
        marginTop: 4,
    },
    section: {
        paddingHorizontal: 16,
        marginBottom: 16,
    },
    sectionTitle: {
        fontSize: 18,
        fontWeight: '600',
        color: '#333',
        marginBottom: 12,
    },
    sectionHeaderAlert: {
        backgroundColor: '#c62828',
        padding: 10,
        borderRadius: 8,
        marginBottom: 12,
    },
    sectionTitleAlert: {
        fontSize: 16,
        fontWeight: '700',
        color: '#fff',
        textAlign: 'center',
    },
    passCard: {
        backgroundColor: '#fff',
        padding: 16,
        borderRadius: 12,
        marginBottom: 12,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
        elevation: 3,
    },
    overtimePassCard: {
        borderLeftWidth: 4,
        borderLeftColor: '#c62828',
    },
    overtimeCard: {
        backgroundColor: '#fff',
        padding: 16,
        borderRadius: 12,
        marginBottom: 12,
        borderWidth: 2,
        borderColor: '#c62828',
    },
    passHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 8,
    },
    studentName: {
        fontSize: 16,
        fontWeight: '600',
        color: '#333',
    },
    remainingTime: {
        fontSize: 14,
        fontWeight: '600',
        color: '#4caf50',
    },
    overtimeTime: {
        fontSize: 14,
        fontWeight: '700',
        color: '#c62828',
    },
    passLocation: {
        fontSize: 14,
        color: '#666',
        marginBottom: 8,
    },
    passFooter: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginTop: 8,
        paddingTop: 8,
        borderTopWidth: 1,
        borderTopColor: '#eee',
    },
    passTime: {
        fontSize: 12,
        color: '#999',
    },
    passActions: {
        flexDirection: 'row',
        gap: 8,
        marginTop: 12,
    },
    actionButton: {
        backgroundColor: '#007AFF',
        paddingHorizontal: 16,
        paddingVertical: 6,
        borderRadius: 6,
    },
    actionButtonText: {
        color: '#fff',
        fontSize: 12,
        fontWeight: '600',
    },
    extendButton: {
        flex: 1,
        backgroundColor: '#4caf50',
        paddingVertical: 10,
        borderRadius: 8,
        alignItems: 'center',
    },
    extendButtonText: {
        color: '#fff',
        fontWeight: '600',
    },
    endButton: {
        flex: 1,
        backgroundColor: '#c62828',
        paddingVertical: 10,
        borderRadius: 8,
        alignItems: 'center',
    },
    endButtonText: {
        color: '#fff',
        fontWeight: '600',
    },
    capacityGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 12,
    },
    capacityCard: {
        backgroundColor: '#fff',
        padding: 12,
        borderRadius: 8,
        minWidth: '30%',
        flex: 1,
        alignItems: 'center',
    },
    fullCapacityCard: {
        backgroundColor: '#ffebee',
        borderWidth: 1,
        borderColor: '#c62828',
    },
    capacityName: {
        fontSize: 12,
        color: '#666',
        marginBottom: 4,
    },
    capacityCount: {
        fontSize: 18,
        fontWeight: '600',
        color: '#333',
    },
    fullCapacityText: {
        color: '#c62828',
    },
    fullBadge: {
        fontSize: 10,
        fontWeight: '700',
        color: '#c62828',
        marginTop: 4,
    },
    emptyState: {
        backgroundColor: '#fff',
        padding: 32,
        borderRadius: 12,
        alignItems: 'center',
    },
    emptyText: {
        fontSize: 14,
        color: '#999',
    },
    footerSpacer: {
        height: 40,
    },
});
