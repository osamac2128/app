import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Animated,
  Dimensions,
  Alert,
  Image,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAuth } from '../../contexts/AuthContext';
import QRCode from 'react-native-qrcode-svg';
import * as ImagePicker from 'expo-image-picker';
import { Ionicons } from '@expo/vector-icons';
import axios from 'axios';
import { API_URL } from '../../contexts/AuthContext';

const { width } = Dimensions.get('window');
const CARD_WIDTH = width - 48;
const CARD_HEIGHT = CARD_WIDTH * 0.63;

interface DigitalID {
  _id: string;
  user_id: string;
  qr_code: string;
  barcode: string;
  photo_url?: string;
  submitted_photo_url?: string;
  photo_status: 'pending' | 'approved' | 'rejected';
  is_active: boolean;
  issued_at: string;
}

export default function IDCardScreen() {
  const { user, token } = useAuth();
  const [digitalId, setDigitalId] = useState<DigitalID | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [isFlipped, setIsFlipped] = useState(false);

  const flipAnimation = useRef(new Animated.Value(0)).current;
  const frontInterpolate = flipAnimation.interpolate({
    inputRange: [0, 180],
    outputRange: ['0deg', '180deg'],
  });
  const backInterpolate = flipAnimation.interpolate({
    inputRange: [0, 180],
    outputRange: ['180deg', '360deg'],
  });

  useEffect(() => {
    fetchDigitalID();
  }, []);

  const fetchDigitalID = async () => {
    try {
      const response = await axios.get(`${API_URL}/api/digital-ids/my-id`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setDigitalId(response.data);
    } catch (error) {
      console.error('Error fetching ID:', error);
      Alert.alert('Error', 'Failed to load Digital ID');
    } finally {
      setLoading(false);
    }
  };

  const flipCard = () => {
    if (isFlipped) {
      Animated.spring(flipAnimation, {
        toValue: 0,
        friction: 8,
        tension: 10,
        useNativeDriver: true,
      }).start();
    } else {
      Animated.spring(flipAnimation, {
        toValue: 180,
        friction: 8,
        tension: 10,
        useNativeDriver: true,
      }).start();
    }
    setIsFlipped(!isFlipped);
  };

  const pickImage = async () => {
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.5,
    });

    if (!result.canceled) {
      uploadPhoto(result.assets[0]);
    }
  };

  const uploadPhoto = async (asset: ImagePicker.ImagePickerAsset) => {
    setUploading(true);
    const formData = new FormData();

    // Append file
    const uriParts = asset.uri.split('.');
    const fileType = uriParts[uriParts.length - 1];

    formData.append('file', {
      uri: asset.uri,
      name: `photo.${fileType}`,
      type: `image/${fileType}`,
    } as any);

    try {
      await axios.post(`${API_URL}/api/digital-ids/upload-photo`, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data',
        },
      });

      Alert.alert('Success', 'Photo uploaded and pending approval');
      fetchDigitalID(); // Refresh to show pending status
    } catch (error: any) {
      console.error('Upload error:', error);
      Alert.alert('Error', 'Failed to upload photo');
    } finally {
      setUploading(false);
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'student': return '#2E5A8F';
      case 'staff': return '#10B981';
      case 'parent': return '#F59E0B';
      default: return '#6B7280';
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
        <Text style={styles.headerTitle}>Digital ID</Text>
        <Text style={styles.headerSubtitle}>Tap card to flip</Text>

        <TouchableOpacity activeOpacity={1} onPress={flipCard}>
          <View style={styles.cardContainer}>
            {/* Front of Card */}
            <Animated.View style={[styles.card, styles.cardFront, { transform: [{ rotateY: frontInterpolate }] }]}>
              <View style={[styles.cardHeader, { backgroundColor: getRoleColor(user?.role || '') }]}>
                <Text style={styles.schoolName}>AISJ CONNECT</Text>
                <Text style={styles.roleText}>{user?.role?.toUpperCase()}</Text>
              </View>

              <View style={styles.cardBody}>
                <View style={styles.photoContainer}>
                  {digitalId?.photo_url ? (
                    <Image source={{ uri: digitalId.photo_url }} style={styles.photo} />
                  ) : (
                    <View style={styles.placeholderPhoto}>
                      <Ionicons name="person" size={40} color="#9CA3AF" />
                    </View>
                  )}
                  {digitalId?.photo_status === 'pending' && (
                    <View style={styles.pendingBadge}>
                      <Text style={styles.pendingText}>Pending</Text>
                    </View>
                  )}
                </View>

                <View style={styles.infoContainer}>
                  <Text style={styles.name}>{user?.first_name} {user?.last_name}</Text>
                  <Text style={styles.idLabel}>ID: {digitalId?.barcode}</Text>
                  <Text style={styles.statusLabel}>Status: <Text style={{ color: digitalId?.is_active ? '#10B981' : '#EF4444' }}>{digitalId?.is_active ? 'Active' : 'Inactive'}</Text></Text>
                </View>
              </View>

              <View style={styles.qrContainer}>
                {digitalId?.qr_code && (
                  <QRCode
                    value={digitalId.qr_code}
                    size={80}
                    color="black"
                    backgroundColor="white"
                  />
                )}
              </View>
            </Animated.View>

            {/* Back of Card */}
            <Animated.View style={[styles.card, styles.cardBack, { transform: [{ rotateY: backInterpolate }] }]}>
              <View style={[styles.cardHeader, { backgroundColor: '#374151' }]}>
                <Text style={styles.schoolName}>EMERGENCY INFO</Text>
              </View>

              <View style={styles.cardBody}>
                <Text style={styles.emergencyTitle}>In case of emergency:</Text>
                <Text style={styles.emergencyText}>School Office: +1 (555) 123-4567</Text>
                <Text style={styles.emergencyText}>Security: +1 (555) 987-6543</Text>

                <View style={styles.barcodeContainer}>
                  <Text style={styles.barcodeText}>{digitalId?.barcode}</Text>
                  {/* Barcode visualization could go here */}
                </View>

                <Text style={styles.disclaimer}>
                  This digital ID is property of AISJ.
                  If found, please return to the school office.
                </Text>
              </View>
            </Animated.View>
          </View>
        </TouchableOpacity>

        <View style={styles.actions}>
          <TouchableOpacity
            style={styles.uploadButton}
            onPress={pickImage}
            disabled={uploading}
          >
            {uploading ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <>
                <Ionicons name="camera" size={20} color="#FFFFFF" style={{ marginRight: 8 }} />
                <Text style={styles.uploadButtonText}>
                  {digitalId?.photo_url ? 'Update Photo' : 'Upload Photo'}
                </Text>
              </>
            )}
          </TouchableOpacity>
        </View>
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
    alignItems: 'center',
    padding: 24,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1E3A5F',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 24,
  },
  cardContainer: {
    width: CARD_WIDTH,
    height: CARD_HEIGHT,
  },
  card: {
    width: '100%',
    height: '100%',
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    overflow: 'hidden',
    position: 'absolute',
    backfaceVisibility: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  cardFront: {
    zIndex: 2,
  },
  cardBack: {
    zIndex: 1,
  },
  cardHeader: {
    padding: 16,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  schoolName: {
    color: '#FFFFFF',
    fontWeight: 'bold',
    fontSize: 16,
  },
  roleText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
    backgroundColor: 'rgba(255,255,255,0.2)',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 4,
  },
  cardBody: {
    padding: 16,
    flex: 1,
  },
  photoContainer: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  photo: {
    width: 80,
    height: 80,
    borderRadius: 8,
    backgroundColor: '#E5E7EB',
  },
  placeholderPhoto: {
    width: 80,
    height: 80,
    borderRadius: 8,
    backgroundColor: '#E5E7EB',
    justifyContent: 'center',
    alignItems: 'center',
  },
  pendingBadge: {
    position: 'absolute',
    bottom: -8,
    left: 0,
    right: 0,
    backgroundColor: '#F59E0B',
    paddingVertical: 2,
    alignItems: 'center',
    borderRadius: 4,
  },
  pendingText: {
    color: '#FFFFFF',
    fontSize: 10,
    fontWeight: 'bold',
  },
  infoContainer: {
    marginLeft: 16,
    justifyContent: 'center',
  },
  name: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1F2937',
    marginBottom: 4,
  },
  idLabel: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 2,
  },
  statusLabel: {
    fontSize: 14,
    color: '#6B7280',
  },
  qrContainer: {
    position: 'absolute',
    bottom: 16,
    right: 16,
  },
  emergencyTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#EF4444',
    marginBottom: 12,
  },
  emergencyText: {
    fontSize: 14,
    color: '#374151',
    marginBottom: 8,
  },
  barcodeContainer: {
    marginTop: 24,
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
    paddingTop: 16,
  },
  barcodeText: {
    fontFamily: 'Courier',
    fontSize: 16,
    letterSpacing: 4,
  },
  disclaimer: {
    position: 'absolute',
    bottom: 16,
    left: 16,
    right: 16,
    fontSize: 10,
    color: '#9CA3AF',
    textAlign: 'center',
  },
  actions: {
    marginTop: 32,
    width: '100%',
  },
  uploadButton: {
    backgroundColor: '#1E3A5F',
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
    borderRadius: 12,
  },
  uploadButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
});
