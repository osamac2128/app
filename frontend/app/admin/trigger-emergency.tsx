import React, { useState, useEffect } from 'react';
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
  Modal,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth, API_URL } from '../../contexts/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import axios from 'axios';

interface EmergencyTemplate {
  type: string;
  title: string;
  message: string;
  instructions: string;
  severity: string;
  color: string;
  icon: string;
}

interface ActivePass {
  _id: string;
  student: {
    name: string;
    email: string;
  } | null;
  destination: {
    name: string;
  } | null;
  time_out_minutes: number;
}

export default function TriggerEmergencyScreen() {
  const { token, user } = useAuth();
  const router = useRouter();
  const [sending, setSending] = useState(false);
  const [loadingTemplates, setLoadingTemplates] = useState(true);
  const [templates, setTemplates] = useState<EmergencyTemplate[]>([]);
  const [showTemplateModal, setShowTemplateModal] = useState(false);
  const [showPassesModal, setShowPassesModal] = useState(false);
  const [activePasses, setActivePasses] = useState<ActivePass[]>([]);
  const [loadingPasses, setLoadingPasses] = useState(false);

  const [formData, setFormData] = useState({
    type: 'lockdown',
    severity: 'high',
    title: '',
    message: '',
    instructions: '',
    isDrill: false,
  });

  const emergencyTypes = [
    { value: 'lockdown', label: 'Lockdown', icon: 'lock-closed', color: '#DC2626' },
    { value: 'fire', label: 'Fire', icon: 'flame', color: '#EF4444' },
    { value: 'medical', label: 'Medical', icon: 'medical', color: '#F59E0B' },
    { value: 'tornado', label: 'Tornado', icon: 'thunderstorm', color: '#8B5CF6' },
    { value: 'earthquake', label: 'Earthquake', icon: 'pulse', color: '#9333EA' },
    { value: 'shelter_in_place', label: 'Shelter', icon: 'home', color: '#3B82F6' },
    { value: 'evacuation', label: 'Evacuate', icon: 'exit', color: '#DC2626' },
    { value: 'all_clear', label: 'All Clear', icon: 'checkmark-circle', color: '#10B981' },
  ];

  const severityLevels = [
    { value: 'critical', label: 'Critical', color: '#DC2626' },
    { value: 'high', label: 'High', color: '#EF4444' },
    { value: 'medium', label: 'Medium', color: '#F59E0B' },
    { value: 'low', label: 'Low', color: '#3B82F6' },
    { value: 'info', label: 'Info', color: '#10B981' },
  ];

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/emergency/templates`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setTemplates(response.data);
    } catch (error) {
      console.error('Error fetching templates:', error);
    } finally {
      setLoadingTemplates(false);
    }
  };

  const fetchActivePasses = async () => {
    setLoadingPasses(true);
    try {
      const response = await axios.get(`${API_URL}/api/emergency/active-passes`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setActivePasses(response.data.passes || []);
    } catch (error) {
      console.error('Error fetching active passes:', error);
    } finally {
      setLoadingPasses(false);
    }
  };

  const handleShowPasses = () => {
    setShowPassesModal(true);
    fetchActivePasses();
  };

  const applyTemplate = (template: EmergencyTemplate) => {
    // Check if it's a drill template
    const isDrill = template.type.includes('_drill');
    const baseType = template.type.replace('_drill', '');

    setFormData({
      type: baseType,
      severity: template.severity,
      title: template.title,
      message: template.message,
      instructions: template.instructions,
      isDrill: isDrill,
    });
    setShowTemplateModal(false);
  };

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
                type: formData.isDrill ? `${formData.type}_drill` : formData.type,
                severity: formData.severity,
                title: formData.title,
                message: formData.message,
                instructions: formData.instructions,
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

  const getTypeColor = (type: string) => {
    const found = emergencyTypes.find(t => t.value === type);
    return found?.color || '#6B7280';
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#FFFFFF" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Trigger Emergency</Text>
        <TouchableOpacity onPress={handleShowPasses} style={styles.passesButton}>
          <Ionicons name="people" size={24} color="#FFFFFF" />
        </TouchableOpacity>
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

          {/* Quick Template Button */}
          <TouchableOpacity
            style={styles.templateButton}
            onPress={() => setShowTemplateModal(true)}
          >
            <Ionicons name="document-text" size={24} color="#2E5A8F" />
            <View style={styles.templateButtonText}>
              <Text style={styles.templateButtonTitle}>Use Template</Text>
              <Text style={styles.templateButtonSubtitle}>
                Quick-fill with predefined emergency content
              </Text>
            </View>
            <Ionicons name="chevron-forward" size={24} color="#9CA3AF" />
          </TouchableOpacity>

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
              numberOfLines={4}
              textAlignVertical="top"
            />
          </View>

          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Instructions (Optional)</Text>
            <TextInput
              style={[styles.input, styles.textArea]}
              placeholder="Step-by-step instructions..."
              placeholderTextColor="#9CA3AF"
              value={formData.instructions}
              onChangeText={(text) => setFormData({ ...formData, instructions: text })}
              multiline
              numberOfLines={4}
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

      {/* Template Selection Modal */}
      <Modal visible={showTemplateModal} animationType="slide" transparent={false}>
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setShowTemplateModal(false)}>
              <Ionicons name="close" size={28} color="#1E3A5F" />
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Select Template</Text>
            <View style={{ width: 28 }} />
          </View>

          {loadingTemplates ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#1E3A5F" />
            </View>
          ) : (
            <ScrollView style={styles.templateList}>
              {templates.map((template, index) => (
                <TouchableOpacity
                  key={index}
                  style={styles.templateCard}
                  onPress={() => applyTemplate(template)}
                >
                  <View
                    style={[
                      styles.templateIcon,
                      { backgroundColor: template.color + '20' },
                    ]}
                  >
                    <Ionicons
                      name={template.icon as any}
                      size={28}
                      color={template.color}
                    />
                  </View>
                  <View style={styles.templateInfo}>
                    <Text style={styles.templateTitle}>{template.title}</Text>
                    <Text style={styles.templateSeverity}>
                      {template.severity.toUpperCase()} - {template.type.replace('_', ' ').toUpperCase()}
                    </Text>
                    <Text style={styles.templateMessage} numberOfLines={2}>
                      {template.message}
                    </Text>
                  </View>
                  <Ionicons name="chevron-forward" size={24} color="#9CA3AF" />
                </TouchableOpacity>
              ))}
            </ScrollView>
          )}
        </SafeAreaView>
      </Modal>

      {/* Active Passes Modal */}
      <Modal visible={showPassesModal} animationType="slide" transparent={false}>
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setShowPassesModal(false)}>
              <Ionicons name="close" size={28} color="#1E3A5F" />
            </TouchableOpacity>
            <Text style={styles.modalTitle}>Students in Hallways</Text>
            <TouchableOpacity onPress={fetchActivePasses}>
              <Ionicons name="refresh" size={24} color="#1E3A5F" />
            </TouchableOpacity>
          </View>

          <View style={styles.passesWarning}>
            <Ionicons name="information-circle" size={20} color="#1E3A5F" />
            <Text style={styles.passesWarningText}>
              {activePasses.length} student(s) currently outside classrooms
            </Text>
          </View>

          {loadingPasses ? (
            <View style={styles.loadingContainer}>
              <ActivityIndicator size="large" color="#1E3A5F" />
            </View>
          ) : activePasses.length === 0 ? (
            <View style={styles.emptyState}>
              <Ionicons name="checkmark-circle" size={60} color="#10B981" />
              <Text style={styles.emptyTitle}>All Clear</Text>
              <Text style={styles.emptyText}>No students currently in hallways</Text>
            </View>
          ) : (
            <ScrollView style={styles.passesList}>
              {activePasses.map((pass) => (
                <View key={pass._id} style={styles.passCard}>
                  <View style={styles.passIcon}>
                    <Ionicons name="walk" size={24} color="#F59E0B" />
                  </View>
                  <View style={styles.passInfo}>
                    <Text style={styles.passStudentName}>
                      {pass.student?.name || 'Unknown Student'}
                    </Text>
                    <Text style={styles.passLocation}>
                      Destination: {pass.destination?.name || 'Unknown'}
                    </Text>
                    <Text style={styles.passTime}>
                      Out for {pass.time_out_minutes} min
                    </Text>
                  </View>
                </View>
              ))}
            </ScrollView>
          )}
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
  passesButton: {
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
  templateButton: {
    backgroundColor: '#FFFFFF',
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    marginHorizontal: 16,
    marginTop: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  templateButtonText: {
    flex: 1,
    marginLeft: 12,
  },
  templateButtonTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1E3A5F',
  },
  templateButtonSubtitle: {
    fontSize: 13,
    color: '#6B7280',
    marginTop: 2,
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
    padding: 12,
    width: '22%',
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
    fontSize: 10,
    fontWeight: '600',
    color: '#6B7280',
    marginTop: 6,
    textAlign: 'center',
  },
  severityButtons: {
    flexDirection: 'row',
    gap: 8,
  },
  severityButton: {
    flex: 1,
    backgroundColor: '#F3F4F6',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  severityButtonText: {
    fontSize: 10,
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
    minHeight: 100,
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  templateList: {
    flex: 1,
    padding: 16,
  },
  templateCard: {
    backgroundColor: '#FFFFFF',
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  templateIcon: {
    width: 56,
    height: 56,
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  templateInfo: {
    flex: 1,
    marginLeft: 12,
  },
  templateTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1F2937',
  },
  templateSeverity: {
    fontSize: 12,
    color: '#6B7280',
    marginTop: 2,
  },
  templateMessage: {
    fontSize: 13,
    color: '#9CA3AF',
    marginTop: 4,
  },
  passesWarning: {
    backgroundColor: '#EBF4FF',
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    gap: 12,
  },
  passesWarningText: {
    fontSize: 14,
    color: '#1E3A5F',
    fontWeight: '600',
  },
  passesList: {
    flex: 1,
    padding: 16,
  },
  passCard: {
    backgroundColor: '#FFFFFF',
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  passIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#FEF3C7',
    justifyContent: 'center',
    alignItems: 'center',
  },
  passInfo: {
    flex: 1,
    marginLeft: 12,
  },
  passStudentName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
  },
  passLocation: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 2,
  },
  passTime: {
    fontSize: 12,
    color: '#F59E0B',
    fontWeight: '600',
    marginTop: 4,
  },
  emptyState: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 32,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#10B981',
    marginTop: 16,
  },
  emptyText: {
    fontSize: 16,
    color: '#6B7280',
    marginTop: 8,
  },
});
