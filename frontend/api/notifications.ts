import client from './client';

export interface Notification {
    _id: string;
    title: string;
    message: string;
    type: string;
    created_at: string;
    is_read: boolean;
}

export const notificationsApi = {
    getMyNotifications: async (): Promise<Notification[]> => {
        const response = await client.get<Notification[]>('/api/notifications/my-notifications');
        return response.data;
    },

    markAsRead: async (notificationId: string): Promise<void> => {
        await client.post(`/api/notifications/mark-read/${notificationId}`);
    },

    sendNotification: async (data: { title: string; message: string; target_role: string }): Promise<void> => {
        await client.post('/api/notifications/send', data);
    },
};
