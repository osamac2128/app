import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth, API_URL } from '../../contexts/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import axios from 'axios';

interface EmergencyAlert {
  _id: string;
  type: string;
  severity: string;
  title: string;
  message: string;
  triggered_at: string;
  resolved_at?: string;
  is_drill: boolean;
}

export default function EmergencyManagementScreen() {
  const { token } = useAuth();
  const router = useRouter();
  const [activeAlert, setActiveAlert] = useState<EmergencyAlert | null>(null);
  const [history, setHistory] = useState<EmergencyAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const [activeResponse, historyResponse] = await Promise.all([
        axios.get(`${API_URL}/api/emergency/active`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios.get(`${API_URL}/api/emergency/history`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      setActiveAlert(activeResponse.data);
      setHistory(historyResponse.data);
    } catch (error: any) {
      console.error('Error fetching emergency data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  const handleTriggerAlert = () => {
    Alert.alert(
      'Trigger Emergency Alert',
      'This will send an alert to all users. Continue?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Trigger Alert',
          style: 'destructive',
          onPress: () => router.push('/admin/trigger-emergency' as any),
        },
      ]
    );
  };

  const handleResolveAlert = async () => {
    if (!activeAlert) return;

    Alert.alert(
      'Resolve Emergency',
      'Mark this emergency as resolved?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Resolve',
          onPress: async () => {
            try {
              await axios.post(
                `${API_URL}/api/emergency/resolve/${activeAlert._id}`,
                { resolution_notes: 'Resolved by admin' },
                { headers: { Authorization: `Bearer ${token}` } }
              );
              
              Alert.alert('Success', 'Emergency resolved');
              fetchData();
            } catch (error: any) {
              Alert.alert('Error', 'Failed to resolve emergency');
            }
          },
        },
      ]
    );
  };

  const getAlertIcon = (type: string) => {
    const icons: any = {
      lockdown: 'lock-closed',
      fire: 'flame',
      medical: 'medical',
      weather: 'thunderstorm',
      tornado: 'thunderstorm',
      earthquake: 'pulse',
    };
    return icons[type] || 'warning';
  };

  const getAlertColor = (severity: string) => {
    const colors: any = {
      critical: '#DC2626',
      high: '#EF4444',
      medium: '#F59E0B',
      low: '#3B82F6',
      info: '#10B981',
    };
    return colors[severity] || '#EF4444';
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#1E3A5F" />
          <Text style={styles.loadingText}>Loading...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#FFFFFF" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Emergency</Text>
        <TouchableOpacity onPress={handleTriggerAlert} style={styles.triggerButton}>
          <Ionicons name="add-circle" size={24} color="#FFFFFF" />
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {activeAlert ? (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Active Emergency</Text>
            <View
              style={[
                styles.activeAlertCard,
                { borderColor: getAlertColor(activeAlert.severity) },
              ]}
            >
              <View style={styles.alertHeader}>
                <View
                  style={[
                    styles.alertIconContainer,
                    { backgroundColor: getAlertColor(activeAlert.severity) },
                  ]}
                >
                  <Ionicons
                    name={getAlertIcon(activeAlert.type) as any}
                    size={32}
                    color="#FFFFFF"
                  />
                </View>
                <View style={styles.alertInfo}>
                  <Text style={styles.alertTitle}>{activeAlert.title}</Text>
                  <Text style={styles.alertType}>
                    {activeAlert.type.toUpperCase()} {activeAlert.is_drill && '(DRILL)'}
                  </Text>
                </View>
              </View>

              <Text style={styles.alertMessage}>{activeAlert.message}</Text>

              <View style={styles.alertMeta}>
                <Text style={styles.alertTime}>
                  Triggered: {new Date(activeAlert.triggered_at).toLocaleString()}
                </Text>
              </View>

              <TouchableOpacity
                style={styles.resolveButton}
                onPress={handleResolveAlert}
              >
                <Ionicons name="checkmark-circle" size={20} color="#FFFFFF" />
                <Text style={styles.resolveButtonText}>Resolve Emergency</Text>
              </TouchableOpacity>
            </View>
          </View>
        ) : (
          <View style={styles.noActiveAlert}>
            <Ionicons name="shield-checkmark" size={64} color="#10B981" />
            <Text style={styles.noActiveText}>No Active Emergency</Text>
          </View>
        )}

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Emergency History</Text>
          {history.length === 0 ? (
            <View style={styles.emptyHistory}>
              <Text style={styles.emptyText}>No previous emergencies</Text>
            </View>
          ) : (
            history.map((alert) => (
              <View key={alert._id} style={styles.historyCard}>
                <View style={styles.historyHeader}>
                  <Ionicons
                    name={getAlertIcon(alert.type) as any}
                    size={24}
                    color={getAlertColor(alert.severity)}
                  />
                  <View style={styles.historyInfo}>
                    <Text style={styles.historyTitle}>{alert.title}</Text>
                    <Text style={styles.historyType}>
                      {alert.type} {alert.is_drill && '(DRILL)'}
                    </Text>
                  </View>
                  {alert.resolved_at && (
                    <Ionicons name="checkmark-circle" size={24} color="#10B981" />
                  )}
                </View>
                <Text style={styles.historyTime}>
                  {new Date(alert.triggered_at).toLocaleString()}
                </Text>
              </View>
            ))
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#F5F7FA',
  },
  header: {
    backgroundColor: '#1E3A5F',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  backButton: {
    padding: 8,
  },
  triggerButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
    flex: 1,
    textAlign: 'center',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#6B7280',
  },
  scrollView: {
    flex: 1,
  },
  section: {
    padding: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1E3A5F',
    marginBottom: 12,
  },
  activeAlertCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    borderWidth: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  alertHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  alertIconContainer: {
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  alertInfo: {
    flex: 1,
  },
  alertTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1E3A5F',
  },
  alertType: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
  },
  alertMessage: {
    fontSize: 16,
    color: '#374151',
    lineHeight: 24,
    marginBottom: 16,
  },
  alertMeta: {
    marginBottom: 16,
  },
  alertTime: {
    fontSize: 14,
    color: '#6B7280',
  },
  resolveButton: {
    backgroundColor: '#10B981',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 14,
    borderRadius: 8,
    gap: 8,
  },
  resolveButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  noActiveAlert: {
    alignItems: 'center',
    padding: 48,
    marginTop: 32,
  },
  noActiveText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#10B981',
    marginTop: 16,
  },
  emptyHistory: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 32,
    alignItems: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: '#9CA3AF',
  },
  historyCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  historyHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8,
  },
  historyInfo: {
    flex: 1,
    marginLeft: 12,
  },
  historyTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1E3A5F',
  },
  historyType: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 2,
    textTransform: 'uppercase',
  },
  historyTime: {
    fontSize: 13,
    color: '#9CA3AF',
    marginLeft: 36,
  },
});