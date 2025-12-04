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

interface DashboardStats {
  total_users: {
    student: number;
    parent: number;
    staff: number;
    admin: number;
  };
  active_passes_count: number;
  pending_id_approvals: number;
  recent_emergency_count: number;
  today_activity: {
    passes_created: number;
    user_logins: number;
  };
}

export default function AdminDashboardScreen() {
  const { user, token } = useAuth();
  const router = useRouter();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchDashboardStats = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/admin/dashboard/stats`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setStats(response.data);
    } catch (error: any) {
      console.error('Error fetching dashboard stats:', error);
      Alert.alert('Error', 'Failed to load dashboard statistics');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    if (user?.role === 'admin' || user?.role === 'staff') {
      fetchDashboardStats();
    } else {
      Alert.alert('Access Denied', 'This feature is only available to administrators');
      router.back();
    }
  }, []);

  const onRefresh = () => {
    setRefreshing(true);
    fetchDashboardStats();
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#1E3A5F" />
          <Text style={styles.loadingText}>Loading dashboard...</Text>
        </View>
      </SafeAreaView>
    );
  }

  const StatCard = ({ title, value, icon, color, onPress }: any) => (
    <TouchableOpacity
      style={[styles.statCard, { borderLeftColor: color }]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <View style={styles.statContent}>
        <View style={[styles.statIcon, { backgroundColor: color + '20' }]}>
          <Ionicons name={icon} size={24} color={color} />
        </View>
        <View style={styles.statInfo}>
          <Text style={styles.statValue}>{value}</Text>
          <Text style={styles.statTitle}>{title}</Text>
        </View>
      </View>
    </TouchableOpacity>
  );

  const QuickActionButton = ({ title, icon, color, onPress }: any) => (
    <TouchableOpacity
      style={styles.quickActionButton}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <View style={[styles.quickActionIcon, { backgroundColor: color + '20' }]}>
        <Ionicons name={icon} size={28} color={color} />
      </View>
      <Text style={styles.quickActionText}>{title}</Text>
    </TouchableOpacity>
  );

  const totalUsers = stats
    ? stats.total_users.student +
      stats.total_users.parent +
      stats.total_users.staff +
      stats.total_users.admin
    : 0;

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#FFFFFF" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Admin Dashboard</Text>
        <TouchableOpacity onPress={onRefresh} style={styles.refreshButton}>
          <Ionicons name="refresh" size={24} color="#FFFFFF" />
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Welcome Card */}
        <View style={styles.welcomeCard}>
          <Text style={styles.welcomeText}>Welcome back, {user?.first_name}!</Text>
          <Text style={styles.welcomeSubtext}>
            Here's what's happening in your school today
          </Text>
        </View>

        {/* Stats Grid */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Overview</Text>
          <View style={styles.statsGrid}>
            <StatCard
              title="Total Users"
              value={totalUsers}
              icon="people"
              color="#2E5A8F"
              onPress={() => router.push('/admin/users' as any)}
            />
            <StatCard
              title="Active Passes"
              value={stats?.active_passes_count || 0}
              icon="time"
              color="#10B981"
              onPress={() => router.push('/admin/pass-analytics' as any)}
            />
            <StatCard
              title="Pending Approvals"
              value={stats?.pending_id_approvals || 0}
              icon="checkmark-circle"
              color="#F59E0B"
              onPress={() => router.push('/admin/ids' as any)}
            />
            <StatCard
              title="Emergency Alerts"
              value={stats?.recent_emergency_count || 0}
              icon="warning"
              color="#EF4444"
              onPress={() => {}}
            />
          </View>
        </View>

        {/* User Breakdown */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Users by Role</Text>
          <View style={styles.userBreakdown}>
            <View style={styles.userRow}>
              <View style={[styles.userDot, { backgroundColor: '#2E5A8F' }]} />
              <Text style={styles.userLabel}>Students</Text>
              <Text style={styles.userCount}>{stats?.total_users.student || 0}</Text>
            </View>
            <View style={styles.userRow}>
              <View style={[styles.userDot, { backgroundColor: '#F59E0B' }]} />
              <Text style={styles.userLabel}>Parents</Text>
              <Text style={styles.userCount}>{stats?.total_users.parent || 0}</Text>
            </View>
            <View style={styles.userRow}>
              <View style={[styles.userDot, { backgroundColor: '#10B981' }]} />
              <Text style={styles.userLabel}>Staff</Text>
              <Text style={styles.userCount}>{stats?.total_users.staff || 0}</Text>
            </View>
            <View style={styles.userRow}>
              <View style={[styles.userDot, { backgroundColor: '#EF4444' }]} />
              <Text style={styles.userLabel}>Admins</Text>
              <Text style={styles.userCount}>{stats?.total_users.admin || 0}</Text>
            </View>
          </View>
        </View>

        {/* Today's Activity */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Today's Activity</Text>
          <View style={styles.activityCard}>
            <View style={styles.activityRow}>
              <Ionicons name="document" size={20} color="#2E5A8F" />
              <Text style={styles.activityLabel}>Passes Created</Text>
              <Text style={styles.activityValue}>
                {stats?.today_activity.passes_created || 0}
              </Text>
            </View>
            <View style={styles.activityRow}>
              <Ionicons name="log-in" size={20} color="#10B981" />
              <Text style={styles.activityLabel}>User Logins</Text>
              <Text style={styles.activityValue}>
                {stats?.today_activity.user_logins || 0}
              </Text>
            </View>
          </View>
        </View>

        {/* Quick Actions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          <View style={styles.quickActionsGrid}>
            <QuickActionButton
              title="Locations"
              icon="location"
              color="#2E5A8F"
              onPress={() => router.push('/admin/locations' as any)}
            />
            <QuickActionButton
              title="ID Cards"
              icon="card"
              color="#10B981"
              onPress={() => router.push('/admin/ids' as any)}
            />
            <QuickActionButton
              title="Messages"
              icon="chatbubbles"
              color="#F59E0B"
              onPress={() => router.push('/admin/messages' as any)}
            />
            <QuickActionButton
              title="Analytics"
              icon="bar-chart"
              color="#8B5CF6"
              onPress={() => router.push('/admin/pass-analytics' as any)}
            />
            <QuickActionButton
              title="Emergency"
              icon="warning"
              color="#EF4444"
              onPress={() => router.push('/admin/emergency' as any)}
            />
            <QuickActionButton
              title="Users"
              icon="people"
              color="#6366F1"
              onPress={() => router.push('/admin/users' as any)}
            />
          </View>
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
  refreshButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
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
  welcomeCard: {
    backgroundColor: '#FFFFFF',
    padding: 24,
    margin: 16,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  welcomeText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1E3A5F',
    marginBottom: 8,
  },
  welcomeSubtext: {
    fontSize: 14,
    color: '#6B7280',
  },
  section: {
    marginHorizontal: 16,
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1E3A5F',
    marginBottom: 12,
  },
  statsGrid: {
    gap: 12,
  },
  statCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    borderLeftWidth: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  statIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  statInfo: {
    flex: 1,
  },
  statValue: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#1E3A5F',
  },
  statTitle: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 4,
  },
  userBreakdown: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  userRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  userDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 12,
  },
  userLabel: {
    flex: 1,
    fontSize: 16,
    color: '#374151',
  },
  userCount: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1E3A5F',
  },
  activityCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  activityRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
  },
  activityLabel: {
    flex: 1,
    fontSize: 16,
    color: '#374151',
    marginLeft: 12,
  },
  activityValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1E3A5F',
  },
  quickActionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  quickActionButton: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    width: '31%',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  quickActionIcon: {
    width: 56,
    height: 56,
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  quickActionText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#374151',
    textAlign: 'center',
  },
});
