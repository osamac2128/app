import client from './client';

export interface EmergencyAlert {
    _id: string;
    type: string;
    title: string;
    message: string;
    instructions: string;
    triggered_by_user_id: string;
    triggered_at: string;
    resolved_at?: string;
    is_active: boolean;
}

export interface EmergencyCheckIn {
    _id: string;
    alert_id: string;
    user_id: string;
    status: 'safe' | 'need_help';
    location?: {
        latitude: number;
        longitude: number;
    };
    checked_in_at: string;
}

export const emergencyApi = {
    getActiveAlert: async (): Promise<EmergencyAlert | null> => {
        const response = await client.get<EmergencyAlert | null>('/api/emergency/active');
        return response.data;
    },

    triggerAlert: async (type: string): Promise<EmergencyAlert> => {
        const response = await client.post<EmergencyAlert>('/api/emergency/trigger', { type });
        return response.data;
    },

    resolveAlert: async (alertId: string): Promise<EmergencyAlert> => {
        const response = await client.post<EmergencyAlert>(`/api/emergency/resolve/${alertId}`);
        return response.data;
    },

    checkIn: async (status: 'safe' | 'need_help', location?: { latitude: number; longitude: number }): Promise<EmergencyCheckIn> => {
        const response = await client.post<EmergencyCheckIn>('/api/emergency/check-in', { status, location });
        return response.data;
    },
};
