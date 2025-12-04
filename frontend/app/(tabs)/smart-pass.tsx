import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth, API_URL } from '../../contexts/AuthContext';
import axios from 'axios';
import { Ionicons } from '@expo/vector-icons';
import { PassTimer } from '../../components/PassTimer';
import { useFocusEffect } from 'expo-router';

interface Location {
  _id: string;
  name: string;
  type: string;
  default_time_limit_minutes: number;
}

interface Pass {
  _id: string;
  origin_location_id: string;
  destination_location_id: string;
  status: 'active' | 'completed' | 'expired';
  departed_at: string;
  time_limit_minutes: number;
}

export default function SmartPassScreen() {
  const { token } = useAuth();
  const [locations, setLocations] = useState<Location[]>([]);
  const [activePass, setActivePass] = useState<Pass | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);

  useFocusEffect(
    React.useCallback(() => {
      loadData();
    }, [])
  );

  const loadData = async () => {
    setLoading(true);
    try {
      await Promise.all([fetchLocations(), fetchActivePass()]);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchLocations = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/passes/locations`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setLocations(response.data);
    } catch (error) {
      console.error('Error fetching locations:', error);
    }
  };

  const fetchActivePass = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/passes/active`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setActivePass(response.data);
    } catch (error) {
      // 404 is expected if no active pass
      setActivePass(null);
    }
  };

  const handleRequestPass = async (location: Location) => {
    setActionLoading(true);
    try {
      // Use the first location as origin (typically a classroom)
      // In production, this would be selected by user or determined by geolocation
      const originLocation = locations.length > 0 ? locations[0]._id : location._id;
      
      const response = await axios.post(
        `${API_URL}/api/passes/request`,
        {
          origin_location_id: originLocation,
          destination_location_id: location._id,
          time_limit_minutes: location.default_time_limit_minutes,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setActivePass(response.data);
      Alert.alert('Success', 'Pass requested successfully!');
    } catch (error: any) {
      console.error('Pass request error:', error);
      Alert.alert('Error', error.response?.data?.detail || 'Failed to request pass');
    } finally {
      setActionLoading(false);
    }
  };

  const handleEndPass = async () => {
    if (!activePass) return;
    setActionLoading(true);
    try {
      await axios.post(
        `${API_URL}/api/passes/end/${activePass._id}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setActivePass(null);
      Alert.alert('Pass Ended', 'You have successfully ended your pass.');
    } catch (error: any) {
      Alert.alert('Error', 'Failed to end pass');
    } finally {
      setActionLoading(false);
    }
  };

  const getLocationIcon = (type: string) => {
    switch (type) {
      case 'bathroom': return 'water';
      case 'nurse': return 'medkit';
      case 'office': return 'briefcase';
      case 'library': return 'book';
      default: return 'location';
    }
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#1E3A5F" />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.headerTitle}>Smart Pass</Text>

        {activePass ? (
          <View style={styles.activePassContainer}>
            <Text style={styles.activePassTitle}>Active Pass</Text>
            <PassTimer
              departedAt={activePass.departed_at}
              timeLimitMinutes={activePass.time_limit_minutes}
            />

            <TouchableOpacity
              style={styles.endButton}
              onPress={handleEndPass}
              disabled={actionLoading}
            >
              {actionLoading ? (
                <ActivityIndicator color="#FFFFFF" />
              ) : (
                <Text style={styles.endButtonText}>End Pass</Text>
              )}
            </TouchableOpacity>
          </View>
        ) : (
          <>
            <Text style={styles.subTitle}>Where are you going?</Text>
            <FlatList
              data={locations}
              keyExtractor={(item) => item._id}
              numColumns={2}
              columnWrapperStyle={styles.row}
              renderItem={({ item }) => (
                <TouchableOpacity
                  style={styles.locationCard}
                  onPress={() => handleRequestPass(item)}
                  disabled={actionLoading}
                >
                  <View style={styles.iconContainer}>
                    <Ionicons name={getLocationIcon(item.type) as any} size={32} color="#1E3A5F" />
                  </View>
                  <Text style={styles.locationName}>{item.name}</Text>
                  <Text style={styles.timeLimit}>{item.default_time_limit_minutes} min</Text>
                </TouchableOpacity>
              )}
            />
          </>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F7FA',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    flex: 1,
    padding: 24,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1E3A5F',
    marginBottom: 8,
  },
  subTitle: {
    fontSize: 16,
    color: '#6B7280',
    marginBottom: 24,
  },
  row: {
    justifyContent: 'space-between',
  },
  locationCard: {
    backgroundColor: '#FFFFFF',
    width: '48%',
    padding: 16,
    borderRadius: 16,
    marginBottom: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  iconContainer: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#E0F2FE',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 12,
  },
  locationName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
    marginBottom: 4,
    textAlign: 'center',
  },
  timeLimit: {
    fontSize: 12,
    color: '#6B7280',
  },
  activePassContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  activePassTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 32,
  },
  endButton: {
    backgroundColor: '#EF4444',
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 12,
    width: '100%',
    alignItems: 'center',
  },
  endButtonText: {
    color: '#FFFFFF',
    fontSize: 18,
    fontWeight: 'bold',
  },
});
