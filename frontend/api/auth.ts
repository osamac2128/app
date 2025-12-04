import client from './client';

export interface User {
    _id: string;
    email: string;
    first_name: string;
    last_name: string;
    role: 'student' | 'parent' | 'staff' | 'admin';
    phone?: string;
    profile_photo_url?: string;
    status: string;
}

export interface AuthResponse {
    access_token: string;
    token_type: string;
    user: User;
}

export interface LoginRequest {
    email: string;
    password: string;
}

export interface RegisterRequest {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    role: 'student' | 'parent' | 'staff' | 'admin';
    phone?: string;
}

export const authApi = {
    login: async (data: LoginRequest): Promise<AuthResponse> => {
        const response = await client.post<AuthResponse>('/api/auth/login', data);
        return response.data;
    },

    register: async (data: RegisterRequest): Promise<AuthResponse> => {
        const response = await client.post<AuthResponse>('/api/auth/register', data);
        return response.data;
    },

    updateProfile: async (data: Partial<User>): Promise<User> => {
        const response = await client.put<User>('/api/auth/me', data);
        return response.data;
    },

    getMe: async (): Promise<User> => {
        const response = await client.get<User>('/api/auth/me');
        return response.data;
    },
};
