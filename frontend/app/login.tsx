import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useAuth } from '../contexts/AuthContext';
import { SafeAreaView } from 'react-native-safe-area-context';

export default function LoginScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const router = useRouter();

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert('Error', 'Please fill in all fields');
      return;
    }

    setLoading(true);
    try {
      await login(email.toLowerCase().trim(), password);
      router.replace('/(tabs)/home');
    } catch (error: any) {
      Alert.alert('Login Failed', error.message || 'Invalid credentials');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.container}
      >
        <ScrollView
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
        >
          <View style={styles.header}>
            <Text style={styles.title}>AISJ Connect</Text>
            <Text style={styles.subtitle}>Welcome back! Please login to continue.</Text>
          </View>

          <View style={styles.form}>
            <View style={styles.inputGroup}>
              <Text style={styles.label}>Email</Text>
              <TextInput
                style={styles.input}
                placeholder="Enter your email"
                placeholderTextColor="#9CA3AF"
                value={email}
                onChangeText={setEmail}
                autoCapitalize="none"
                keyboardType="email-address"
                editable={!loading}
              />
            </View>

            <View style={styles.inputGroup}>
              <Text style={styles.label}>Password</Text>
              <TextInput
                style={styles.input}
                placeholder="Enter your password"
                placeholderTextColor="#9CA3AF"
                value={password}
                onChangeText={setPassword}
                import React, {useState} from 'react';
              import {
                View,
                Text,
                TextInput,
                TouchableOpacity,
                StyleSheet,
                KeyboardAvoidingView,
                Platform,
                ScrollView,
                Alert,
                ActivityIndicator,
} from 'react-native';
              import {useRouter} from 'expo-router';
              import {useAuth} from '../contexts/AuthContext';
              import {SafeAreaView} from 'react-native-safe-area-context';

              export default function LoginScreen() {
  const [email, setEmail] = useState('');
              const [password, setPassword] = useState('');
              const [loading, setLoading] = useState(false);
              const {login} = useAuth();
              const router = useRouter();

  const handleLogin = async () => {
    if (!email || !password) {
                Alert.alert('Error', 'Please fill in all fields');
              return;
    }

              setLoading(true);
              try {
                await login(email.toLowerCase().trim(), password);
              router.replace('/(tabs)/home');
    } catch (error: any) {
                Alert.alert('Login Failed', error.message || 'Invalid credentials');
    } finally {
                setLoading(false);
    }
  };

              return (
              <SafeAreaView style={styles.container}>
                <KeyboardAvoidingView
                  behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
                  style={styles.container}
                >
                  <ScrollView
                    contentContainerStyle={styles.content}
                    keyboardShouldPersistTaps="handled"
                  >
                    <View style={styles.header}>
                      <Text style={styles.title}>AISJ Connect</Text>
                      <Text style={styles.subtitle}>Welcome back! Please login to continue.</Text>
                    </View>

                    <View style={styles.form}>
                      <View style={styles.inputContainer}>
                        <Text style={styles.label}>Email</Text>
                        <TextInput
                          style={styles.input}
                          placeholder="Enter your email"
                          placeholderTextColor="#9CA3AF"
                          value={email}
                          onChangeText={setEmail}
                          autoCapitalize="none"
                          keyboardType="email-address"
                          editable={!loading}
                        />
                      </View>

                      <View style={styles.inputContainer}>
                        <Text style={styles.label}>Password</Text>
                        <TextInput
                          style={styles.input}
                          placeholder="Enter your password"
                          placeholderTextColor="#9CA3AF"
                          value={password}
                          onChangeText={setPassword}
                          secureTextEntry
                          editable={!loading}
                        />
                      </View>

                      <TouchableOpacity
                        style={styles.button}
                        onPress={handleLogin}
                        disabled={loading}
                      >
                        {loading ? (
                          <ActivityIndicator color="#FFFFFF" />
                        ) : (
                          <Text style={styles.buttonText}>Login</Text>
                        )}
                      </TouchableOpacity>

                      <TouchableOpacity
                        style={styles.secondaryButton}
                        onPress={() => router.push('/register')}
                      >
                        <Text style={styles.secondaryButtonText}>Create Account</Text>
                      </TouchableOpacity>

                      <TouchableOpacity
                        style={styles.visitorButton}
                        onPress={() => router.push('/visitor')}
                      >
                        <Text style={styles.visitorButtonText}>Visitor Check-in</Text>
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
              backgroundColor: '#FFFFFF',
  },
              content: {
                flexGrow: 1,
              justifyContent: 'center',
              padding: 24,
  },
              header: {
                marginBottom: 48,
              alignItems: 'center',
  },
              title: {
                fontSize: 32,
              fontWeight: 'bold',
              color: '#1E3A5F',
              marginBottom: 8,
              textAlign: 'center',
  },
              subtitle: {
                fontSize: 16,
              color: '#6B7280',
              marginBottom: 32,
              textAlign: 'center',
  },
              form: {
                width: '100%',
  },
              inputContainer: {
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
              marginTop: 24,
  },
              buttonText: {
                color: '#FFFFFF',
              fontSize: 16,
              fontWeight: 'bold',
  },
              secondaryButton: {
                padding: 16,
              alignItems: 'center',
              marginTop: 8,
  },
              secondaryButtonText: {
                color: '#1E3A5F',
              fontSize: 16,
              fontWeight: '600',
  },
              visitorButton: {
                padding: 16,
              alignItems: 'center',
              marginTop: 8,
              borderTopWidth: 1,
              borderTopColor: '#E5E7EB',
  },
              visitorButtonText: {
                color: '#6B7280',
              fontSize: 14,
  },
});
