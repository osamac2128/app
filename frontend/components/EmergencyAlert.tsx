import React, { useState, useEffect } from 'react';
import {
  Modal,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
  Dimensions,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { BlurView } from 'expo-blur';

const { width, height } = Dimensions.get('window');

interface EmergencyAlertProps {
  visible: boolean;
  alertType: string;
  title: string;
  message: string;
  instructions?: string[];
  isDrill?: boolean;
  severity?: string;
  onCheckIn: () => void;
  onDismiss?: () => void;
}

export default function EmergencyAlert({
  visible,
  alertType,
  title,
  message,
  instructions = [],
  isDrill = false,
  severity = 'high',
  onCheckIn,
  onDismiss,
}: EmergencyAlertProps) {
  const [pulseAnim] = useState(new Animated.Value(1));

  useEffect(() => {
    if (visible && severity === 'critical') {
      // Pulse animation for critical alerts
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.1,
            duration: 500,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 500,
            useNativeDriver: true,
          }),
        ])
      ).start();
    }
  }, [visible, severity]);

  const getAlertColor = () => {
    if (isDrill) return '#F59E0B'; // Orange for drills
    
    switch (severity) {
      case 'critical':
        return '#DC2626'; // Red
      case 'high':
        return '#EF4444'; // Light red
      case 'medium':
        return '#F59E0B'; // Orange
      case 'low':
        return '#3B82F6'; // Blue
      case 'info':
        return '#10B981'; // Green
      default:
        return '#EF4444';
    }
  };

  const getAlertIcon = () => {
    if (isDrill) return 'megaphone';
    
    switch (alertType.toLowerCase()) {
      case 'lockdown':
      case 'lockdown_secure':
      case 'lockout':
        return 'lock-closed';
      case 'fire':
      case 'fire_drill':
        return 'flame';
      case 'tornado':
      case 'tornado_drill':
      case 'weather':
        return 'thunderstorm';
      case 'earthquake':
      case 'earthquake_drill':
        return 'pulse';
      case 'medical':
        return 'medical';
      case 'evacuation':
        return 'exit';
      case 'all_clear':
        return 'checkmark-circle';
      default:
        return 'warning';
    }
  };

  const backgroundColor = getAlertColor();

  return (
    <Modal
      visible={visible}
      animationType="fade"
      transparent={false}
      statusBarTranslucent
    >
      <View style={[styles.container, { backgroundColor }]}>
        {/* Drill Banner */}
        {isDrill && (
          <View style={styles.drillBanner}>
            <Ionicons name="megaphone" size={24} color="#FFFFFF" />
            <Text style={styles.drillText}>THIS IS A DRILL</Text>
            <Ionicons name="megaphone" size={24} color="#FFFFFF" />
          </View>
        )}

        {/* Alert Icon */}
        <Animated.View
          style={[
            styles.iconContainer,
            { transform: [{ scale: pulseAnim }] },
          ]}
        >
          <Ionicons name={getAlertIcon() as any} size={120} color="#FFFFFF" />
        </Animated.View>

        {/* Alert Title */}
        <Text style={styles.title}>{title.toUpperCase()}</Text>

        {/* Alert Message */}
        <View style={styles.messageContainer}>
          <Text style={styles.message}>{message}</Text>
        </View>

        {/* Instructions */}
        {instructions.length > 0 && (
          <View style={styles.instructionsContainer}>
            <Text style={styles.instructionsTitle}>WHAT TO DO:</Text>
            {instructions.map((instruction, index) => (
              <View key={index} style={styles.instructionRow}>
                <Text style={styles.instructionNumber}>{index + 1}.</Text>
                <Text style={styles.instructionText}>{instruction}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Action Buttons */}
        <View style={styles.actionContainer}>
          <TouchableOpacity
            style={[styles.button, styles.checkInButton]}
            onPress={onCheckIn}
            activeOpacity={0.8}
          >
            <Ionicons name="checkmark-circle" size={24} color={backgroundColor} />
            <Text style={[styles.buttonText, { color: backgroundColor }]}>
              CHECK IN - I'M SAFE
            </Text>
          </TouchableOpacity>

          {(alertType === 'all_clear' || isDrill) && onDismiss && (
            <TouchableOpacity
              style={[styles.button, styles.dismissButton]}
              onPress={onDismiss}
              activeOpacity={0.8}
            >
              <Text style={styles.dismissButtonText}>CLOSE</Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Emergency Contact Info */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            For assistance, contact school office immediately
          </Text>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  drillBanner: {
    position: 'absolute',
    top: Platform.OS === 'ios' ? 60 : 40,
    left: 0,
    right: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.3)',
    paddingVertical: 16,
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 12,
  },
  drillText: {
    color: '#FFFFFF',
    fontSize: 24,
    fontWeight: 'bold',
    letterSpacing: 2,
  },
  iconContainer: {
    marginBottom: 32,
  },
  title: {
    fontSize: 42,
    fontWeight: 'bold',
    color: '#FFFFFF',
    textAlign: 'center',
    marginBottom: 24,
    letterSpacing: 2,
  },
  messageContainer: {
    backgroundColor: 'rgba(0, 0, 0, 0.2)',
    borderRadius: 16,
    padding: 24,
    marginBottom: 32,
    width: '100%',
  },
  message: {
    fontSize: 20,
    color: '#FFFFFF',
    textAlign: 'center',
    lineHeight: 28,
  },
  instructionsContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderRadius: 16,
    padding: 24,
    marginBottom: 32,
    width: '100%',
  },
  instructionsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1E3A5F',
    marginBottom: 16,
    textAlign: 'center',
  },
  instructionRow: {
    flexDirection: 'row',
    marginBottom: 12,
    alignItems: 'flex-start',
  },
  instructionNumber: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1E3A5F',
    marginRight: 8,
    minWidth: 24,
  },
  instructionText: {
    fontSize: 16,
    color: '#374151',
    flex: 1,
    lineHeight: 22,
  },
  actionContainer: {
    width: '100%',
    gap: 12,
  },
  button: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
    borderRadius: 12,
    gap: 12,
  },
  checkInButton: {
    backgroundColor: '#FFFFFF',
  },
  buttonText: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  dismissButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderWidth: 2,
    borderColor: '#FFFFFF',
  },
  dismissButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#FFFFFF',
  },
  footer: {
    position: 'absolute',
    bottom: 24,
    left: 24,
    right: 24,
  },
  footerText: {
    color: '#FFFFFF',
    fontSize: 12,
    textAlign: 'center',
    opacity: 0.8,
  },
});
