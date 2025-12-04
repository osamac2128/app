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
  TextInput,
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth, API_URL } from '../../contexts/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import axios from 'axios';

interface Notification {
  _id: string;
  title: string;
  body: string; // Backend uses "body" not "message"
  type: string;
  priority?: string; // Optional as backend doesn't have this field
  created_at: string;
  recipient_count?: number;
}

export default function AdminMessagesScreen() {
  const { token } = useAuth();
  const router = useRouter();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showComposeModal, setShowComposeModal] = useState(false);
  const [sending, setSending] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    title: '',
    message: '',
    type: 'announcement',
    priority: 'normal',
    target: 'all',
  });

  const fetchNotifications = async () => {
    try {
      // Fetch notifications sent by this admin
      const response = await axios.get(`${API_URL}/api/notifications/sent`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setNotifications(response.data);
    } catch (error: any) {
      console.error('Error fetching notifications:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchNotifications();
  };

  const handleCompose = () => {
    setFormData({
      title: '',
      message: '',
      type: 'announcement',
      priority: 'normal',
      target: 'all',
    });
    setShowComposeModal(true);
  };

  const handleSend = async () => {
    if (!formData.title.trim() || !formData.message.trim()) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    setSending(true);
    
    try {
      // Map frontend target to backend target_roles
      let target_roles = null;
      if (formData.target !== 'all') {
        // Map target to role format expected by backend
        const roleMap: any = {
          'students': 'student',
          'parents': 'parent',
          'staff': 'staff'
        };
        target_roles = [roleMap[formData.target]];
      }

      // Map frontend type to backend NotificationType enum
      const typeMap: any = {
        'announcement': 'announcement',
        'alert': 'urgent',
        'reminder': 'reminder',
        'info': 'general'
      };

      const notificationData = {
        title: formData.title,
        body: formData.message, // Backend uses "body" not "message"
        type: typeMap[formData.type],
        target_roles: target_roles,
        created_by: '' // Will be set by backend from token
      };

      const response = await axios.post(
        `${API_URL}/api/notifications/send`,
        notificationData,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (response.status === 200) {
        Alert.alert(
          'Message Sent',
          `Your ${formData.type} has been sent to ${formData.target === 'all' ? 'all users' : formData.target}.`,
          [
            {
              text: 'OK',
              onPress: () => {
                setShowComposeModal(false);
                fetchNotifications();
              },
            },
          ]
        );
      }
    } catch (error: any) {
      console.error('Error sending notification:', error);
      Alert.alert('Error', error.response?.data?.detail || 'Failed to send message');
    } finally {
      setSending(false);
    }
  };

  const getTypeColor = (type: string) => {
    const colors: any = {
      announcement: '#2E5A8F',
      alert: '#EF4444',
      reminder: '#F59E0B',
      info: '#10B981',
    };
    return colors[type] || '#6B7280';
  };

  const getTypeIcon = (type: string) => {
    const icons: any = {
      announcement: 'megaphone',
      alert: 'warning',
      reminder: 'time',
      info: 'information-circle',
    };
    return icons[type] || 'notifications';
  };

  const getPriorityBadge = (priority: string) => {
    const badges: any = {
      high: { color: '#EF4444', text: 'HIGH' },
      normal: { color: '#10B981', text: 'NORMAL' },
      low: { color: '#6B7280', text: 'LOW' },
    };
    return badges[priority] || badges.normal;
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#1E3A5F" />
          <Text style={styles.loadingText}>Loading messages...</Text>
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
        <Text style={styles.headerTitle}>Messages</Text>
        <TouchableOpacity onPress={handleCompose} style={styles.composeButton}>
          <Ionicons name="create" size={24} color="#FFFFFF" />
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <View style={styles.statsBar}>
          <View style={styles.stat}>
            <Text style={styles.statValue}>{notifications.length}</Text>
            <Text style={styles.statLabel}>Total Messages</Text>
          </View>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Recent Messages</Text>
          {notifications.length === 0 ? (
            <View style={styles.emptyState}>
              <Ionicons name="chatbubbles" size={80} color="#9CA3AF" />
              <Text style={styles.emptyTitle}>No Messages</Text>
              <Text style={styles.emptyText}>Send your first message to users</Text>
              <TouchableOpacity style={styles.emptyButton} onPress={handleCompose}>
                <Ionicons name="create" size={20} color="#FFFFFF" />
                <Text style={styles.emptyButtonText}>Compose Message</Text>
              </TouchableOpacity>
            </View>
          ) : (
            notifications.map((notification) => (
              <View key={notification._id} style={styles.messageCard}>
                <View style={styles.messageHeader}>
                  <View
                    style={[
                      styles.typeIcon,
                      { backgroundColor: getTypeColor(notification.type) + '20' },
                    ]}
                  >
                    <Ionicons
                      name={getTypeIcon(notification.type) as any}
                      size={24}
                      color={getTypeColor(notification.type)}
                    />
                  </View>
                  <View style={styles.messageInfo}>
                    <Text style={styles.messageTitle}>{notification.title}</Text>
                    <Text style={styles.messageType}>{notification.type.toUpperCase()}</Text>
                  </View>
                  {notification.priority && (
                    <View
                      style={[
                        styles.priorityBadge,
                        { backgroundColor: getPriorityBadge(notification.priority).color },
                      ]}
                    >
                      <Text style={styles.priorityText}>
                        {getPriorityBadge(notification.priority).text}
                      </Text>
                    </View>
                  )}
                </View>

                <Text style={styles.messageContent}>{notification.body}</Text>

                <View style={styles.messageFooter}>
                  <Text style={styles.messageDate}>
                    {new Date(notification.created_at).toLocaleString()}
                  </Text>
                  {notification.recipient_count && (
                    <View style={styles.recipientCount}>
                      <Ionicons name="people" size={16} color="#6B7280" />
                      <Text style={styles.recipientText}>
                        {notification.recipient_count} recipients
                      </Text>
                    </View>
                  )}
                </View>
              </View>
            ))
          )}
        </View>
      </ScrollView>

      {/* Compose Modal */}
      <Modal visible={showComposeModal} animationType="slide" transparent={false}>
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setShowComposeModal(false)}>
              <Ionicons name="close" size={28} color="#1E3A5F" />
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Compose Message</Text>
            <TouchableOpacity onPress={handleSend} disabled={sending}>
              <Ionicons name="send" size={28} color={sending ? '#9CA3AF' : '#10B981'} />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalContent}>
            <View style={styles.formGroup}>
              <Text style={styles.formLabel}>Target Audience *</Text>
              <View style={styles.targetButtons}>
                {['all', 'students', 'parents', 'staff'].map((target) => (
                  <TouchableOpacity
                    key={target}
                    style={[
                      styles.targetButton,
                      formData.target === target && styles.targetButtonActive,
                    ]}
                    onPress={() => setFormData({ ...formData, target })}
                  >
                    <Text
                      style={[
                        styles.targetButtonText,
                        formData.target === target && styles.targetButtonTextActive,
                      ]}
                    >
                      {target === 'all' ? 'All Users' : target.charAt(0).toUpperCase() + target.slice(1)}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <View style={styles.formGroup}>
              <Text style={styles.formLabel}>Message Type *</Text>
              <View style={styles.typeButtons}>
                {['announcement', 'alert', 'reminder', 'info'].map((type) => (
                  <TouchableOpacity
                    key={type}
                    style={[
                      styles.typeButton,
                      formData.type === type && styles.typeButtonActive,
                    ]}
                    onPress={() => setFormData({ ...formData, type })}
                  >
                    <Ionicons
                      name={getTypeIcon(type) as any}
                      size={20}
                      color={formData.type === type ? '#FFFFFF' : '#6B7280'}
                    />
                    <Text
                      style={[
                        styles.typeButtonText,
                        formData.type === type && styles.typeButtonTextActive,
                      ]}
                    >
                      {type.charAt(0).toUpperCase() + type.slice(1)}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <View style={styles.formGroup}>
              <Text style={styles.formLabel}>Priority *</Text>
              <View style={styles.priorityButtons}>
                {['high', 'normal', 'low'].map((priority) => (
                  <TouchableOpacity
                    key={priority}
                    style={[
                      styles.priorityButton,
                      formData.priority === priority && styles.priorityButtonActive,
                    ]}
                    onPress={() => setFormData({ ...formData, priority })}
                  >
                    <Text
                      style={[
                        styles.priorityButtonText,
                        formData.priority === priority && styles.priorityButtonTextActive,
                      ]}
                    >
                      {priority.toUpperCase()}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>
            </View>

            <View style={styles.formGroup}>
              <Text style={styles.formLabel}>Title *</Text>
              <TextInput
                style={styles.formInput}
                value={formData.title}
                onChangeText={(text) => setFormData({ ...formData, title: text })}
                placeholder="Enter message title"
                placeholderTextColor="#9CA3AF"
              />
            </View>

            <View style={styles.formGroup}>
              <Text style={styles.formLabel}>Message *</Text>
              <TextInput
                style={[styles.formInput, styles.textArea]}
                value={formData.message}
                onChangeText={(text) => setFormData({ ...formData, message: text })}
                placeholder="Enter your message"
                placeholderTextColor="#9CA3AF"
                multiline
                numberOfLines={6}
                textAlignVertical="top"
              />
            </View>

            <TouchableOpacity
              style={[styles.sendButton, sending && styles.sendButtonDisabled]}
              onPress={handleSend}
              disabled={sending}
            >
              {sending ? (
                <ActivityIndicator size="small" color="#FFFFFF" />
              ) : (
                <>
                  <Ionicons name="send" size={20} color="#FFFFFF" />
                  <Text style={styles.sendButtonText}>Send Message</Text>
                </>
              )}
            </TouchableOpacity>
          </ScrollView>
        </SafeAreaView>
      </Modal>
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
  composeButton: {
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
    fontSize: 32,
    fontWeight: 'bold',
    color: '#1E3A5F',
  },
  statLabel: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
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
  emptyState: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 48,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  emptyTitle: {
    fontSize: 20,
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
  emptyButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2E5A8F',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    marginTop: 24,
    gap: 8,
  },
  emptyButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  messageCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  messageHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  typeIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  messageInfo: {
    flex: 1,
  },
  messageTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1E3A5F',
  },
  messageType: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  priorityBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  priorityText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: 'bold',
  },
  messageContent: {
    fontSize: 14,
    color: '#374151',
    lineHeight: 20,
    marginBottom: 12,
  },
  messageFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  messageDate: {
    fontSize: 12,
    color: '#9CA3AF',
  },
  recipientCount: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  recipientText: {
    fontSize: 12,
    color: '#6B7280',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#F5F7FA',
  },
  modalHeader: {
    backgroundColor: '#FFFFFF',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1E3A5F',
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  formGroup: {
    marginBottom: 24,
  },
  formLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  formInput: {
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: '#D1D5DB',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    color: '#1F2937',
  },
  textArea: {
    minHeight: 120,
  },
  targetButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  targetButton: {
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  targetButtonActive: {
    backgroundColor: '#2E5A8F',
    borderColor: '#2E5A8F',
  },
  targetButtonText: {
    fontSize: 14,
    color: '#6B7280',
    fontWeight: '600',
  },
  targetButtonTextActive: {
    color: '#FFFFFF',
  },
  typeButtons: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  typeButton: {
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  typeButtonActive: {
    backgroundColor: '#2E5A8F',
    borderColor: '#2E5A8F',
  },
  typeButtonText: {
    fontSize: 14,
    color: '#6B7280',
    fontWeight: '600',
  },
  typeButtonTextActive: {
    color: '#FFFFFF',
  },
  priorityButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  priorityButton: {
    flex: 1,
    backgroundColor: '#F3F4F6',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
    borderWidth: 2,
    borderColor: 'transparent',
  },
  priorityButtonActive: {
    backgroundColor: '#2E5A8F',
    borderColor: '#2E5A8F',
  },
  priorityButtonText: {
    fontSize: 14,
    color: '#6B7280',
    fontWeight: 'bold',
  },
  priorityButtonTextActive: {
    color: '#FFFFFF',
  },
  sendButton: {
    backgroundColor: '#10B981',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 8,
    gap: 8,
    marginTop: 8,
  },
  sendButtonDisabled: {
    opacity: 0.5,
  },
  sendButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
