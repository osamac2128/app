import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Modal,
  Image,
  ScrollView,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useAuth, API_URL } from '../../contexts/AuthContext';
import axios from 'axios';

interface ScannedUser {
  _id: string;
  first_name: string;
  last_name: string;
  email: string;
  role: string;
  status: string;
}

interface ScannedDigitalID {
  _id: string;
  qr_code: string;
  barcode: string;
  photo_url?: string;
  is_active: boolean;
  issued_at: string;
}

interface ScanResult {
  valid: boolean;
  user: ScannedUser;
  digital_id: ScannedDigitalID;
}

interface ScanHistoryItem {
  _id: string;
  scanned_at: string;
  scanned_user: {
    name: string;
    role: string;
  } | null;
  scanned_by: {
    name: string;
    role: string;
  } | null;
  purpose: string;
  location: string | null;
}

export default function IDScannerScreen() {
  const { token, user } = useAuth();
  const router = useRouter();
  const [permission, requestPermission] = useCameraPermissions();
  const [scanning, setScanning] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [scanResult, setScanResult] = useState<ScanResult | null>(null);
  const [showResultModal, setShowResultModal] = useState(false);
  const [showHistoryModal, setShowHistoryModal] = useState(false);
  const [scanHistory, setScanHistory] = useState<ScanHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [scanned, setScanned] = useState(false);

  useEffect(() => {
    if (!user || (user.role !== 'staff' && user.role !== 'admin')) {
      Alert.alert('Access Denied', 'Only staff and admins can access the ID scanner.');
      router.back();
    }
  }, [user]);

  const handleBarCodeScanned = async ({ type, data }: { type: string; data: string }) => {
    if (scanned || processing) return;

    setScanned(true);
    setProcessing(true);
    setScanning(false);

    try {
      const response = await axios.get(
        `${API_URL}/api/digital-ids/scan/${encodeURIComponent(data)}`,
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setScanResult(response.data);
      setShowResultModal(true);
    } catch (error: any) {
      console.error('Scan error:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to verify ID';
      Alert.alert('Scan Failed', errorMessage, [
        { text: 'OK', onPress: () => resetScanner() }
      ]);
    } finally {
      setProcessing(false);
    }
  };

  const resetScanner = () => {
    setScanned(false);
    setScanResult(null);
    setShowResultModal(false);
    setScanning(true);
  };

  const fetchScanHistory = async () => {
    setLoadingHistory(true);
    try {
      const response = await axios.get(`${API_URL}/api/digital-ids/scan-history?limit=20`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setScanHistory(response.data);
    } catch (error) {
      console.error('Error fetching scan history:', error);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleShowHistory = () => {
    setShowHistoryModal(true);
    fetchScanHistory();
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'student': return '#2E5A8F';
      case 'staff': return '#10B981';
      case 'parent': return '#F59E0B';
      case 'admin': return '#EF4444';
      default: return '#6B7280';
    }
  };

  if (!permission) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centerContent}>
          <ActivityIndicator size="large" color="#1E3A5F" />
          <Text style={styles.loadingText}>Loading camera...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!permission.granted) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.header}>
          <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
            <Ionicons name="arrow-back" size={24} color="#FFFFFF" />
          </TouchableOpacity>
          <Text style={styles.headerTitle}>ID Scanner</Text>
          <View style={{ width: 40 }} />
        </View>
        <View style={styles.centerContent}>
          <Ionicons name="camera-outline" size={80} color="#9CA3AF" />
          <Text style={styles.permissionTitle}>Camera Permission Required</Text>
          <Text style={styles.permissionText}>
            To scan ID cards, we need access to your camera.
          </Text>
          <TouchableOpacity style={styles.permissionButton} onPress={requestPermission}>
            <Text style={styles.permissionButtonText}>Grant Permission</Text>
          </TouchableOpacity>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#FFFFFF" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>ID Scanner</Text>
        <TouchableOpacity onPress={handleShowHistory} style={styles.historyButton}>
          <Ionicons name="time" size={24} color="#FFFFFF" />
        </TouchableOpacity>
      </View>

      <View style={styles.cameraContainer}>
        {scanning ? (
          <CameraView
            style={styles.camera}
            barcodeScannerSettings={{
              barcodeTypes: ['qr', 'code128', 'code39', 'ean13', 'ean8'],
            }}
            onBarcodeScanned={scanned ? undefined : handleBarCodeScanned}
          >
            <View style={styles.overlay}>
              <View style={styles.scanFrame}>
                <View style={[styles.corner, styles.topLeft]} />
                <View style={[styles.corner, styles.topRight]} />
                <View style={[styles.corner, styles.bottomLeft]} />
                <View style={[styles.corner, styles.bottomRight]} />
              </View>
              <Text style={styles.scanText}>
                Position the QR code within the frame
              </Text>
            </View>
          </CameraView>
        ) : (
          <View style={styles.processingContainer}>
            {processing ? (
              <>
                <ActivityIndicator size="large" color="#1E3A5F" />
                <Text style={styles.processingText}>Verifying ID...</Text>
              </>
            ) : (
              <>
                <Ionicons name="checkmark-circle" size={80} color="#10B981" />
                <Text style={styles.processingText}>Scan Complete</Text>
              </>
            )}
          </View>
        )}
      </View>

      <View style={styles.instructionContainer}>
        <Ionicons name="information-circle" size={24} color="#2E5A8F" />
        <Text style={styles.instructionText}>
          Point the camera at the QR code on the student or staff ID card to verify their identity.
        </Text>
      </View>

      {/* Result Modal */}
      <Modal visible={showResultModal} animationType="slide" transparent>
        <View style={styles.modalOverlay}>
          <View style={styles.resultModal}>
            <View style={styles.resultHeader}>
              <Ionicons
                name={scanResult?.valid ? 'checkmark-circle' : 'close-circle'}
                size={60}
                color={scanResult?.valid ? '#10B981' : '#EF4444'}
              />
              <Text style={styles.resultTitle}>
                {scanResult?.valid ? 'ID Verified' : 'Verification Failed'}
              </Text>
            </View>

            {scanResult?.valid && (
              <View style={styles.resultContent}>
                <View style={styles.photoContainer}>
                  {scanResult.digital_id.photo_url ? (
                    <Image
                      source={{ uri: scanResult.digital_id.photo_url }}
                      style={styles.resultPhoto}
                    />
                  ) : (
                    <View style={styles.placeholderPhoto}>
                      <Ionicons name="person" size={50} color="#9CA3AF" />
                    </View>
                  )}
                </View>

                <Text style={styles.resultName}>
                  {scanResult.user.first_name} {scanResult.user.last_name}
                </Text>

                <View
                  style={[
                    styles.roleBadge,
                    { backgroundColor: getRoleColor(scanResult.user.role) },
                  ]}
                >
                  <Text style={styles.roleText}>
                    {scanResult.user.role.toUpperCase()}
                  </Text>
                </View>

                <View style={styles.detailsContainer}>
                  <View style={styles.detailRow}>
                    <Ionicons name="mail" size={18} color="#6B7280" />
                    <Text style={styles.detailText}>{scanResult.user.email}</Text>
                  </View>
                  <View style={styles.detailRow}>
                    <Ionicons name="card" size={18} color="#6B7280" />
                    <Text style={styles.detailText}>ID: {scanResult.digital_id.barcode}</Text>
                  </View>
                  <View style={styles.detailRow}>
                    <Ionicons
                      name={scanResult.user.status === 'active' ? 'checkmark-circle' : 'close-circle'}
                      size={18}
                      color={scanResult.user.status === 'active' ? '#10B981' : '#EF4444'}
                    />
                    <Text style={styles.detailText}>
                      Status: {scanResult.user.status}
                    </Text>
                  </View>
                </View>
              </View>
            )}

            <TouchableOpacity style={styles.closeButton} onPress={resetScanner}>
              <Text style={styles.closeButtonText}>Scan Another ID</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>

      {/* History Modal */}
      <Modal visible={showHistoryModal} animationType="slide" transparent={false}>
        <SafeAreaView style={styles.historyModal}>
          <View style={styles.historyHeader}>
            <TouchableOpacity onPress={() => setShowHistoryModal(false)}>
              <Ionicons name="close" size={28} color="#1E3A5F" />
            </TouchableOpacity>
            <Text style={styles.historyTitle}>Scan History</Text>
            <TouchableOpacity onPress={fetchScanHistory}>
              <Ionicons name="refresh" size={24} color="#1E3A5F" />
            </TouchableOpacity>
          </View>

          {loadingHistory ? (
            <View style={styles.centerContent}>
              <ActivityIndicator size="large" color="#1E3A5F" />
            </View>
          ) : (
            <ScrollView style={styles.historyList}>
              {scanHistory.length === 0 ? (
                <View style={styles.emptyHistory}>
                  <Ionicons name="time-outline" size={60} color="#9CA3AF" />
                  <Text style={styles.emptyHistoryText}>No scan history</Text>
                </View>
              ) : (
                scanHistory.map((item) => (
                  <View key={item._id} style={styles.historyItem}>
                    <View style={styles.historyItemIcon}>
                      <Ionicons name="scan" size={24} color="#2E5A8F" />
                    </View>
                    <View style={styles.historyItemContent}>
                      <Text style={styles.historyItemName}>
                        {item.scanned_user?.name || 'Unknown User'}
                      </Text>
                      <Text style={styles.historyItemMeta}>
                        {item.scanned_user?.role || 'N/A'} - Scanned by {item.scanned_by?.name || 'Unknown'}
                      </Text>
                      <Text style={styles.historyItemDate}>
                        {new Date(item.scanned_at).toLocaleString()}
                      </Text>
                    </View>
                  </View>
                ))
              )}
            </ScrollView>
          )}
        </SafeAreaView>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
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
  historyButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  centerContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#6B7280',
  },
  permissionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1E3A5F',
    marginTop: 16,
    textAlign: 'center',
  },
  permissionText: {
    fontSize: 16,
    color: '#6B7280',
    textAlign: 'center',
    marginTop: 8,
    paddingHorizontal: 32,
  },
  permissionButton: {
    backgroundColor: '#1E3A5F',
    paddingHorizontal: 32,
    paddingVertical: 14,
    borderRadius: 8,
    marginTop: 24,
  },
  permissionButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  cameraContainer: {
    flex: 1,
    margin: 16,
    borderRadius: 16,
    overflow: 'hidden',
    backgroundColor: '#000000',
  },
  camera: {
    flex: 1,
  },
  overlay: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.4)',
  },
  scanFrame: {
    width: 250,
    height: 250,
    position: 'relative',
  },
  corner: {
    position: 'absolute',
    width: 40,
    height: 40,
    borderColor: '#FFFFFF',
  },
  topLeft: {
    top: 0,
    left: 0,
    borderTopWidth: 4,
    borderLeftWidth: 4,
  },
  topRight: {
    top: 0,
    right: 0,
    borderTopWidth: 4,
    borderRightWidth: 4,
  },
  bottomLeft: {
    bottom: 0,
    left: 0,
    borderBottomWidth: 4,
    borderLeftWidth: 4,
  },
  bottomRight: {
    bottom: 0,
    right: 0,
    borderBottomWidth: 4,
    borderRightWidth: 4,
  },
  scanText: {
    color: '#FFFFFF',
    fontSize: 16,
    marginTop: 24,
    textAlign: 'center',
    paddingHorizontal: 32,
  },
  processingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#F5F7FA',
  },
  processingText: {
    marginTop: 16,
    fontSize: 18,
    color: '#1E3A5F',
    fontWeight: '600',
  },
  instructionContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#EBF4FF',
    margin: 16,
    marginTop: 0,
    padding: 16,
    borderRadius: 12,
    gap: 12,
  },
  instructionText: {
    flex: 1,
    fontSize: 14,
    color: '#374151',
    lineHeight: 20,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  resultModal: {
    backgroundColor: '#FFFFFF',
    borderRadius: 16,
    padding: 24,
    width: '100%',
    maxWidth: 360,
  },
  resultHeader: {
    alignItems: 'center',
    marginBottom: 20,
  },
  resultTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#1E3A5F',
    marginTop: 12,
  },
  resultContent: {
    alignItems: 'center',
  },
  photoContainer: {
    marginBottom: 16,
  },
  resultPhoto: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#E5E7EB',
  },
  placeholderPhoto: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#E5E7EB',
    justifyContent: 'center',
    alignItems: 'center',
  },
  resultName: {
    fontSize: 22,
    fontWeight: 'bold',
    color: '#1F2937',
    marginBottom: 8,
  },
  roleBadge: {
    paddingHorizontal: 16,
    paddingVertical: 6,
    borderRadius: 20,
    marginBottom: 16,
  },
  roleText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: 'bold',
  },
  detailsContainer: {
    width: '100%',
    backgroundColor: '#F9FAFB',
    borderRadius: 12,
    padding: 16,
    gap: 12,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  detailText: {
    fontSize: 14,
    color: '#374151',
    flex: 1,
  },
  closeButton: {
    backgroundColor: '#1E3A5F',
    paddingVertical: 14,
    borderRadius: 8,
    marginTop: 20,
    alignItems: 'center',
  },
  closeButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  historyModal: {
    flex: 1,
    backgroundColor: '#F5F7FA',
  },
  historyHeader: {
    backgroundColor: '#FFFFFF',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  historyTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#1E3A5F',
  },
  historyList: {
    flex: 1,
    padding: 16,
  },
  emptyHistory: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 100,
  },
  emptyHistoryText: {
    marginTop: 16,
    fontSize: 16,
    color: '#9CA3AF',
  },
  historyItem: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    flexDirection: 'row',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  historyItemIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#EBF4FF',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  historyItemContent: {
    flex: 1,
  },
  historyItemName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#1F2937',
  },
  historyItemMeta: {
    fontSize: 13,
    color: '#6B7280',
    marginTop: 2,
  },
  historyItemDate: {
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 4,
  },
});
