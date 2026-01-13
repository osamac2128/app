from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from pydantic import BaseModel
from datetime import datetime
from app.core.database import get_database
from utils.dependencies import get_current_active_user, require_role
from models.digital_ids import DigitalID, DigitalIDCreate, PhotoStatus
from models.users import UserRole
from bson import ObjectId
import base64

router = APIRouter(prefix='/digital-ids', tags=['Digital IDs'])

class PhotoUploadResponse(BaseModel):
    message: str
    photo_url: str
    status: str

@router.get('/my-id', response_model=DigitalID)
async def get_my_digital_id(current_user: dict = Depends(get_current_active_user), db = Depends(get_database)):
    """Get current user's digital ID. Create one if it doesn't exist."""
    user_id = str(current_user['_id'])
    
    # Try to find existing ID
    digital_id = await db.digital_ids.find_one({'user_id': user_id})
    
    if digital_id:
        digital_id['_id'] = str(digital_id['_id'])
        return digital_id
    
    # Create new ID if not exists
    # Generate simple unique codes based on user ID and timestamp
    timestamp = int(datetime.utcnow().timestamp())
    qr_code = f"AISJ:{user_id}:{timestamp}"
    barcode = f"{timestamp}"
    
    new_id_data = {
        'user_id': user_id,
        'qr_code': qr_code,
        'barcode': barcode,
        'photo_url': current_user.get('profile_photo_url'),
        'photo_status': PhotoStatus.APPROVED if current_user.get('profile_photo_url') else PhotoStatus.PENDING,
        'is_active': True,
        'issued_at': datetime.utcnow(),
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    
    result = await db.digital_ids.insert_one(new_id_data)
    new_id_data['_id'] = str(result.inserted_id)
    
    return new_id_data

@router.post('/upload-photo', response_model=PhotoUploadResponse)
async def upload_photo(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_active_user),
    db = Depends(get_database)
):
    """Upload a photo for the digital ID."""
    # Validate file type
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='File must be an image'
        )
    
    # Read file content
    content = await file.read()
    
    # Encode to base64
    # In production, this should upload to S3/Cloud Storage and return a URL
    base64_image = f"data:{file.content_type};base64,{base64.b64encode(content).decode('utf-8')}"
    user_id = str(current_user['_id'])
    
    # Update Digital ID
    await db.digital_ids.update_one(
        {'user_id': user_id},
        {
            '$set': {
                'submitted_photo_url': base64_image,
                'photo_status': PhotoStatus.PENDING,
                'updated_at': datetime.utcnow()
            }
        },
        upsert=True
    )
    
    return {
        'message': 'Photo uploaded successfully. Pending approval.',
        'photo_url': base64_image,
        'status': PhotoStatus.PENDING
    }

