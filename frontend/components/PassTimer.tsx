import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface PassTimerProps {
    departedAt: string;
    timeLimitMinutes: number;
    onExpire?: () => void;
}

export const PassTimer: React.FC<PassTimerProps> = ({ departedAt, timeLimitMinutes, onExpire }) => {
    const [timeLeft, setTimeLeft] = useState<string>('00:00');
    const [isOvertime, setIsOvertime] = useState(false);

    useEffect(() => {
        const interval = setInterval(() => {
            const start = new Date(departedAt).getTime();
            const limit = timeLimitMinutes * 60 * 1000;
            const now = new Date().getTime();
            const elapsed = now - start;
            const remaining = limit - elapsed;

            if (remaining <= 0) {
                setIsOvertime(true);
                const overtime = Math.abs(remaining);
                setTimeLeft(`-${formatTime(overtime)}`);
                if (onExpire) onExpire();
            } else {
                setIsOvertime(false);
                setTimeLeft(formatTime(remaining));
            }
        }, 1000);

        return () => clearInterval(interval);
    }, [departedAt, timeLimitMinutes]);

    const formatTime = (ms: number) => {
        const totalSeconds = Math.floor(ms / 1000);
        const minutes = Math.floor(totalSeconds / 60);
        const seconds = totalSeconds % 60;
        return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    };

    return (
        <View style={[styles.container, isOvertime && styles.overtimeContainer]}>
            <Text style={[styles.timerText, isOvertime && styles.overtimeText]}>
                {timeLeft}
            </Text>
            <Text style={[styles.statusText, isOvertime && styles.overtimeText]}>
                {isOvertime ? 'OVERTIME' : 'REMAINING'}
            </Text>
        </View>
    );
};

const styles = StyleSheet.create({
    container: {
        alignItems: 'center',
        justifyContent: 'center',
        padding: 24,
        borderRadius: 100,
        borderWidth: 4,
        borderColor: '#10B981',
        width: 200,
        height: 200,
        backgroundColor: '#FFFFFF',
        marginBottom: 24,
    },
    overtimeContainer: {
        borderColor: '#EF4444',
        backgroundColor: '#FEF2F2',
    },
    timerText: {
        fontSize: 48,
        fontWeight: 'bold',
        color: '#10B981',
        fontVariant: ['tabular-nums'],
    },
    statusText: {
        fontSize: 14,
        fontWeight: '600',
        color: '#10B981',
        marginTop: 4,
    },
    overtimeText: {
        color: '#EF4444',
    },
});
