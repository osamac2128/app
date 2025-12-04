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

interface PendingPass {
  _id: string;
  student: {
    name: string;
    email: string;
  };
  origin_name?: string;
  destination_name: string;
  time_limit_minutes: number;
  created_at: string;
  notes?: string;
}

export default function PassApprovalScreen() {
  const { user, token } = useAuth();
  const router = useRouter();
  const [pendingPasses, setPendingPasses] = useState<PendingPass[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [processingIds, setProcessingIds] = useState<Set<string>>(new Set());

  const fetchPendingPasses = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/passes/teacher/pending`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setPendingPasses(response.data);
    } catch (error: any) {
      console.error('Error fetching pending passes:', error);
      Alert.alert('Error', 'Failed to load pending passes');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    if (user?.role === 'staff' || user?.role === 'admin') {
      fetchPendingPasses();
    } else {
      Alert.alert('Access Denied', 'This feature is only available to staff');
      router.back();
    }
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchPendingPasses();
  };

  const handleApprove = async (passId: string) => {
    setProcessingIds(prev => new Set(prev).add(passId));
    
    try {
      await axios.post(
        `${API_URL}/api/passes/approve/${passId}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      Alert.alert('Success', 'Pass approved successfully');
      
      // Remove from list
      setPendingPasses(prev => prev.filter(p => p._id !== passId));
    } catch (error: any) {
      console.error('Error approving pass:', error);
      Alert.alert('Error', error.response?.data?.detail || 'Failed to approve pass');
    } finally {
      setProcessingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(passId);
        return newSet;
      });
    }
  };

  const handleDeny = async (passId: string) => {
    Alert.prompt(
      'Deny Pass',
      'Please provide a reason for denial (optional):',
      [
        {
          text: 'Cancel',
          style: 'cancel',
        },
        {
          text: 'Deny',
          style: 'destructive',
          onPress: async (reason) => {
            setProcessingIds(prev => new Set(prev).add(passId));
            
            try {
              await axios.post(
                `${API_URL}/api/passes/deny/${passId}`,
                { reason },
                { headers: { Authorization: `Bearer ${token}` } }
              );
              
              Alert.alert('Success', 'Pass denied');
              
              // Remove from list
              setPendingPasses(prev => prev.filter(p => p._id !== passId));
            } catch (error: any) {
              console.error('Error denying pass:', error);
              Alert.alert('Error', error.response?.data?.detail || 'Failed to deny pass');
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
      'plain-text'
    );
  };

  const handleBulkApprove = async () => {
    if (pendingPasses.length === 0) return;

    Alert.alert(
      'Bulk Approve',
      `Approve all ${pendingPasses.length} pending passes?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Approve All',
          onPress: async () => {
            setLoading(true);
            
            try {
              const passIds = pendingPasses.map(p => p._id);
              
              await axios.post(
                `${API_URL}/api/passes/bulk-approve`,
                { pass_ids: passIds },
                { headers: { Authorization: `Bearer ${token}` } }
              );
              
              Alert.alert('Success', `Approved ${passIds.length} passes`);
              setPendingPasses([]);
            } catch (error: any) {
              console.error('Error bulk approving:', error);
              Alert.alert('Error', 'Failed to approve all passes');
            } finally {
              setLoading(false);
            }
          },
        },
      ]
    );
  };

  const formatTimeAgo = (dateString: string) => {
    const now = new Date();
    const created = new Date(dateString);
    const diffMs = now.getTime() - created.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${Math.floor(diffHours / 24)}d ago`;
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#1E3A5F" />
          <Text style={styles.loadingText}>Loading pending passes...</Text>
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
        <Text style={styles.headerTitle}>Pass Approvals</Text>
        {pendingPasses.length > 0 && (
          <TouchableOpacity onPress={handleBulkApprove} style={styles.bulkButton}>
            <Ionicons name="checkmark-done" size={24} color="#FFFFFF" />
          </TouchableOpacity>
        )}
      </View>

      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <View style={styles.statsBar}>
          <View style={styles.stat}>
            <Text style={styles.statValue}>{pendingPasses.length}</Text>
            <Text style={styles.statLabel}>Pending</Text>
          </View>
        </View>

        {pendingPasses.length === 0 ? (
          <View style={styles.emptyState}>
            <Ionicons name="checkmark-circle" size={80} color="#10B981" />
            <Text style={styles.emptyTitle}>All Caught Up!</Text>
            <Text style={styles.emptyText}>No passes pending approval</Text>
          </View>
        ) : (
          <View style={styles.passesContainer}>
            {pendingPasses.map((pass) => (
              <View key={pass._id} style={styles.passCard}>
                <View style={styles.passHeader}>
                  <View style={styles.studentInfo}>
                    <Ionicons name="person-circle" size={40} color="#2E5A8F" />
                    <View style={styles.studentDetails}>
                      <Text style={styles.studentName}>{pass.student.name}</Text>
                      <Text style={styles.studentEmail}>{pass.student.email}</Text>
                    </View>
                  </View>
                  <Text style={styles.timeAgo}>{formatTimeAgo(pass.created_at)}</Text>
                </View>

                <View style={styles.passDetails}>
                  <View style={styles.detailRow}>
                    <Ionicons name="navigate" size={20} color="#6B7280" />
                    <Text style={styles.detailLabel}>From:</Text>
                    <Text style={styles.detailValue}>
                      {pass.origin_name || 'Current Location'}
                    </Text>
                  </View>

                  <View style={styles.detailRow}>
                    <Ionicons name="location" size={20} color="#2E5A8F" />
                    <Text style={styles.detailLabel}>To:</Text>
                    <Text style={styles.detailValue}>{pass.destination_name}</Text>
                  </View>

                  <View style={styles.detailRow}>
                    <Ionicons name="time" size={20} color="#10B981" />
                    <Text style={styles.detailLabel}>Duration:</Text>
                    <Text style={styles.detailValue}>{pass.time_limit_minutes} min</Text>
                  </View>

                  {pass.notes && (
                    <View style={styles.notesContainer}>
                      <Text style={styles.notesLabel}>Notes:</Text>
                      <Text style={styles.notesText}>{pass.notes}</Text>
                    </View>
                  )}
                </View>

                <View style={styles.actionButtons}>
                  <TouchableOpacity
                    style={[
                      styles.actionButton,
                      styles.denyButton,
                      processingIds.has(pass._id) && styles.disabledButton,
                    ]}
                    onPress={() => handleDeny(pass._id)}
                    disabled={processingIds.has(pass._id)}
                    activeOpacity={0.7}
                  >
                    {processingIds.has(pass._id) ? (
                      <ActivityIndicator size="small" color="#FFFFFF" />
                    ) : (
                      <>
                        <Ionicons name="close-circle" size={24} color="#FFFFFF" />
                        <Text style={styles.actionButtonText}>Deny</Text>
                      </>
                    )}
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={[
                      styles.actionButton,
                      styles.approveButton,
                      processingIds.has(pass._id) && styles.disabledButton,
                    ]}
                    onPress={() => handleApprove(pass._id)}
                    disabled={processingIds.has(pass._id)}
                    activeOpacity={0.7}
                  >
                    {processingIds.has(pass._id) ? (
                      <ActivityIndicator size="small" color="#FFFFFF" />
                    ) : (
                      <>
                        <Ionicons name="checkmark-circle" size={24} color="#FFFFFF" />
                        <Text style={styles.actionButtonText}>Approve</Text>
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
  bulkButton: {
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
  statsBar: {
    backgroundColor: '#FFFFFF',
    flexDirection: 'row',
    padding: 20,
    marginBottom: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  stat: {
    flex: 1,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#1E3A5F',
  },
  statLabel: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
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
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  passHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  studentInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
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
  timeAgo: {
    fontSize: 12,
    color: '#9CA3AF',
    marginLeft: 8,
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
  notesContainer: {
    backgroundColor: '#F9FAFB',
    padding: 12,
    borderRadius: 8,
    marginTop: 4,
  },
  notesLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6B7280',
    marginBottom: 4,
  },
  notesText: {
    fontSize: 14,
    color: '#374151',
    lineHeight: 20,
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
    padding: 14,
    borderRadius: 8,
    gap: 8,
  },
  denyButton: {
    backgroundColor: '#EF4444',
  },
  approveButton: {
    backgroundColor: '#10B981',
  },
  disabledButton: {
    opacity: 0.5,
  },
  actionButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
});
