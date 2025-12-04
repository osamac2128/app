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

interface OvertimePass {
  _id: string;
  student: {
    name: string;
    email: string;
  };
  destination_name: string;
  minutes_overtime: number;
  expected_return_time: string;
  start_time: string;
}

export default function OvertimePassesScreen() {
  const { token } = useAuth();
  const router = useRouter();
  const [overtimePasses, setOvertimePasses] = useState<OvertimePass[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [processingIds, setProcessingIds] = useState<Set<string>>(new Set());

  const fetchOvertimePasses = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/passes/overtime`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setOvertimePasses(response.data);
    } catch (error: any) {
      console.error('Error fetching overtime passes:', error);
      Alert.alert('Error', 'Failed to load overtime passes');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchOvertimePasses();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchOvertimePasses();
  };

  const handleExtend = async (passId: string) => {
    Alert.prompt(
      'Extend Pass',
      'Enter additional minutes:',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Extend',
          onPress: async (minutes) => {
            const additionalMinutes = parseInt(minutes || '0');
            if (additionalMinutes <= 0) {
              Alert.alert('Error', 'Please enter a valid number of minutes');
              return;
            }

            setProcessingIds(prev => new Set(prev).add(passId));
            
            try {
              await axios.post(
                `${API_URL}/api/passes/extend/${passId}`,
                { additional_minutes: additionalMinutes },
                { headers: { Authorization: `Bearer ${token}` } }
              );
              
              Alert.alert('Success', `Pass extended by ${additionalMinutes} minutes`);
              fetchOvertimePasses();
            } catch (error: any) {
              Alert.alert('Error', 'Failed to extend pass');
            } finally {
              setProcessingIds(prev => {
                const newSet = new Set(prev);
                newSet.delete(passId);
                return newSet;
              });
            }
          },
        },
      ],
      'plain-text',
      '5'
    );
  };

  const handleForceEnd = async (passId: string) => {
    Alert.alert(
      'Force End Pass',
      'Are you sure you want to forcefully end this pass?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'End Pass',
          style: 'destructive',
          onPress: async () => {
            setProcessingIds(prev => new Set(prev).add(passId));
            
            try {
              await axios.post(
                `${API_URL}/api/passes/end/${passId}`,
                {},
                { headers: { Authorization: `Bearer ${token}` } }
              );
              
              Alert.alert('Success', 'Pass ended successfully');
              setOvertimePasses(prev => prev.filter(p => p._id !== passId));
            } catch (error: any) {
              Alert.alert('Error', 'Failed to end pass');
            } finally {
              setProcessingIds(prev => {
                const newSet = new Set(prev);
                newSet.delete(passId);
                return newSet;
              });
            }
          },
        },
      ]
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#1E3A5F" />
          <Text style={styles.loadingText}>Loading overtime passes...</Text>
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
        <Text style={styles.headerTitle}>Overtime Passes</Text>
        <View style={styles.placeholder} />
      </View>

      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <View style={styles.statsBar}>
          <View style={styles.stat}>
            <Ionicons name="warning" size={32} color="#EF4444" />
            <Text style={styles.statValue}>{overtimePasses.length}</Text>
            <Text style={styles.statLabel}>Overtime Now</Text>
          </View>
        </View>

        {overtimePasses.length === 0 ? (
          <View style={styles.emptyState}>
            <Ionicons name="checkmark-circle" size={80} color="#10B981" />
            <Text style={styles.emptyTitle}>All Good!</Text>
            <Text style={styles.emptyText}>No passes are currently overtime</Text>
          </View>
        ) : (
          <View style={styles.passesContainer}>
            {overtimePasses.map((pass) => (
              <View key={pass._id} style={styles.passCard}>
                <View style={styles.overtimeBadge}>
                  <Ionicons name="warning" size={16} color="#FFFFFF" />
                  <Text style={styles.overtimeBadgeText}>
                    {pass.minutes_overtime} MIN OVERTIME
                  </Text>
                </View>

                <View style={styles.passHeader}>
                  <View style={styles.studentInfo}>
                    <Ionicons name="person-circle" size={40} color="#EF4444" />
                    <View style={styles.studentDetails}>
                      <Text style={styles.studentName}>{pass.student.name}</Text>
                      <Text style={styles.studentEmail}>{pass.student.email}</Text>
                    </View>
                  </View>
                </View>

                <View style={styles.passDetails}>
                  <View style={styles.detailRow}>
                    <Ionicons name="location" size={20} color="#EF4444" />
                    <Text style={styles.detailLabel}>Destination:</Text>
                    <Text style={styles.detailValue}>{pass.destination_name}</Text>
                  </View>

                  <View style={styles.detailRow}>
                    <Ionicons name="time" size={20} color="#F59E0B" />
                    <Text style={styles.detailLabel}>Expected Return:</Text>
                    <Text style={styles.detailValue}>
                      {new Date(pass.expected_return_time).toLocaleTimeString()}
                    </Text>
                  </View>

                  <View style={styles.detailRow}>
                    <Ionicons name="hourglass" size={20} color="#6B7280" />
                    <Text style={styles.detailLabel}>Started:</Text>
                    <Text style={styles.detailValue}>
                      {new Date(pass.start_time).toLocaleTimeString()}
                    </Text>
                  </View>
                </View>

                <View style={styles.actionButtons}>
                  <TouchableOpacity
                    style={[
                      styles.actionButton,
                      styles.extendButton,
                      processingIds.has(pass._id) && styles.disabledButton,
                    ]}
                    onPress={() => handleExtend(pass._id)}
                    disabled={processingIds.has(pass._id)}
                  >
                    {processingIds.has(pass._id) ? (
                      <ActivityIndicator size="small" color="#FFFFFF" />
                    ) : (
                      <>
                        <Ionicons name="time" size={20} color="#FFFFFF" />
                        <Text style={styles.actionButtonText}>Extend</Text>
                      </>
                    )}
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={[
                      styles.actionButton,
                      styles.endButton,
                      processingIds.has(pass._id) && styles.disabledButton,
                    ]}
                    onPress={() => handleForceEnd(pass._id)}
                    disabled={processingIds.has(pass._id)}
                  >
                    {processingIds.has(pass._id) ? (
                      <ActivityIndicator size="small" color="#FFFFFF" />
                    ) : (
                      <>
                        <Ionicons name="close-circle" size={20} color="#FFFFFF" />
                        <Text style={styles.actionButtonText}>Force End</Text>
                      </>
                    )}
                  </TouchableOpacity>
                </View>
              </View>
            ))}
          </View>
        )}
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
  placeholder: {
    width: 40,
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
  statsBar: {
    backgroundColor: '#FFFFFF',
    padding: 20,
    marginBottom: 8,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  stat: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 48,
    fontWeight: 'bold',
    color: '#EF4444',
    marginVertical: 8,
  },
  statLabel: {
    fontSize: 16,
    color: '#6B7280',
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 48,
    marginTop: 64,
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1E3A5F',
    marginTop: 16,
  },
  emptyText: {
    fontSize: 16,
    color: '#6B7280',
    marginTop: 8,
    textAlign: 'center',
  },
  passesContainer: {
    padding: 16,
    gap: 16,
  },
  passCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    borderWidth: 2,
    borderColor: '#FEE2E2',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  overtimeBadge: {
    backgroundColor: '#EF4444',
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
    marginBottom: 12,
    gap: 6,
  },
  overtimeBadgeText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: 'bold',
  },
  passHeader: {
    marginBottom: 16,
  },
  studentInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  studentDetails: {
    marginLeft: 12,
    flex: 1,
  },
  studentName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1E3A5F',
  },
  studentEmail: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 2,
  },
  passDetails: {
    marginBottom: 16,
    gap: 12,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  detailLabel: {
    fontSize: 14,
    color: '#6B7280',
    fontWeight: '500',
  },
  detailValue: {
    fontSize: 14,
    color: '#374151',
    flex: 1,
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  actionButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    borderRadius: 8,
    gap: 6,
  },
  extendButton: {
    backgroundColor: '#F59E0B',
  },
  endButton: {
    backgroundColor: '#EF4444',
  },
  disabledButton: {
    opacity: 0.5,
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
});