"""WebSocket/Socket.IO Manager for Real-Time Communications"""

import socketio
import logging
from typing import Dict, Set, Optional
from datetime import datetime
import jwt
from app.core.config import settings

logger = logging.getLogger(__name__)

# Create Socket.IO server with ASGI support
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.ALLOWED_ORIGINS,
    logger=True,
    engineio_logger=True if settings.DEBUG else False
)


class ConnectionManager:
    """Manages WebSocket connections and rooms"""

    def __init__(self):
        # Map of user_id to set of session IDs
        self.user_connections: Dict[str, Set[str]] = {}
        # Map of session_id to user_id
        self.session_users: Dict[str, str] = {}
        # Map of room name to set of session IDs
        self.rooms: Dict[str, Set[str]] = {}

    async def connect(self, sid: str, user_id: str) -> None:
        """Register a new connection"""
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(sid)
        self.session_users[sid] = user_id
        logger.info(f"User {user_id} connected with session {sid}")

    async def disconnect(self, sid: str) -> Optional[str]:
        """Remove a connection"""
        user_id = self.session_users.pop(sid, None)
        if user_id and user_id in self.user_connections:
            self.user_connections[user_id].discard(sid)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]

        # Remove from all rooms
        for room_sessions in self.rooms.values():
            room_sessions.discard(sid)

        logger.info(f"Session {sid} disconnected (user: {user_id})")
        return user_id

    async def join_room(self, sid: str, room: str) -> None:
        """Add a session to a room"""
        if room not in self.rooms:
            self.rooms[room] = set()
        self.rooms[room].add(sid)
        await sio.enter_room(sid, room)
        logger.info(f"Session {sid} joined room {room}")

    async def leave_room(self, sid: str, room: str) -> None:
        """Remove a session from a room"""
        if room in self.rooms:
            self.rooms[room].discard(sid)
        await sio.leave_room(sid, room)
        logger.info(f"Session {sid} left room {room}")

    def get_user_sessions(self, user_id: str) -> Set[str]:
        """Get all sessions for a user"""
        return self.user_connections.get(user_id, set())

    def is_user_online(self, user_id: str) -> bool:
        """Check if a user has any active connections"""
        return bool(self.user_connections.get(user_id))

    def get_online_user_count(self) -> int:
        """Get the number of online users"""
        return len(self.user_connections)


# Global connection manager instance
manager = ConnectionManager()


