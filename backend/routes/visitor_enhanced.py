"""Enhanced Visitor Management - Photo capture, badges, watchlist, pre-registration"""

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from typing import List, Optional
from datetime import datetime, timedelta
from app.core.database import get_database
from utils.dependencies import require_role, get_current_active_user
from models.users import UserRole
from pydantic import BaseModel, EmailStr
from bson import ObjectId
import base64
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import qrcode

router = APIRouter(prefix='/visitors/enhanced', tags=['Visitor Management Enhanced'])


# ============================================
# MODELS
# ============================================

class VisitorPreRegistration(BaseModel):
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    purpose: str
    host_name: str
    host_email: EmailStr
    visit_date: datetime
    expected_duration_minutes: int = 60
    requires_escort: bool = False
    notes: Optional[str] = None


class VisitorCheckInWithPhoto(BaseModel):
    pre_registration_id: Optional[str] = None
    first_name: str
    last_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    purpose: str
    host_name: str
    photo_base64: Optional[str] = None  # Base64 encoded photo
    id_type: Optional[str] = None  # "drivers_license", "passport", etc.
    id_number: Optional[str] = None


class WatchlistEntry(BaseModel):
    first_name: str
    last_name: str
    reason: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    photo_base64: Optional[str] = None
    alert_type: str = "warning"  # "warning", "block"
    added_by: Optional[str] = None
    notes: Optional[str] = None


class VisitorBadgeData(BaseModel):
    visitor_id: str
    badge_number: str
    valid_until: datetime


# ============================================
# PRE-REGISTRATION
# ============================================

