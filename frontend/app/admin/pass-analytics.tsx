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
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth, API_URL } from '../../contexts/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import axios from 'axios';

const { width } = Dimensions.get('window');

interface PassAnalytics {
  most_used_locations: Array<{ location_name: string; count: number }>;
  average_duration_minutes: number;
  overtime_count: number;
  total_passes_today: number;
  total_passes_week: number;
  hourly_distribution: Array<{ hour: number; count: number }>;
}

export default function PassAnalyticsScreen() {
  const { token } = useAuth();
  const router = useRouter();
  const [analytics, setAnalytics] = useState<PassAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/admin/analytics/passes`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setAnalytics(response.data);
    } catch (error: any) {
      console.error('Error fetching analytics:', error);
      Alert.alert('Error', 'Failed to load pass analytics');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchAnalytics();
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#1E3A5F" />
          <Text style={styles.loadingText}>Loading analytics...</Text>
        </View>
      </SafeAreaView>
    );
  }

  const maxCount = Math.max(...(analytics?.most_used_locations.map(l => l.count) || [1]));
  const maxHourly = Math.max(...(analytics?.hourly_distribution.map(h => h.count) || [1]));

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#FFFFFF" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Pass Analytics</Text>
        <TouchableOpacity onPress={() => router.push('/admin/overtime-passes' as any)} style={styles.overtimeButton}>
          <Ionicons name="warning" size={24} color="#FFFFFF" />
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Summary Cards */}
        <View style={styles.summaryContainer}>
          <View style={[styles.summaryCard, { backgroundColor: '#2E5A8F' }]}>
            <Ionicons name="document-text" size={32} color="#FFFFFF" />
            <Text style={styles.summaryValue}>{analytics?.total_passes_today || 0}</Text>
            <Text style={styles.summaryLabel}>Today</Text>
          </View>

          <View style={[styles.summaryCard, { backgroundColor: '#10B981' }]}>
            <Ionicons name="calendar" size={32} color="#FFFFFF" />
            <Text style={styles.summaryValue}>{analytics?.total_passes_week || 0}</Text>
            <Text style={styles.summaryLabel}>This Week</Text>
          </View>

          <View style={[styles.summaryCard, { backgroundColor: '#F59E0B' }]}>
            <Ionicons name="time" size={32} color="#FFFFFF" />
            <Text style={styles.summaryValue}>{analytics?.average_duration_minutes.toFixed(1) || 0}</Text>
            <Text style={styles.summaryLabel}>Avg Duration (min)</Text>
          </View>

          <View style={[styles.summaryCard, { backgroundColor: '#EF4444' }]}>
            <Ionicons name="warning" size={32} color="#FFFFFF" />
            <Text style={styles.summaryValue}>{analytics?.overtime_count || 0}</Text>
            <Text style={styles.summaryLabel}>Overtime</Text>
          </View>
        </View>

        {/* Most Used Locations */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Most Used Locations (Last 7 Days)</Text>
          <View style={styles.chartCard}>
            {analytics?.most_used_locations.length === 0 ? (
              <Text style={styles.emptyText}>No data available</Text>
            ) : (
              analytics?.most_used_locations.map((location, index) => (
                <View key={index} style={styles.barContainer}>
                  <Text style={styles.locationName}>{location.location_name}</Text>
                  <View style={styles.barWrapper}>
                    <View
                      style={[
                        styles.bar,
                        {
                          width: `${(location.count / maxCount) * 100}%`,
                          backgroundColor: `hsl(${210 - (index * 30)}, 70%, 50%)`,
                        },
                      ]}
                    />
                    <Text style={styles.barLabel}>{location.count}</Text>
                  </View>
                </View>
              ))
            )}
          </View>
        </View>

        {/* Hourly Distribution */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Hourly Pass Activity (Today)</Text>
          <View style={styles.chartCard}>
            {analytics?.hourly_distribution.length === 0 ? (
              <Text style={styles.emptyText}>No activity today</Text>
            ) : (
              <View style={styles.hourlyChart}>
                {analytics?.hourly_distribution.map((hour, index) => {
                  const barHeight = (hour.count / maxHourly) * 150;
                  return (
                    <View key={index} style={styles.hourlyBar}>
                      <View style={styles.hourlyBarContainer}>
                        <View
                          style={[
                            styles.hourlyBarFill,
                            {
                              height: barHeight,
                              backgroundColor: '#2E5A8F',
                            },
                          ]}
                        />
                      </View>
                      <Text style={styles.hourLabel}>{hour.hour}h</Text>
                      <Text style={styles.hourCount}>{hour.count}</Text>
                    </View>
                  );
                })}
              </View>
            )}
          </View>
        </View>

        {/* Quick Actions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => router.push('/admin/overtime-passes' as any)}
          >
            <Ionicons name="warning" size={24} color="#EF4444" />
            <View style={styles.actionContent}>
              <Text style={styles.actionTitle}>View Overtime Passes</Text>
              <Text style={styles.actionSubtitle}>
                {analytics?.overtime_count || 0} passes currently overtime
              </Text>
            </View>
            <Ionicons name="chevron-forward" size={24} color="#9CA3AF" />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => router.push('/staff/pass-approval' as any)}
          >
            <Ionicons name="checkmark-done" size={24} color="#10B981" />
            <View style={styles.actionContent}>
              <Text style={styles.actionTitle}>Approve Pending Passes</Text>
              <Text style={styles.actionSubtitle}>Review pass requests</Text>
            </View>
            <Ionicons name="chevron-forward" size={24} color="#9CA3AF" />
          </TouchableOpacity>
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
  overtimeButton: {
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
  summaryContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    padding: 16,
    gap: 12,
  },
  summaryCard: {
    width: (width - 44) / 2,
    padding: 20,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  summaryValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginTop: 8,
  },
  summaryLabel: {
    fontSize: 14,
    color: '#FFFFFF',
    marginTop: 4,
    opacity: 0.9,
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
  chartCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  emptyText: {
    textAlign: 'center',
    color: '#9CA3AF',
    fontSize: 16,
    padding: 20,
  },
  barContainer: {
    marginBottom: 20,
  },
  locationName: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
  },
  barWrapper: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  bar: {
    height: 32,
    borderRadius: 4,
    minWidth: 30,
  },
  barLabel: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#374151',
    marginLeft: 12,
  },
  hourlyChart: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-around',
    height: 200,
    paddingTop: 20,
  },
  hourlyBar: {
    alignItems: 'center',
    flex: 1,
  },
  hourlyBarContainer: {
    height: 150,
    justifyContent: 'flex-end',
    alignItems: 'center',
    width: 20,
  },
  hourlyBarFill: {
    width: 20,
    borderTopLeftRadius: 4,
    borderTopRightRadius: 4,
    minHeight: 5,
  },
  hourLabel: {
    fontSize: 10,
    color: '#6B7280',
    marginTop: 4,
  },
  hourCount: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#374151',
  },
  actionButton: {
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
  actionContent: {
    flex: 1,
    marginLeft: 16,
  },
  actionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1E3A5F',
  },
  actionSubtitle: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 2,
  },
});
