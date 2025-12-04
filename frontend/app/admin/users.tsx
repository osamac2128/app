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
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth, API_URL } from '../../contexts/AuthContext';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import axios from 'axios';

interface User {
  _id: string;
  first_name: string;
  last_name: string;
  email: string;
  role: string;
  phone?: string;
  status: string;
  created_at: string;
}

export default function UsersManagementScreen() {
  const { token } = useAuth();
  const router = useRouter();
  const [users, setUsers] = useState<User[]>([]);
  const [filteredUsers, setFilteredUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRole, setSelectedRole] = useState<string>('all');

  const fetchUsers = async () => {
    try {
      // Since we don't have a specific endpoint, we'll fetch from admin stats
      // In production, you'd have a GET /api/admin/users endpoint
      const response = await axios.get(`${API_URL}/api/admin/dashboard/stats`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      // For now, we'll show a placeholder message
      // In production, you'd fetch actual user list
      Alert.alert(
        'Feature Info',
        'User management endpoint is not yet implemented in the backend. This screen shows the UI design.'
      );
      
      setUsers([]);
      setFilteredUsers([]);
    } catch (error: any) {
      console.error('Error fetching users:', error);
      Alert.alert('Error', 'Failed to load users');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  useEffect(() => {
    // Filter users based on search and role
    let filtered = users;
    
    if (selectedRole !== 'all') {
      filtered = filtered.filter(user => user.role === selectedRole);
    }
    
    if (searchQuery) {
      filtered = filtered.filter(user => 
        user.first_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        user.last_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        user.email.toLowerCase().includes(searchQuery.toLowerCase())
      );
    }
    
    setFilteredUsers(filtered);
  }, [users, searchQuery, selectedRole]);

  const onRefresh = () => {
    setRefreshing(true);
    fetchUsers();
  };

  const handleUserPress = (user: User) => {
    Alert.alert(
      user.first_name + ' ' + user.last_name,
      `Email: ${user.email}\nRole: ${user.role}\nStatus: ${user.status}`,
      [
        { text: 'Close', style: 'cancel' },
        { text: 'Edit', onPress: () => {} },
        {
          text: user.status === 'active' ? 'Deactivate' : 'Activate',
          style: 'destructive',
          onPress: () => {},
        },
      ]
    );
  };

  const getRoleColor = (role: string) => {
    const colors: any = {
      admin: '#EF4444',
      staff: '#10B981',
      student: '#2E5A8F',
      parent: '#F59E0B',
    };
    return colors[role] || '#6B7280';
  };

  const getRoleIcon = (role: string) => {
    const icons: any = {
      admin: 'shield-checkmark',
      staff: 'briefcase',
      student: 'school',
      parent: 'people',
    };
    return icons[role] || 'person';
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#1E3A5F" />
          <Text style={styles.loadingText}>Loading users...</Text>
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
        <Text style={styles.headerTitle}>Users</Text>
        <TouchableOpacity onPress={onRefresh} style={styles.refreshButton}>
          <Ionicons name="refresh" size={24} color="#FFFFFF" />
        </TouchableOpacity>
      </View>

      <View style={styles.searchContainer}>
        <Ionicons name="search" size={20} color="#9CA3AF" style={styles.searchIcon} />
        <TextInput
          style={styles.searchInput}
          placeholder="Search by name or email..."
          placeholderTextColor="#9CA3AF"
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
      </View>

      <ScrollView
        horizontal
        showsHorizontalScrollIndicator={false}
        style={styles.filterContainer}
        contentContainerStyle={styles.filterContent}
      >
        {['all', 'admin', 'staff', 'student', 'parent'].map((role) => (
          <TouchableOpacity
            key={role}
            style={[
              styles.filterButton,
              selectedRole === role && styles.filterButtonActive,
            ]}
            onPress={() => setSelectedRole(role)}
          >
            <Text
              style={[
                styles.filterButtonText,
                selectedRole === role && styles.filterButtonTextActive,
              ]}
            >
              {role === 'all' ? 'All Users' : role.charAt(0).toUpperCase() + role.slice(1)}
            </Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        <View style={styles.statsBar}>
          <View style={styles.stat}>
            <Text style={styles.statValue}>{filteredUsers.length}</Text>
            <Text style={styles.statLabel}>Total Users</Text>
          </View>
        </View>

        <View style={styles.section}>
          {filteredUsers.length === 0 ? (
            <View style={styles.emptyState}>
              <Ionicons name="people" size={80} color="#9CA3AF" />
              <Text style={styles.emptyTitle}>No Users Found</Text>
              <Text style={styles.emptyText}>
                {searchQuery || selectedRole !== 'all'
                  ? 'Try adjusting your filters'
                  : 'User list will appear here'}
              </Text>
            </View>
          ) : (
            filteredUsers.map((user) => (
              <TouchableOpacity
                key={user._id}
                style={styles.userCard}
                onPress={() => handleUserPress(user)}
              >
                <View
                  style={[
                    styles.userIconContainer,
                    { backgroundColor: getRoleColor(user.role) + '20' },
                  ]}
                >
                  <Ionicons
                    name={getRoleIcon(user.role) as any}
                    size={24}
                    color={getRoleColor(user.role)}
                  />
                </View>
                
                <View style={styles.userInfo}>
                  <Text style={styles.userName}>
                    {user.first_name} {user.last_name}
                  </Text>
                  <Text style={styles.userEmail}>{user.email}</Text>
                  {user.phone && (
                    <Text style={styles.userPhone}>{user.phone}</Text>
                  )}
                </View>

                <View style={styles.userMeta}>
                  <View
                    style={[
                      styles.roleBadge,
                      { backgroundColor: getRoleColor(user.role) },
                    ]}
                  >
                    <Text style={styles.roleBadgeText}>
                      {user.role.toUpperCase()}
                    </Text>
                  </View>
                  <View
                    style={[
                      styles.statusBadge,
                      {
                        backgroundColor:
                          user.status === 'active' ? '#10B981' : '#9CA3AF',
                      },
                    ]}
                  >
                    <Text style={styles.statusBadgeText}>
                      {user.status.toUpperCase()}
                    </Text>
                  </View>
                </View>
              </TouchableOpacity>
            ))
          )}
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
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    marginHorizontal: 16,
    marginTop: 16,
    marginBottom: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  searchIcon: {
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    paddingVertical: 12,
    fontSize: 16,
    color: '#1F2937',
  },
  filterContainer: {
    maxHeight: 60,
  },
  filterContent: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    gap: 8,
  },
  filterButton: {
    backgroundColor: '#FFFFFF',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 2,
    borderColor: '#E5E7EB',
  },
  filterButtonActive: {
    backgroundColor: '#2E5A8F',
    borderColor: '#2E5A8F',
  },
  filterButtonText: {
    fontSize: 14,
    color: '#6B7280',
    fontWeight: '600',
  },
  filterButtonTextActive: {
    color: '#FFFFFF',
  },
  scrollView: {
    flex: 1,
  },
  statsBar: {
    backgroundColor: '#FFFFFF',
    padding: 16,
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
  userCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  userIconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  userInfo: {
    flex: 1,
  },
  userName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1E3A5F',
  },
  userEmail: {
    fontSize: 14,
    color: '#6B7280',
    marginTop: 2,
  },
  userPhone: {
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 2,
  },
  userMeta: {
    alignItems: 'flex-end',
    gap: 4,
  },
  roleBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  roleBadgeText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: 'bold',
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  statusBadgeText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: 'bold',
  },
});