def verify_socket_token(token: str) -> Optional[dict]:
    """Verify JWT token for socket connections"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Socket auth failed: Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Socket auth failed: {e}")
        return None


# Socket.IO Event Handlers

@sio.event
async def connect(sid, environ, auth):
    """Handle new socket connection"""
    logger.info(f"New socket connection attempt: {sid}")

    # Extract token from auth
    token = None
    if auth and isinstance(auth, dict):
        token = auth.get('token')

    if not token:
        logger.warning(f"Connection rejected: No token provided for {sid}")
        return False

    # Verify token
    payload = verify_socket_token(token)
    if not payload:
        logger.warning(f"Connection rejected: Invalid token for {sid}")
        return False

    user_id = payload.get('sub')
    user_role = payload.get('role')

    if not user_id:
        logger.warning(f"Connection rejected: No user_id in token for {sid}")
        return False

    # Register connection
    await manager.connect(sid, user_id)

    # Auto-join role-based rooms
    await manager.join_room(sid, f"role:{user_role}")
    await manager.join_room(sid, f"user:{user_id}")

    # Staff and Admin auto-join hall monitor room
    if user_role in ['STAFF', 'ADMIN']:
        await manager.join_room(sid, 'hall_monitor')
        await manager.join_room(sid, 'emergency_alerts')

    # Emit successful connection
    await sio.emit('connected', {
        'message': 'Successfully connected',
        'user_id': user_id,
        'role': user_role,
        'timestamp': datetime.utcnow().isoformat()
    }, to=sid)

    logger.info(f"User {user_id} ({user_role}) connected successfully")
    return True


@sio.event
async def disconnect(sid):
    """Handle socket disconnection"""
    user_id = await manager.disconnect(sid)
    logger.info(f"Socket disconnected: {sid} (user: {user_id})")


@sio.event
async def join_room(sid, data):
    """Handle room join request"""
    room = data.get('room') if isinstance(data, dict) else data
    if room:
        await manager.join_room(sid, room)
        await sio.emit('room_joined', {'room': room}, to=sid)


@sio.event
async def leave_room(sid, data):
    """Handle room leave request"""
    room = data.get('room') if isinstance(data, dict) else data
    if room:
        await manager.leave_room(sid, room)
        await sio.emit('room_left', {'room': room}, to=sid)


# Real-time Event Emitters

async def emit_pass_created(pass_data: dict):
    """Emit when a new pass is created"""
    event_data = {
        'type': 'pass_created',
        'pass': pass_data,
        'timestamp': datetime.utcnow().isoformat()
    }
    # Notify hall monitors
    await sio.emit('pass_created', event_data, room='hall_monitor')
    # Notify the student
    student_id = pass_data.get('student_id')
    if student_id:
        await sio.emit('pass_created', event_data, room=f'user:{student_id}')
    logger.info(f"Emitted pass_created event for pass {pass_data.get('_id')}")


async def emit_pass_approved(pass_data: dict):
    """Emit when a pass is approved"""
    event_data = {
        'type': 'pass_approved',
        'pass': pass_data,
        'timestamp': datetime.utcnow().isoformat()
    }
    # Notify hall monitors
    await sio.emit('pass_approved', event_data, room='hall_monitor')
    # Notify the student
    student_id = pass_data.get('student_id')
    if student_id:
        await sio.emit('pass_approved', event_data, room=f'user:{student_id}')
    logger.info(f"Emitted pass_approved event for pass {pass_data.get('_id')}")


async def emit_pass_rejected(pass_data: dict, reason: Optional[str] = None):
    """Emit when a pass is rejected/denied"""
    event_data = {
        'type': 'pass_rejected',
        'pass': pass_data,
        'reason': reason,
        'timestamp': datetime.utcnow().isoformat()
    }
    # Notify the student
    student_id = pass_data.get('student_id')
    if student_id:
        await sio.emit('pass_rejected', event_data, room=f'user:{student_id}')
    # Notify hall monitors
    await sio.emit('pass_rejected', event_data, room='hall_monitor')
    logger.info(f"Emitted pass_rejected event for pass {pass_data.get('_id')}")


async def emit_pass_completed(pass_data: dict):
    """Emit when a pass is completed/ended"""
    event_data = {
        'type': 'pass_completed',
        'pass': pass_data,
        'timestamp': datetime.utcnow().isoformat()
    }
    # Notify hall monitors
    await sio.emit('pass_completed', event_data, room='hall_monitor')
    logger.info(f"Emitted pass_completed event for pass {pass_data.get('_id')}")


async def emit_pass_overtime(pass_data: dict, minutes_overtime: int):
    """Emit when a pass goes overtime"""
    event_data = {
        'type': 'pass_overtime',
        'pass': pass_data,
        'minutes_overtime': minutes_overtime,
        'timestamp': datetime.utcnow().isoformat()
    }
    # Notify hall monitors
    await sio.emit('pass_overtime', event_data, room='hall_monitor')
    # Notify the student
    student_id = pass_data.get('student_id')
    if student_id:
        await sio.emit('pass_overtime', event_data, room=f'user:{student_id}')
    # Notify admins
    await sio.emit('pass_overtime', event_data, room='role:ADMIN')
    logger.info(f"Emitted pass_overtime event for pass {pass_data.get('_id')} ({minutes_overtime} mins)")


async def emit_emergency_triggered(alert_data: dict):
    """Emit when an emergency is triggered"""
    event_data = {
        'type': 'emergency_triggered',
        'alert': alert_data,
        'timestamp': datetime.utcnow().isoformat()
    }
    # Broadcast to all connected users
    await sio.emit('emergency_triggered', event_data)
    logger.info(f"Emitted emergency_triggered event: {alert_data.get('alert_type')}")


async def emit_emergency_updated(alert_data: dict):
    """Emit when an emergency status is updated"""
    event_data = {
        'type': 'emergency_updated',
        'alert': alert_data,
        'timestamp': datetime.utcnow().isoformat()
    }
    # Broadcast to all connected users
    await sio.emit('emergency_updated', event_data)
    logger.info(f"Emitted emergency_updated event: {alert_data.get('status')}")


async def emit_emergency_ended(alert_data: dict):
    """Emit when an emergency is ended/resolved"""
    event_data = {
        'type': 'emergency_ended',
        'alert': alert_data,
        'timestamp': datetime.utcnow().isoformat()
    }
    # Broadcast to all connected users
    await sio.emit('emergency_ended', event_data)
    logger.info(f"Emitted emergency_ended event")


async def emit_checkin_update(checkin_data: dict):
    """Emit when a student checks in during emergency"""
    event_data = {
        'type': 'checkin_update',
        'checkin': checkin_data,
        'timestamp': datetime.utcnow().isoformat()
    }
    # Notify emergency coordinators
    await sio.emit('checkin_update', event_data, room='emergency_alerts')
    logger.info(f"Emitted checkin_update event")


async def emit_visitor_checkin(visitor_data: dict):
    """Emit when a visitor checks in"""
    event_data = {
        'type': 'visitor_checkin',
        'visitor': visitor_data,
        'timestamp': datetime.utcnow().isoformat()
    }
    # Notify front desk / admin
    await sio.emit('visitor_checkin', event_data, room='role:ADMIN')
    await sio.emit('visitor_checkin', event_data, room='role:STAFF')
    logger.info(f"Emitted visitor_checkin event")


async def emit_visitor_checkout(visitor_data: dict):
    """Emit when a visitor checks out"""
    event_data = {
        'type': 'visitor_checkout',
        'visitor': visitor_data,
        'timestamp': datetime.utcnow().isoformat()
    }
    # Notify front desk / admin
    await sio.emit('visitor_checkout', event_data, room='role:ADMIN')
    await sio.emit('visitor_checkout', event_data, room='role:STAFF')
    logger.info(f"Emitted visitor_checkout event")


async def emit_to_user(user_id: str, event: str, data: dict):
    """Emit an event to a specific user"""
    await sio.emit(event, data, room=f'user:{user_id}')
    logger.info(f"Emitted {event} to user {user_id}")


async def broadcast_to_role(role: str, event: str, data: dict):
    """Broadcast an event to all users with a specific role"""
    await sio.emit(event, data, room=f'role:{role}')
    logger.info(f"Broadcast {event} to role {role}")


# Get connection stats
def get_connection_stats() -> dict:
    """Get current connection statistics"""
    return {
        'online_users': manager.get_online_user_count(),
        'total_connections': len(manager.session_users),
        'rooms': {room: len(sessions) for room, sessions in manager.rooms.items()}
    }
