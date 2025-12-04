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
async def get_my_digital_id(current_user: dict = Depends(get_current_active_user)):
    """Get current user's digital ID. Create one if it doesn't exist."""
    db = get_database()
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
    current_user: dict = Depends(get_current_active_user)
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
    
    db = get_database()
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
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF))
):
    """Approve or reject a submitted photo (Admin/Staff only)."""
    db = get_database()
    
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
