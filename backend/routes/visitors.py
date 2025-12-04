from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from datetime import datetime
from app.core.database import get_database
from utils.dependencies import get_current_active_user, require_role
from pydantic import BaseModel, Field
from models.users import UserRole
from bson import ObjectId

router = APIRouter(prefix='/visitors', tags=['Visitor Management'])

class VisitorCheckIn(BaseModel):
    first_name: str
    last_name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    purpose: str
    host_name: Optional[str] = None
    
class Visitor(VisitorCheckIn):
    id: Optional[str] = Field(default=None, alias="_id")
    check_in_time: datetime = Field(default_factory=datetime.utcnow)
    check_out_time: Optional[datetime] = None
    is_active: bool = True

@router.post('/check-in', response_model=Visitor)
async def visitor_check_in(visitor_data: VisitorCheckIn):
    """Visitor self-check-in (Public endpoint)."""
    db = get_database()
    
    new_visitor = visitor_data.dict()
    new_visitor['check_in_time'] = datetime.utcnow()
    new_visitor['is_active'] = True
    
    result = await db.visitors.insert_one(new_visitor)
    new_visitor['_id'] = str(result.inserted_id)
    
    return new_visitor

@router.get('/active', response_model=List[Visitor])
async def get_active_visitors(
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF))
):
    """(Admin/Staff) List active visitors."""
    db = get_database()
    visitors = await db.visitors.find({'is_active': True}).to_list(length=100)
    for v in visitors:
        v['_id'] = str(v['_id'])
    return visitors

@router.post('/check-out/{visitor_id}', response_model=Visitor)
async def visitor_check_out(
    visitor_id: str,
    current_user: dict = Depends(require_role(UserRole.ADMIN, UserRole.STAFF))
):
    """(Admin/Staff) Check out a visitor."""
    db = get_database()
    
    visitor = await db.visitors.find_one({'_id': ObjectId(visitor_id)})
    if not visitor:
        raise HTTPException(status_code=404, detail="Visitor not found")
        
    update_data = {
        'check_out_time': datetime.utcnow(),
        'is_active': False
    }
    
    await db.visitors.update_one(
        {'_id': ObjectId(visitor_id)},
        {'$set': update_data}
    )
    
    visitor.update(update_data)
    visitor['_id'] = str(visitor['_id'])
    return visitor
