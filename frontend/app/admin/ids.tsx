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
  Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth, API_URL } from '../../contexts/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import axios from 'axios';

interface PendingID {
  _id: string;
  user: {
    email: string;
    first_name: string;
    last_name: string;
    role: string;
  };
  submitted_photo_url: string;
  photo_status: string;
  updated_at: string;
}

export default function IDManagementScreen() {
  const { token } = useAuth();
  const router = useRouter();
  const [pendingIDs, setPendingIDs] = useState<PendingID[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [processingIds, setProcessingIds] = useState<Set<string>>(new Set());

  const fetchPendingIDs = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/admin/ids/pending-approvals`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setPendingIDs(response.data);
    } catch (error: any) {
      console.error('Error fetching pending IDs:', error);
      Alert.alert('Error', 'Failed to load pending ID approvals');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchPendingIDs();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchPendingIDs();
  };

  const handleApprove = async (idId: string) => {
    setProcessingIds(prev => new Set(prev).add(idId));
    
    try {
      await axios.post(
        `${API_URL}/api/digital-ids/approve-photo/${idId}?approved=true`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      Alert.alert('Success', 'Photo approved successfully');
      setPendingIDs(prev => prev.filter(id => id._id !== idId));
    } catch (error: any) {
      console.error('Error approving photo:', error);
      Alert.alert('Error', error.response?.data?.detail || 'Failed to approve photo');
    } finally {
      setProcessingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(idId);
        return newSet;
      });
    }
  };

  const handleReject = async (idId: string) => {
    Alert.alert(
      'Reject Photo',
      'Are you sure you want to reject this photo? The user will need to submit a new one.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Reject',
          style: 'destructive',
          onPress: async () => {
            setProcessingIds(prev => new Set(prev).add(idId));
            
            try {
              await axios.post(
                `${API_URL}/api/digital-ids/approve-photo/${idId}?approved=false`,
                {},
                { headers: { Authorization: `Bearer ${token}` } }
              );
              
              Alert.alert('Success', 'Photo rejected');
              setPendingIDs(prev => prev.filter(id => id._id !== idId));
            } catch (error: any) {
              console.error('Error rejecting photo:', error);
              Alert.alert('Error', 'Failed to reject photo');
            } finally {
              setProcessingIds(prev => {
                const newSet = new Set(prev);
                newSet.delete(idId);
                return newSet;
              });
            }
          },
        },
      ]
    );
  };

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'student':
        return '#2E5A8F';
      case 'staff':
        return '#10B981';
      case 'parent':
        return '#F59E0B';
      case 'admin':
        return '#EF4444';
      default:
        return '#6B7280';
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#1E3A5F" />
          <Text style={styles.loadingText}>Loading pending approvals...</Text>
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
        <Text style={styles.headerTitle}>ID Approvals</Text>
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
            <Text style={styles.statValue}>{pendingIDs.length}</Text>
            <Text style={styles.statLabel}>Pending</Text>
          </View>
        </View>

        {pendingIDs.length === 0 ? (
          <View style={styles.emptyState}>
            <Ionicons name="checkmark-circle" size={80} color="#10B981" />
            <Text style={styles.emptyTitle}>All Caught Up!</Text>
            <Text style={styles.emptyText}>No ID photos pending approval</Text>
          </View>
        ) : (
          <View style={styles.idsContainer}>
            {pendingIDs.map((id) => (
              <View key={id._id} style={styles.idCard}>
                <View style={styles.idHeader}>
                  <View style={styles.userInfo}>
                    <View style={styles.avatarContainer}>
                      {id.submitted_photo_url ? (
                        <Image
                          source={{ uri: id.submitted_photo_url }}
                          style={styles.avatar}
                        />
                      ) : (
                        <View style={styles.avatarPlaceholder}>
                          <Ionicons name="person" size={40} color="#9CA3AF" />
                        </View>
                      )}
                    </View>
                    <View style={styles.userDetails}>
                      <Text style={styles.userName}>
                        {id.user.first_name} {id.user.last_name}
                      </Text>
                      <Text style={styles.userEmail}>{id.user.email}</Text>
                      <View style={[styles.roleBadge, { backgroundColor: getRoleBadgeColor(id.user.role) + '20' }]}>
                        <Text style={[styles.roleBadgeText, { color: getRoleBadgeColor(id.user.role) }]}>
                          {id.user.role.toUpperCase()}
                        </Text>
                      </View>
                    </View>
                  </View>
                </View>

                {id.submitted_photo_url && (
                  <View style={styles.photoPreviewContainer}>
                    <Text style={styles.photoPreviewLabel}>Submitted Photo:</Text>
                    <Image
                      source={{ uri: id.submitted_photo_url }}
                      style={styles.photoPreview}
                      resizeMode="cover"
                    />
                  </View>
                )}

                <View style={styles.actionButtons}>
                  <TouchableOpacity
                    style={[
                      styles.actionButton,
                      styles.rejectButton,
                      processingIds.has(id._id) && styles.disabledButton,
                    ]}
                    onPress={() => handleReject(id._id)}
                    disabled={processingIds.has(id._id)}
                    activeOpacity={0.7}
                  >
                    {processingIds.has(id._id) ? (
                      <ActivityIndicator size="small" color="#FFFFFF" />
                    ) : (
                      <>
                        <Ionicons name="close-circle" size={24} color="#FFFFFF" />
                        <Text style={styles.actionButtonText}>Reject</Text>
                      </>
                    )}
                  </TouchableOpacity>

                  <TouchableOpacity
                    style={[
                      styles.actionButton,
                      styles.approveButton,
                      processingIds.has(id._id) && styles.disabledButton,
                    ]}
                    onPress={() => handleApprove(id._id)}
                    disabled={processingIds.has(id._id)}
                    activeOpacity={0.7}
                  >
                    {processingIds.has(id._id) ? (
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
  idsContainer: {
    padding: 16,
    gap: 16,
  },
  idCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  idHeader: {
    marginBottom: 16,
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatarContainer: {
    marginRight: 12,
  },
  avatar: {
    width: 64,
    height: 64,
    borderRadius: 32,
  },
  avatarPlaceholder: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#F3F4F6',
    justifyContent: 'center',
    alignItems: 'center',
  },
  userDetails: {
    flex: 1,
  },
  userName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1E3A5F',
  },
  userEmail: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 2,
  },
  roleBadge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    marginTop: 6,
  },
  roleBadgeText: {
    fontSize: 11,
    fontWeight: 'bold',
  },
  photoPreviewContainer: {
    marginBottom: 16,
  },
  photoPreviewLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  photoPreview: {
    width: '100%',
    height: 300,
    borderRadius: 8,
    backgroundColor: '#F3F4F6',
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
  rejectButton: {
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
