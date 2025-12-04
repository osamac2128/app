import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth, API_URL } from '../../contexts/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import axios from 'axios';

export default function TriggerEmergencyScreen() {
  const { token, user } = useAuth();
  const router = useRouter();
  const [sending, setSending] = useState(false);
  const [formData, setFormData] = useState({
    type: 'lockdown',
    severity: 'high',
    title: '',
    message: '',
    isDrill: false,
  });

  const emergencyTypes = [
    { value: 'lockdown', label: 'Lockdown', icon: 'lock-closed', color: '#DC2626' },
    { value: 'fire', label: 'Fire', icon: 'flame', color: '#EF4444' },
    { value: 'medical', label: 'Medical', icon: 'medical', color: '#F59E0B' },
    { value: 'weather', label: 'Weather', icon: 'thunderstorm', color: '#3B82F6' },
    { value: 'earthquake', label: 'Earthquake', icon: 'pulse', color: '#8B5CF6' },
  ];

  const severityLevels = [
    { value: 'critical', label: 'Critical', color: '#DC2626' },
    { value: 'high', label: 'High', color: '#EF4444' },
    { value: 'medium', label: 'Medium', color: '#F59E0B' },
    { value: 'low', label: 'Low', color: '#3B82F6' },
  ];

  const handleTrigger = async () => {
    if (!formData.title.trim() || !formData.message.trim()) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    Alert.alert(
      formData.isDrill ? 'Trigger Drill' : 'Trigger Emergency',
      `This will send a ${formData.type.toUpperCase()} ${formData.isDrill ? 'DRILL' : 'ALERT'} to all users. Continue?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Confirm',
          style: 'destructive',
          onPress: async () => {
            setSending(true);
            try {
              const payload = {
                type: formData.type,
                severity: formData.severity,
                title: formData.title,
                message: formData.message,
                is_drill: formData.isDrill,
                triggered_by: user?._id || '',
              };

              await axios.post(
                `${API_URL}/api/emergency/trigger`,
                payload,
                {
                  headers: { Authorization: `Bearer ${token}` },
                }
              );

              Alert.alert(
                'Success',
                `${formData.isDrill ? 'Drill' : 'Emergency alert'} triggered successfully`,
                [
                  {
                    text: 'OK',
                    onPress: () => router.back(),
                  },
                ]
              );
            } catch (error: any) {
              console.error('Error triggering emergency:', error);
              Alert.alert(
                'Error',
                error.response?.data?.detail || 'Failed to trigger emergency alert'
              );
            } finally {
              setSending(false);
            }
          },
        },
      ]
    );
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#FFFFFF" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Trigger Emergency</Text>
        <View style={styles.backButton} />
      </View>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.container}
      >
        <ScrollView style={styles.scrollView}>
          <View style={styles.warningBanner}>
            <Ionicons name="warning" size={24} color="#DC2626" />
            <Text style={styles.warningText}>
              This will send an alert to all users in the system. Use with caution.
            </Text>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Emergency Type *</Text>
            <View style={styles.typeGrid}>
              {emergencyTypes.map((type) => (
                <TouchableOpacity
                  key={type.value}
                  style={[
                    styles.typeButton,
                    formData.type === type.value && styles.typeButtonActive,
                    formData.type === type.value && {
                      borderColor: type.color,
                      backgroundColor: type.color + '10',
                    },
                  ]}
                  onPress={() => setFormData({ ...formData, type: type.value })}
                >
                  <Ionicons
                    name={type.icon as any}
                    size={28}
                    color={formData.type === type.value ? type.color : '#6B7280'}
                  />
                  <Text
                    style={[
                      styles.typeButtonText,
                      formData.type === type.value && { color: type.color },
                    ]}
                  >
                    {type.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Severity Level *</Text>
            <View style={styles.severityButtons}>
              {severityLevels.map((severity) => (
                <TouchableOpacity
                  key={severity.value}
                  style={[
                    styles.severityButton,
                    formData.severity === severity.value && {
                      backgroundColor: severity.color,
                    },
                  ]}
                  onPress={() => setFormData({ ...formData, severity: severity.value })}
                >
                  <Text
                    style={[
                      styles.severityButtonText,
                      formData.severity === severity.value &&
                        styles.severityButtonTextActive,
                    ]}
                  >
                    {severity.label.toUpperCase()}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Title *</Text>
            <TextInput
              style={styles.input}
              placeholder="e.g., Lockdown in Progress"
              placeholderTextColor="#9CA3AF"
              value={formData.title}
              onChangeText={(text) => setFormData({ ...formData, title: text })}
            />
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Message *</Text>
            <TextInput
              style={[styles.input, styles.textArea]}
              placeholder="Enter detailed instructions for users..."
              placeholderTextColor="#9CA3AF"
              value={formData.message}
              onChangeText={(text) => setFormData({ ...formData, message: text })}
              multiline
              numberOfLines={6}
              textAlignVertical="top"
            />
          </View>

          <View style={styles.section}>
            <TouchableOpacity
              style={styles.drillToggle}
              onPress={() => setFormData({ ...formData, isDrill: !formData.isDrill })}
            >
              <View style={styles.drillToggleLeft}>
                <Ionicons
                  name={formData.isDrill ? 'checkbox' : 'square-outline'}
                  size={24}
                  color={formData.isDrill ? '#2E5A8F' : '#9CA3AF'}
                />
                <Text style={styles.drillToggleText}>This is a drill</Text>
              </View>
              <Text style={styles.drillToggleHint}>
                Users will be notified this is practice
              </Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            style={[
              styles.triggerButton,
              sending && styles.triggerButtonDisabled,
              { backgroundColor: formData.isDrill ? '#2E5A8F' : '#DC2626' },
            ]}
            onPress={handleTrigger}
            disabled={sending}
          >
            {sending ? (
              <ActivityIndicator size="small" color="#FFFFFF" />
            ) : (
              <>
                <Ionicons name="warning" size={20} color="#FFFFFF" />
                <Text style={styles.triggerButtonText}>
                  {formData.isDrill ? 'Trigger Drill' : 'Trigger Emergency'}
                </Text>
              </>
            )}
          </TouchableOpacity>
        </ScrollView>
      </KeyboardAvoidingView>
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
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  container: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  warningBanner: {
    backgroundColor: '#FEE2E2',
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    marginHorizontal: 16,
    marginTop: 16,
    borderRadius: 8,
    gap: 12,
  },
  warningText: {
    flex: 1,
    fontSize: 14,
    color: '#991B1B',
    fontWeight: '600',
  },
  section: {
    paddingHorizontal: 16,
    marginTop: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1E3A5F',
    marginBottom: 12,
  },
  typeGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  typeButton: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    width: '31%',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#E5E7EB',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  typeButtonActive: {
    borderWidth: 2,
  },
  typeButtonText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6B7280',
    marginTop: 8,
    textAlign: 'center',
  },
  severityButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  severityButton: {
    flex: 1,
    backgroundColor: '#F3F4F6',
    paddingVertical: 12,
    borderRadius: 8,
    alignItems: 'center',
  },
  severityButtonText: {
    fontSize: 12,
    color: '#6B7280',
    fontWeight: 'bold',
  },
  severityButtonTextActive: {
    color: '#FFFFFF',
  },
  input: {
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
  drillToggle: {
    backgroundColor: '#FFFFFF',
    borderRadius: 8,
    padding: 16,
    borderWidth: 1,
    borderColor: '#D1D5DB',
  },
  drillToggleLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  drillToggleText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1E3A5F',
  },
  drillToggleHint: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 4,
    marginLeft: 36,
  },
  triggerButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 16,
    borderRadius: 8,
    marginHorizontal: 16,
    marginTop: 32,
    marginBottom: 32,
    gap: 8,
  },
  triggerButtonDisabled: {
    opacity: 0.5,
  },
  triggerButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: 'bold',
  },
});