@router.post('/admin/approve-photo/{id_id}')
async def approve_photo(
    id_id: str,
    approved: bool,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """Approve or reject a submitted photo (Admin/Staff only)."""
    
    digital_id = await db.digital_ids.find_one({'_id': ObjectId(id_id)})
    if not digital_id:
        raise HTTPException(status_code=404, detail="Digital ID not found")
        
    if not digital_id.get('submitted_photo_url'):
        raise HTTPException(status_code=400, detail="No photo submitted for approval")
    
    update_data = {
        'photo_status': PhotoStatus.APPROVED if approved else PhotoStatus.REJECTED,
        'photo_reviewed_by': str(current_user['_id']),
        'photo_reviewed_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    
    if approved:
        update_data['photo_url'] = digital_id['submitted_photo_url']
        update_data['submitted_photo_url'] = None
    
    await db.digital_ids.update_one(
        {'_id': ObjectId(id_id)},
        {'$set': update_data}
    )
    
    return {"message": f"Photo {'approved' if approved else 'rejected'}"}


@router.get('/scan/{qr_code}')
async def scan_id(
    qr_code: str,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """(Staff/Admin) Scan a QR code to verify a digital ID."""

    # Find the digital ID by QR code
    digital_id = await db.digital_ids.find_one({'qr_code': qr_code})

    if not digital_id:
        raise HTTPException(status_code=404, detail="Digital ID not found")

    if not digital_id.get('is_active'):
        raise HTTPException(status_code=400, detail="This ID has been deactivated")

    # Get user information
    user = await db.users.find_one({'_id': ObjectId(digital_id['user_id'])})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Log the scan
    scan_log = {
        'digital_id_id': str(digital_id['_id']),
        'scanned_by': str(current_user['_id']),
        'scanned_at': datetime.utcnow(),
        'location': None,  # Could be passed as query param
        'purpose': 'verification',
        'created_at': datetime.utcnow()
    }
    await db.id_scan_logs.insert_one(scan_log)

    return {
        'valid': True,
        'user': {
            '_id': str(user['_id']),
            'first_name': user.get('first_name'),
            'last_name': user.get('last_name'),
            'email': user.get('email'),
            'role': user.get('role'),
            'status': user.get('status')
        },
        'digital_id': {
            '_id': str(digital_id['_id']),
            'qr_code': digital_id.get('qr_code'),
            'barcode': digital_id.get('barcode'),
            'photo_url': digital_id.get('photo_url'),
            'is_active': digital_id.get('is_active'),
            'issued_at': digital_id.get('issued_at')
        }
    }


@router.get('/admin/pending-photos')
async def get_pending_photos(
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """(Staff/Admin) Get all digital IDs with pending photo approval."""

    pending_ids = await db.digital_ids.find({
        'photo_status': PhotoStatus.PENDING,
        'submitted_photo_url': {'$ne': None}
    }).to_list(length=100)

    result = []
    for digital_id in pending_ids:
        user = await db.users.find_one({'_id': ObjectId(digital_id['user_id'])})
        if user:
            result.append({
                '_id': str(digital_id['_id']),
                'user_id': digital_id['user_id'],
                'user_name': f"{user.get('first_name', '')} {user.get('last_name', '')}",
                'user_role': user.get('role'),
                'submitted_photo_url': digital_id.get('submitted_photo_url'),
                'photo_status': digital_id.get('photo_status'),
                'updated_at': digital_id.get('updated_at')
            })

    return result


@router.post('/admin/deactivate/{id_id}')
async def deactivate_id(
    id_id: str,
    reason: str = "Admin deactivation",
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db = Depends(get_database)
):
    """(Admin only) Deactivate a digital ID."""

    digital_id = await db.digital_ids.find_one({'_id': ObjectId(id_id)})
    if not digital_id:
        raise HTTPException(status_code=404, detail="Digital ID not found")

    await db.digital_ids.update_one(
        {'_id': ObjectId(id_id)},
        {
            '$set': {
                'is_active': False,
                'deactivated_at': datetime.utcnow(),
                'deactivation_reason': reason,
                'deactivated_by': str(current_user['_id']),
                'updated_at': datetime.utcnow()
            }
        }
    )

    return {"message": "Digital ID deactivated successfully"}


@router.post('/admin/reactivate/{id_id}')
async def reactivate_id(
    id_id: str,
    current_user: dict = Depends(require_role(UserRole.ADMIN)),
    db = Depends(get_database)
):
    """(Admin only) Reactivate a digital ID."""

    digital_id = await db.digital_ids.find_one({'_id': ObjectId(id_id)})
    if not digital_id:
        raise HTTPException(status_code=404, detail="Digital ID not found")

    await db.digital_ids.update_one(
        {'_id': ObjectId(id_id)},
        {
            '$set': {
                'is_active': True,
                'deactivated_at': None,
                'deactivation_reason': None,
                'reactivated_by': str(current_user['_id']),
                'updated_at': datetime.utcnow()
            }
        }
    )

    return {"message": "Digital ID reactivated successfully"}


@router.get('/scan-history')
async def get_scan_history(
    limit: int = 50,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF)),
    db = Depends(get_database)
):
    """(Staff/Admin) Get recent ID scan history."""

    scans = await db.id_scan_logs.find().sort('scanned_at', -1).limit(limit).to_list(length=limit)

    result = []
    for scan in scans:
        # Get scanned user info
        digital_id = await db.digital_ids.find_one({'_id': ObjectId(scan['digital_id_id'])})
        scanned_user = None
        if digital_id:
            scanned_user = await db.users.find_one({'_id': ObjectId(digital_id['user_id'])})

        # Get scanner info
        scanner = await db.users.find_one({'_id': ObjectId(scan['scanned_by'])})

        result.append({
            '_id': str(scan['_id']),
            'scanned_at': scan.get('scanned_at'),
            'scanned_user': {
                'name': f"{scanned_user.get('first_name', '')} {scanned_user.get('last_name', '')}" if scanned_user else 'Unknown',
                'role': scanned_user.get('role') if scanned_user else None
            } if scanned_user else None,
            'scanned_by': {
                'name': f"{scanner.get('first_name', '')} {scanner.get('last_name', '')}" if scanner else 'Unknown',
                'role': scanner.get('role') if scanner else None
            } if scanner else None,
            'purpose': scan.get('purpose'),
            'location': scan.get('location')
        })

    return result
