import React, { useState } from 'react';
import {
    View,
    Text,
    StyleSheet,
    TextInput,
    TouchableOpacity,
    ScrollView,
    Alert,
    ActivityIndicator,
    KeyboardAvoidingView,
    Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import axios from 'axios';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { API_URL } from '../../contexts/AuthContext';

export default function VisitorKioskScreen() {
    const router = useRouter();
    const [formData, setFormData] = useState({
        first_name: '',
        last_name: '',
        email: '',
        purpose: '',
        host_name: '',
    });
    const [loading, setLoading] = useState(false);
    const [success, setSuccess] = useState(false);

    const handleSubmit = async () => {
        if (!formData.first_name || !formData.last_name || !formData.purpose) {
            Alert.alert('Error', 'Please fill in all required fields.');
            return;
        }

        setLoading(true);
        try {
            await axios.post(`${API_URL}/api/visitors/check-in`, formData);
            setSuccess(true);
            setTimeout(() => {
                setSuccess(false);
                setFormData({
                    first_name: '',
                    last_name: '',
                    email: '',
                    purpose: '',
                    host_name: '',
                });
                router.replace('/'); // Go back to home/login
            }, 3000);
        } catch (error) {
            console.error('Check-in error:', error);
            Alert.alert('Error', 'Failed to check in. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    if (success) {
        return (
            <View style={styles.successContainer}>
                <Ionicons name="checkmark-circle" size={100} color="#10B981" />
                <Text style={styles.successTitle}>Welcome to AISJ!</Text>
                <Text style={styles.successSubtitle}>You are checked in.</Text>
                <Text style={styles.redirectText}>Redirecting...</Text>
            </View>
        );
    }

    return (
        <SafeAreaView style={styles.container}>
            <KeyboardAvoidingView
                behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
                style={{ flex: 1 }}
            >
                <ScrollView contentContainerStyle={styles.content}>
                    <View style={styles.header}>
                        <Text style={styles.title}>Visitor Check-In</Text>
                        <Text style={styles.subtitle}>Please enter your details</Text>
                    </View>

                    <View style={styles.form}>
                        <View style={styles.row}>
                            <View style={styles.inputGroupHalf}>
                                <Text style={styles.label}>First Name *</Text>
                                <TextInput
                                    style={styles.input}
                                    placeholder="John"
                                    value={formData.first_name}
                                    onChangeText={(text) => setFormData({ ...formData, first_name: text })}
                                />
                            </View>
                            <View style={styles.inputGroupHalf}>
                                <Text style={styles.label}>Last Name *</Text>
                                <TextInput
                                    style={styles.input}
                                    placeholder="Doe"
                                    value={formData.last_name}
                                    onChangeText={(text) => setFormData({ ...formData, last_name: text })}
                                />
                            </View>
                        </View>

                        <View style={styles.inputGroup}>
                            <Text style={styles.label}>Email (Optional)</Text>
                            <TextInput
                                style={styles.input}
                                placeholder="john@example.com"
                                keyboardType="email-address"
                                autoCapitalize="none"
                                value={formData.email}
                                onChangeText={(text) => setFormData({ ...formData, email: text })}
                            />
                        </View>

                        <View style={styles.inputGroup}>
                            <Text style={styles.label}>Purpose of Visit *</Text>
                            <TextInput
                                style={styles.input}
                                placeholder="Meeting, Event, etc."
                                value={formData.purpose}
                                onChangeText={(text) => setFormData({ ...formData, purpose: text })}
                            />
                        </View>

                        <View style={styles.inputGroup}>
                            <Text style={styles.label}>Host Name (Optional)</Text>
                            <TextInput
                                style={styles.input}
                                placeholder="Who are you visiting?"
                                value={formData.host_name}
                                onChangeText={(text) => setFormData({ ...formData, host_name: text })}
                            />
                        </View>

                        <TouchableOpacity
                            style={styles.button}
                            onPress={handleSubmit}
                            disabled={loading}
                        >
                            {loading ? (
                                <ActivityIndicator color="#FFFFFF" />
                            ) : (
                                <Text style={styles.buttonText}>Check In</Text>
                            )}
                        </TouchableOpacity>

                        <TouchableOpacity
                            style={styles.cancelButton}
                            onPress={() => router.back()}
                        >
                            <Text style={styles.cancelButtonText}>Cancel</Text>
                        </TouchableOpacity>
                    </View>
                </ScrollView>
            </KeyboardAvoidingView>
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#F5F7FA',
    },
    content: {
        padding: 24,
        flexGrow: 1,
        justifyContent: 'center',
    },
    header: {
        alignItems: 'center',
        marginBottom: 32,
    },
    title: {
        fontSize: 32,
        fontWeight: 'bold',
        color: '#1E3A5F',
        marginBottom: 8,
    },
    subtitle: {
        fontSize: 16,
        color: '#6B7280',
    },
    form: {
        backgroundColor: '#FFFFFF',
        padding: 24,
        borderRadius: 16,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 4 },
        shadowOpacity: 0.1,
        shadowRadius: 8,
        elevation: 5,
    },
    row: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        gap: 16,
    },
    inputGroup: {
        marginBottom: 16,
    },
    inputGroupHalf: {
        flex: 1,
        marginBottom: 16,
    },
    label: {
        fontSize: 14,
        fontWeight: '600',
        color: '#374151',
        marginBottom: 8,
    },
    input: {
        backgroundColor: '#F9FAFB',
        borderWidth: 1,
        borderColor: '#D1D5DB',
        borderRadius: 8,
        padding: 12,
        fontSize: 16,
        color: '#1F2937',
    },
    button: {
        backgroundColor: '#1E3A5F',
        padding: 16,
        borderRadius: 8,
        alignItems: 'center',
        marginTop: 16,
    },
    buttonText: {
        color: '#FFFFFF',
        fontSize: 16,
        fontWeight: 'bold',
    },
    cancelButton: {
        padding: 16,
        alignItems: 'center',
        marginTop: 8,
    },
    cancelButtonText: {
        color: '#6B7280',
        fontSize: 16,
    },
    successContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#FFFFFF',
    },
    successTitle: {
        fontSize: 28,
        fontWeight: 'bold',
        color: '#10B981',
        marginTop: 24,
        marginBottom: 8,
    },
    successSubtitle: {
        fontSize: 18,
        color: '#374151',
        marginBottom: 32,
    },
    redirectText: {
        fontSize: 14,
        color: '#9CA3AF',
    },
});
