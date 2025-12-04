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

interface Location {
  _id: string;
  name: string;
  type: string;
  building?: string;
  floor?: string;
  room_number?: string;
  max_capacity?: number;
  requires_approval: boolean;
  default_time_limit_minutes: number;
  is_active: boolean;
}

export default function LocationManagementScreen() {
  const { token } = useAuth();
  const router = useRouter();
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingLocation, setEditingLocation] = useState<Location | null>(null);

  // Form state
  const [formData, setFormData] = useState({
    name: '',
    type: 'other',
    building: '',
    floor: '',
    room_number: '',
    max_capacity: '',
    requires_approval: false,
    default_time_limit_minutes: '5',
  });

  const locationTypes = [
    'classroom', 'bathroom', 'office', 'library', 'gym', 
    'cafeteria', 'nurse', 'counselor', 'other'
  ];

  const fetchLocations = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/admin/locations/all?include_inactive=true`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setLocations(response.data);
    } catch (error: any) {
      console.error('Error fetching locations:', error);
      Alert.alert('Error', 'Failed to load locations');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchLocations();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchLocations();
  };

  const resetForm = () => {
    setFormData({
      name: '',
      type: 'other',
      building: '',
      floor: '',
      room_number: '',
      max_capacity: '',
      requires_approval: false,
      default_time_limit_minutes: '5',
    });
    setEditingLocation(null);
  };

  const handleAdd = () => {
    resetForm();
    setShowAddModal(true);
  };

  const handleEdit = (location: Location) => {
    setFormData({
      name: location.name,
      type: location.type,
      building: location.building || '',
      floor: location.floor || '',
      room_number: location.room_number || '',
      max_capacity: location.max_capacity?.toString() || '',
      requires_approval: location.requires_approval,
      default_time_limit_minutes: location.default_time_limit_minutes.toString(),
    });
    setEditingLocation(location);
    setShowAddModal(true);
  };

  const handleSave = async () => {
    if (!formData.name.trim()) {
      Alert.alert('Error', 'Location name is required');
      return;
    }

    const payload = {
      name: formData.name.trim(),
      type: formData.type,
      building: formData.building.trim() || null,
      floor: formData.floor.trim() || null,
      room_number: formData.room_number.trim() || null,
      max_capacity: formData.max_capacity ? parseInt(formData.max_capacity) : null,
      requires_approval: formData.requires_approval,
      default_time_limit_minutes: parseInt(formData.default_time_limit_minutes) || 5,
    };

    try {
      if (editingLocation) {
        await axios.put(
          `${API_URL}/api/admin/locations/${editingLocation._id}`,
          payload,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        Alert.alert('Success', 'Location updated successfully');
      } else {
        await axios.post(
          `${API_URL}/api/admin/locations`,
          payload,
          { headers: { Authorization: `Bearer ${token}` } }
        );
        Alert.alert('Success', 'Location created successfully');
      }
      
      setShowAddModal(false);
      resetForm();
      fetchLocations();
    } catch (error: any) {
      console.error('Error saving location:', error);
      Alert.alert('Error', error.response?.data?.detail || 'Failed to save location');
    }
  };

  const handleToggleStatus = async (location: Location) => {
    const action = location.is_active ? 'deactivate' : 'activate';
    
    Alert.alert(
      `${action.charAt(0).toUpperCase() + action.slice(1)} Location`,
      `Are you sure you want to ${action} "${location.name}"?`,
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: action.charAt(0).toUpperCase() + action.slice(1),
          onPress: async () => {
            try {
              await axios.delete(`${API_URL}/api/admin/locations/${location._id}`, {
                headers: { Authorization: `Bearer ${token}` },
              });
              Alert.alert('Success', `Location ${action}d successfully`);
              fetchLocations();
            } catch (error: any) {
              Alert.alert('Error', `Failed to ${action} location`);
            }
          },
        },
      ]
    );
  };

  const getLocationIcon = (type: string) => {
    const icons: any = {
      classroom: 'school',
      bathroom: 'water',
      office: 'briefcase',
      library: 'book',
      gym: 'fitness',
      cafeteria: 'restaurant',
      nurse: 'medical',
      counselor: 'people',
      other: 'location',
    };
    return icons[type] || 'location';
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#1E3A5F" />
          <Text style={styles.loadingText}>Loading locations...</Text>
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
        <Text style={styles.headerTitle}>Locations</Text>
        <TouchableOpacity onPress={handleAdd} style={styles.addButton}>
          <Ionicons name="add-circle" size={24} color="#FFFFFF" />
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
            <Text style={styles.statValue}>{locations.filter(l => l.is_active).length}</Text>
            <Text style={styles.statLabel}>Active</Text>
          </View>
          <View style={styles.stat}>
            <Text style={styles.statValue}>{locations.filter(l => !l.is_active).length}</Text>
            <Text style={styles.statLabel}>Inactive</Text>
          </View>
          <View style={styles.stat}>
            <Text style={styles.statValue}>{locations.length}</Text>
            <Text style={styles.statLabel}>Total</Text>
          </View>
        </View>

        <View style={styles.locationsContainer}>
          {locations.map((location) => (
            <View
              key={location._id}
              style={[
                styles.locationCard,
                !location.is_active && styles.inactiveCard,
              ]}
            >
              <View style={styles.locationHeader}>
                <View style={styles.locationInfo}>
                  <View style={[styles.iconCircle, { backgroundColor: location.is_active ? '#2E5A8F20' : '#9CA3AF20' }]}>
                    <Ionicons
                      name={getLocationIcon(location.type) as any}
                      size={28}
                      color={location.is_active ? '#2E5A8F' : '#9CA3AF'}
                    />
                  </View>
                  <View style={styles.locationDetails}>
                    <Text style={styles.locationName}>{location.name}</Text>
                    <Text style={styles.locationType}>{location.type}</Text>
                  </View>
                </View>
                
                {!location.is_active && (
                  <View style={styles.inactiveBadge}>
                    <Text style={styles.inactiveBadgeText}>Inactive</Text>
                  </View>
                )}
              </View>

              <View style={styles.locationMeta}>
                {location.building && (
                  <View style={styles.metaItem}>
                    <Ionicons name="business" size={16} color="#6B7280" />
                    <Text style={styles.metaText}>{location.building}</Text>
                  </View>
                )}
                {location.floor && (
                  <View style={styles.metaItem}>
                    <Ionicons name="layers" size={16} color="#6B7280" />
                    <Text style={styles.metaText}>Floor {location.floor}</Text>
                  </View>
                )}
                {location.room_number && (
                  <View style={styles.metaItem}>
                    <Ionicons name="door-open" size={16} color="#6B7280" />
                    <Text style={styles.metaText}>Room {location.room_number}</Text>
                  </View>
                )}
              </View>

              <View style={styles.locationSettings}>
                <View style={styles.settingRow}>
                  <Ionicons name="time" size={16} color="#10B981" />
                  <Text style={styles.settingText}>{location.default_time_limit_minutes} min default</Text>
                </View>
                {location.max_capacity && (
                  <View style={styles.settingRow}>
                    <Ionicons name="people" size={16} color="#F59E0B" />
                    <Text style={styles.settingText}>Max {location.max_capacity}</Text>
                  </View>
                )}
                {location.requires_approval && (
                  <View style={styles.settingRow}>
                    <Ionicons name="checkmark-circle" size={16} color="#EF4444" />
                    <Text style={styles.settingText}>Requires Approval</Text>
                  </View>
                )}
              </View>

              <View style={styles.actionButtons}>
                <TouchableOpacity
                  style={[styles.actionButton, styles.editButton]}
                  onPress={() => handleEdit(location)}
                >
                  <Ionicons name="create" size={20} color="#2E5A8F" />
                  <Text style={styles.editButtonText}>Edit</Text>
                </TouchableOpacity>

                <TouchableOpacity
                  style={[styles.actionButton, location.is_active ? styles.deactivateButton : styles.activateButton]}
                  onPress={() => handleToggleStatus(location)}
                >
                  <Ionicons
                    name={location.is_active ? 'close-circle' : 'checkmark-circle'}
                    size={20}
                    color="#FFFFFF"
                  />
                  <Text style={styles.actionButtonText}>
                    {location.is_active ? 'Deactivate' : 'Activate'}
                  </Text>
                </TouchableOpacity>
              </View>
            </View>
          ))}
        </View>
      </ScrollView>

      {/* Add/Edit Modal */}
      <Modal
        visible={showAddModal}
        animationType="slide"
        transparent={false}
      >
        <SafeAreaView style={styles.modalContainer}>
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => { setShowAddModal(false); resetForm(); }}>
              <Ionicons name="close" size={28} color="#1E3A5F" />
            </TouchableOpacity>
            <Text style={styles.modalTitle}>
              {editingLocation ? 'Edit Location' : 'Add Location'}
            </Text>
            <TouchableOpacity onPress={handleSave}>
              <Ionicons name="checkmark" size={28} color="#10B981" />
            </TouchableOpacity>
          </View>

          <ScrollView style={styles.modalContent}>
            <View style={styles.formGroup}>
              <Text style={styles.formLabel}>Name *</Text>
              <TextInput
                style={styles.formInput}
                value={formData.name}
                onChangeText={(text) => setFormData({ ...formData, name: text })}
                placeholder="Enter location name"
                placeholderTextColor="#9CA3AF"
              />
            </View>

            <View style={styles.formGroup}>
              <Text style={styles.formLabel}>Type *</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.typeScroll}>
                {locationTypes.map((type) => (
                  <TouchableOpacity
                    key={type}
                    style={[
                      styles.typeChip,
                      formData.type === type && styles.typeChipActive,
                    ]}
                    onPress={() => setFormData({ ...formData, type })}
                  >
                    <Text style={[
                      styles.typeChipText,
                      formData.type === type && styles.typeChipTextActive,
                    ]}>
                      {type}
                    </Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>

            <View style={styles.formRow}>
              <View style={[styles.formGroup, { flex: 1, marginRight: 8 }]}>
                <Text style={styles.formLabel}>Building</Text>
                <TextInput
                  style={styles.formInput}
                  value={formData.building}
                  onChangeText={(text) => setFormData({ ...formData, building: text })}
                  placeholder="Building name"
                  placeholderTextColor="#9CA3AF"
                />
              </View>

              <View style={[styles.formGroup, { flex: 1, marginLeft: 8 }]}>
                <Text style={styles.formLabel}>Floor</Text>
                <TextInput
                  style={styles.formInput}
                  value={formData.floor}
                  onChangeText={(text) => setFormData({ ...formData, floor: text })}
                  placeholder="Floor"
                  placeholderTextColor="#9CA3AF"
                />
              </View>
            </View>

            <View style={styles.formRow}>
              <View style={[styles.formGroup, { flex: 1, marginRight: 8 }]}>
                <Text style={styles.formLabel}>Room Number</Text>
                <TextInput
                  style={styles.formInput}
                  value={formData.room_number}
                  onChangeText={(text) => setFormData({ ...formData, room_number: text })}
                  placeholder="Room"
                  placeholderTextColor="#9CA3AF"
                />
              </View>

              <View style={[styles.formGroup, { flex: 1, marginLeft: 8 }]}>
                <Text style={styles.formLabel}>Max Capacity</Text>
                <TextInput
                  style={styles.formInput}
                  value={formData.max_capacity}
                  onChangeText={(text) => setFormData({ ...formData, max_capacity: text.replace(/[^0-9]/g, '') })}
                  placeholder="Capacity"
                  keyboardType="numeric"
                  placeholderTextColor="#9CA3AF"
                />
              </View>
            </View>

            <View style={styles.formGroup}>
              <Text style={styles.formLabel}>Default Time Limit (minutes) *</Text>
              <TextInput
                style={styles.formInput}
                value={formData.default_time_limit_minutes}
                onChangeText={(text) => setFormData({ ...formData, default_time_limit_minutes: text.replace(/[^0-9]/g, '') })}
                placeholder="5"
                keyboardType="numeric"
                placeholderTextColor="#9CA3AF"
              />
            </View>

            <TouchableOpacity
              style={styles.checkboxRow}
              onPress={() => setFormData({ ...formData, requires_approval: !formData.requires_approval })}
            >
              <View style={[styles.checkbox, formData.requires_approval && styles.checkboxChecked]}>
                {formData.requires_approval && (
                  <Ionicons name="checkmark" size={18} color="#FFFFFF" />
                )}
              </View>
              <Text style={styles.checkboxLabel}>Requires teacher approval</Text>
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
  addButton: {
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
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1E3A5F',
  },
  statLabel: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
  },
  locationsContainer: {
    padding: 16,
    gap: 16,
  },
  locationCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  inactiveCard: {
    opacity: 0.6,
  },
  locationHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  locationInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  iconCircle: {
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  locationDetails: {
    flex: 1,
  },
  locationName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1E3A5F',
  },
  locationType: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 2,
    textTransform: 'capitalize',
  },
  inactiveBadge: {
    backgroundColor: '#EF4444',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  inactiveBadgeText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: 'bold',
  },
  locationMeta: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  metaText: {
    fontSize: 14,
    color: '#6B7280',
  },
  locationSettings: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 12,
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  settingText: {
    fontSize: 13,
    color: '#374151',
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 12,
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
  editButton: {
    backgroundColor: '#E0E7FF',
  },
  editButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2E5A8F',
  },
  deactivateButton: {
    backgroundColor: '#EF4444',
  },
  activateButton: {
    backgroundColor: '#10B981',
  },
  actionButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
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
    marginBottom: 20,
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
  formRow: {
    flexDirection: 'row',
  },
  typeScroll: {
    marginTop: 8,
  },
  typeChip: {
    backgroundColor: '#F3F4F6',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 8,
  },
  typeChipActive: {
    backgroundColor: '#2E5A8F',
  },
  typeChipText: {
    fontSize: 14,
    color: '#6B7280',
    textTransform: 'capitalize',
  },
  typeChipTextActive: {
    color: '#FFFFFF',
    fontWeight: '600',
  },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderWidth: 2,
    borderColor: '#D1D5DB',
    borderRadius: 6,
    marginRight: 12,
    justifyContent: 'center',
    alignItems: 'center',
  },
  checkboxChecked: {
    backgroundColor: '#2E5A8F',
    borderColor: '#2E5A8F',
  },
  checkboxLabel: {
    fontSize: 16,
    color: '#374151',
  },
});
