import client from './client';

export interface DigitalID {
    _id: string;
    user_id: string;
    qr_code: string;
    barcode: string;
    photo_url?: string;
    status: 'active' | 'inactive' | 'suspended';
    issued_at: string;
    expires_at?: string;
}

export const digitalIdsApi = {
    getMyId: async (): Promise<DigitalID> => {
        const response = await client.get<DigitalID>('/api/digital-ids/my-id');
        return response.data;
    },

    uploadPhoto: async (formData: FormData): Promise<DigitalID> => {
        const response = await client.post<DigitalID>('/api/digital-ids/upload-photo', formData, {
            headers: {
                'Content-Type': 'multipart/form-data',
            },
        });
        return response.data;
    },
};
