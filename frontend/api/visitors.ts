import client from './client';

export interface Visitor {
    _id: string;
    first_name: string;
    last_name: string;
    email?: string;
    phone?: string;
    purpose: string;
    host_user_id?: string;
    check_in_time: string;
    check_out_time?: string;
    is_active: boolean;
}

export interface VisitorCheckInRequest {
    first_name: string;
    last_name: string;
    email?: string;
    phone?: string;
    purpose: string;
    host_name?: string;
}

export const visitorsApi = {
    checkIn: async (data: VisitorCheckInRequest): Promise<Visitor> => {
        const response = await client.post<Visitor>('/api/visitors/check-in', data);
        return response.data;
    },

    getActiveVisitors: async (): Promise<Visitor[]> => {
        const response = await client.get<Visitor[]>('/api/visitors/active');
        return response.data;
    },

    checkOut: async (visitorId: string): Promise<Visitor> => {
        const response = await client.post<Visitor>(`/api/visitors/check-out/${visitorId}`);
        return response.data;
    },
};
