import client from './client';

export interface Location {
    _id: string;
    name: string;
    type: string;
    max_capacity?: number;
    requires_approval: boolean;
    default_time_limit_minutes: number;
    is_active: boolean;
}

export interface Pass {
    _id: string;
    student_id: string;
    origin_location_id: string;
    destination_location_id: string;
    status: 'active' | 'completed' | 'pending' | 'approved' | 'rejected' | 'expired';
    requested_at: string;
    departed_at?: string;
    returned_at?: string;
    time_limit_minutes: number;
    is_overtime: boolean;
    notes?: string;
}

export interface PassCreate {
    origin_location_id: string;
    destination_location_id: string;
    time_limit_minutes: number;
    notes?: string;
}

export const passesApi = {
    getLocations: async (): Promise<Location[]> => {
        const response = await client.get<Location[]>('/api/passes/locations');
        return response.data;
    },

    requestPass: async (data: PassCreate): Promise<Pass> => {
        const response = await client.post<Pass>('/api/passes/request', data);
        return response.data;
    },

    getActivePass: async (): Promise<Pass> => {
        const response = await client.get<Pass>('/api/passes/active');
        return response.data;
    },

    endPass: async (passId: string): Promise<Pass> => {
        const response = await client.post<Pass>(`/api/passes/end/${passId}`);
        return response.data;
    },

    getHallMonitorPasses: async (): Promise<Pass[]> => {
        const response = await client.get<Pass[]>('/api/passes/hall-monitor');
        return response.data;
    },
};