@router.post('/pre-register')
async def pre_register_visitor(
    visitor_data: VisitorPreRegistration,
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """
    Pre-register a visitor before their arrival.
    
    Available to: All authenticated users (for their own guests)
    """
    new_pre_registration = visitor_data.dict()
    new_pre_registration['status'] = 'pending'
    new_pre_registration['created_by'] = str(current_user['_id'])
    new_pre_registration['created_at'] = datetime.utcnow()
    new_pre_registration['checked_in'] = False
    
    result = await db.visitor_pre_registrations.insert_one(new_pre_registration)
    
    return {
        "id": str(result.inserted_id),
        "message": "Visitor pre-registered successfully",
        "visit_date": visitor_data.visit_date,
        "confirmation_code": str(result.inserted_id)[:8].upper()
    }


@router.get('/pre-registrations')
async def get_pre_registrations(
    date: Optional[str] = None,
    status: Optional[str] = None,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """
    Get all pre-registered visitors.
    
    Available to: Admin, Staff
    """
    query = {}
    
    if date:
        # Parse date and create range
        date_obj = datetime.fromisoformat(date)
        start_of_day = date_obj.replace(hour=0, minute=0, second=0)
        end_of_day = date_obj.replace(hour=23, minute=59, second=59)
        query['visit_date'] = {'$gte': start_of_day, '$lte': end_of_day}
    
    if status:
        query['status'] = status
    
    pre_registrations = await db.visitor_pre_registrations.find(query).sort('visit_date', 1).to_list(length=200)
    
    result = []
    for pr in pre_registrations:
        result.append({
            'id': str(pr['_id']),
            'first_name': pr['first_name'],
            'last_name': pr['last_name'],
            'email': pr.get('email'),
            'company': pr.get('company'),
            'purpose': pr['purpose'],
            'host_name': pr['host_name'],
            'visit_date': pr['visit_date'],
            'status': pr['status'],
            'checked_in': pr.get('checked_in', False),
            'confirmation_code': str(pr['_id'])[:8].upper()
        })
    
    return result


# ============================================
# CHECK-IN WITH PHOTO
# ============================================

@router.post('/check-in-with-photo')
async def check_in_visitor_with_photo(
    visitor_data: VisitorCheckInWithPhoto,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """
    Check in a visitor with photo capture.
    
    Available to: Admin, Staff
    """
    # Check watchlist first
    watchlist_check = await check_watchlist(
        visitor_data.first_name,
        visitor_data.last_name,
        visitor_data.email,
        db
    )
    
    if watchlist_check['on_watchlist'] and watchlist_check['alert_type'] == 'block':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Visitor is on watchlist (BLOCKED): {watchlist_check['reason']}"
        )
    
    # Create visitor record
    new_visitor = {
        'first_name': visitor_data.first_name,
        'last_name': visitor_data.last_name,
        'email': visitor_data.email,
        'phone': visitor_data.phone,
        'company': visitor_data.company,
        'purpose': visitor_data.purpose,
        'host_name': visitor_data.host_name,
        'photo_base64': visitor_data.photo_base64,
        'id_type': visitor_data.id_type,
        'id_number': visitor_data.id_number,
        'check_in_time': datetime.utcnow(),
        'check_out_time': None,
        'status': 'active',
        'checked_in_by': str(current_user['_id']),
        'watchlist_warning': watchlist_check['on_watchlist'],
        'watchlist_reason': watchlist_check.get('reason') if watchlist_check['on_watchlist'] else None
    }
    
    # If pre-registered, link to pre-registration
    if visitor_data.pre_registration_id:
        new_visitor['pre_registration_id'] = visitor_data.pre_registration_id
        await db.visitor_pre_registrations.update_one(
            {'_id': ObjectId(visitor_data.pre_registration_id)},
            {'$set': {'checked_in': True, 'status': 'checked_in'}}
        )
    
    result = await db.visitors.insert_one(new_visitor)
    visitor_id = str(result.inserted_id)
    
    # Generate badge
    badge_number = f"V{datetime.utcnow().strftime('%Y%m%d')}{str(result.inserted_id)[-4:]}"
    
    response = {
        "id": visitor_id,
        "badge_number": badge_number,
        "check_in_time": new_visitor['check_in_time'],
        "message": "Visitor checked in successfully"
    }
    
    if watchlist_check['on_watchlist']:
        response['warning'] = f"WATCHLIST ALERT: {watchlist_check['reason']}"
    
    return response


# ============================================
# WATCHLIST MANAGEMENT
# ============================================

@router.post('/watchlist')
async def add_to_watchlist(
    watchlist_data: WatchlistEntry,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db = Depends(get_database)
):
    """
    Add a person to the visitor watchlist.
    
    Available to: Admin only
    """
    new_entry = watchlist_data.dict()
    new_entry['added_by'] = str(current_user['_id'])
    new_entry['added_at'] = datetime.utcnow()
    new_entry['is_active'] = True
    
    result = await db.visitor_watchlist.insert_one(new_entry)
    
    return {
        "id": str(result.inserted_id),
        "message": "Person added to watchlist successfully"
    }


@router.get('/watchlist')
async def get_watchlist(
    active_only: bool = True,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """
    Get visitor watchlist.
    
    Available to: Admin, Staff
    """
    query = {'is_active': True} if active_only else {}
    
    watchlist = await db.visitor_watchlist.find(query).sort('added_at', -1).to_list(length=500)
    
    result = []
    for entry in watchlist:
        result.append({
            'id': str(entry['_id']),
            'first_name': entry['first_name'],
            'last_name': entry['last_name'],
            'reason': entry['reason'],
            'email': entry.get('email'),
            'phone': entry.get('phone'),
            'alert_type': entry['alert_type'],
            'added_at': entry['added_at'],
            'notes': entry.get('notes')
        })
    
    return result


@router.delete('/watchlist/{entry_id}')
async def remove_from_watchlist(
    entry_id: str,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db = Depends(get_database)
):
    """
    Remove a person from the watchlist.
    
    Available to: Admin only
    """
    result = await db.visitor_watchlist.update_one(
        {'_id': ObjectId(entry_id)},
        {'$set': {'is_active': False, 'removed_at': datetime.utcnow()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Watchlist entry not found")
    
    return {"message": "Person removed from watchlist"}


async def check_watchlist(first_name: str, last_name: str, email: Optional[str], db):
    """
    Internal function to check if visitor is on watchlist.
    """
    query = {
        'is_active': True,
        '$or': [
            {'first_name': {'$regex': f'^{first_name}$', '$options': 'i'},
             'last_name': {'$regex': f'^{last_name}$', '$options': 'i'}}
        ]
    }
    
    if email:
        query['$or'].append({'email': email})
    
    watchlist_entry = await db.visitor_watchlist.find_one(query)
    
    if watchlist_entry:
        return {
            'on_watchlist': True,
            'alert_type': watchlist_entry['alert_type'],
            'reason': watchlist_entry['reason']
        }
    
    return {'on_watchlist': False}


# ============================================
# BADGE GENERATION
# ============================================

@router.get('/badge/{visitor_id}/generate')
async def generate_visitor_badge(
    visitor_id: str,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """
    Generate a digital visitor badge (PDF).
    
    Available to: Admin, Staff
    Returns: Base64 encoded PDF
    """
    visitor = await db.visitors.find_one({'_id': ObjectId(visitor_id)})
    
    if not visitor:
        raise HTTPException(status_code=404, detail="Visitor not found")
    
    # Generate badge PDF
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=(4*72, 6*72))  # 4x6 inch badge
    
    # Badge design
    c.setFont("Helvetica-Bold", 24)
    c.drawString(40, 380, "VISITOR")
    
    c.setFont("Helvetica", 14)
    c.drawString(40, 340, f"{visitor['first_name']} {visitor['last_name']}")
    
    if visitor.get('company'):
        c.setFont("Helvetica", 10)
        c.drawString(40, 320, f"Company: {visitor['company']}")
    
    c.setFont("Helvetica", 10)
    c.drawString(40, 300, f"Host: {visitor['host_name']}")
    
    # Badge number
    badge_number = f"V{visitor['check_in_time'].strftime('%Y%m%d')}{str(visitor['_id'])[-4:]}"
    c.drawString(40, 280, f"Badge #: {badge_number}")
    
    # Date/Time
    c.drawString(40, 260, f"Check-in: {visitor['check_in_time'].strftime('%m/%d/%Y %I:%M %p')}")
    
    # Valid until (default: end of day)
    valid_until = visitor['check_in_time'].replace(hour=23, minute=59, second=59)
    c.drawString(40, 240, f"Valid until: {valid_until.strftime('%I:%M %p')}")
    
    # Generate QR code
    qr = qrcode.QRCode(version=1, box_size=3, border=1)
    qr.add_data(visitor_id)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Save QR to bytes
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    
    # Add QR code to badge
    c.drawImage(ImageReader(qr_buffer), 70, 80, width=120, height=120)
    
    # Add photo if available
    if visitor.get('photo_base64'):
        try:
            photo_data = base64.b64decode(visitor['photo_base64'].split(',')[-1])
            photo_buffer = io.BytesIO(photo_data)
            c.drawImage(ImageReader(photo_buffer), 40, 420, width=100, height=120)
        except:
            pass
    
    c.save()
    
    # Convert PDF to base64
    buffer.seek(0)
    pdf_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    
    return {
        "badge_pdf_base64": pdf_base64,
        "badge_number": badge_number,
        "visitor_name": f"{visitor['first_name']} {visitor['last_name']}",
        "valid_until": valid_until
    }


# ============================================
# ANALYTICS
# ============================================

@router.get('/analytics/summary')
async def get_visitor_analytics(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """
    Get visitor analytics summary.
    
    Available to: Admin, Staff
    """
    query = {}
    
    if start_date and end_date:
        query['check_in_time'] = {
            '$gte': datetime.fromisoformat(start_date),
            '$lte': datetime.fromisoformat(end_date)
        }
    
    total_visitors = await db.visitors.count_documents(query)
    active_visitors = await db.visitors.count_documents({**query, 'status': 'active'})
    
    # Pre-registrations
    total_pre_reg = await db.visitor_pre_registrations.count_documents({})
    checked_in_from_pre_reg = await db.visitor_pre_registrations.count_documents({'checked_in': True})
    
    # Average visit duration
    completed_visits = await db.visitors.find({
        **query,
        'check_out_time': {'$ne': None}
    }).to_list(length=1000)
    
    if completed_visits:
        total_duration = sum(
            (v['check_out_time'] - v['check_in_time']).total_seconds() / 60
            for v in completed_visits
        )
        avg_duration = total_duration / len(completed_visits)
    else:
        avg_duration = 0
    
    return {
        "total_visitors": total_visitors,
        "active_visitors": active_visitors,
        "completed_visits": len(completed_visits),
        "average_duration_minutes": round(avg_duration, 2),
        "pre_registrations": {
            "total": total_pre_reg,
            "checked_in": checked_in_from_pre_reg,
            "conversion_rate": round((checked_in_from_pre_reg / total_pre_reg * 100), 2) if total_pre_reg > 0 else 0
        }
    }
