"""Real-time WebSocket status and management routes"""

from fastapi import APIRouter, Depends
from app.core.websocket import get_connection_stats, manager
from utils.dependencies import require_role
from models.users import UserRole

router = APIRouter(prefix='/realtime', tags=['Real-Time'])


@router.get('/status')
async def get_realtime_status(
    current_user: dict = Depends(require_role(UserRole.ADMIN))
):
    """
    Get real-time connection status (Admin only).

    Returns current WebSocket connection statistics including online users,
    active connections, and room membership.
    """
    stats = get_connection_stats()
    return {
        'status': 'operational',
        'websocket_enabled': True,
        'statistics': stats
    }


@router.get('/online-users')
async def get_online_users(
    current_user: dict = Depends(require_role(UserRole.STAFF, UserRole.ADMIN))
):
    """
    Get count of currently online users (Staff/Admin only).
    """
    return {
        'online_users': manager.get_online_user_count(),
        'total_connections': len(manager.session_users)
    }


@router.get('/rooms')
async def get_active_rooms(
    current_user: dict = Depends(require_role(UserRole.ADMIN))
):
    """
    Get active rooms and their member counts (Admin only).
    """
    rooms_info = {}
    for room_name, sessions in manager.rooms.items():
        rooms_info[room_name] = {
            'connections': len(sessions),
            'session_ids': list(sessions)[:10]  # Limit for privacy
        }
    return {'rooms': rooms_info}
