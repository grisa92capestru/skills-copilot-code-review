"""
Announcement endpoints for the High School Management System API
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from pymongo import ReturnDocument
from bson import ObjectId
from bson.errors import InvalidId
import uuid

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


class AnnouncementPayload(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)
    expires_at: str
    starts_at: Optional[str] = None


def parse_iso_datetime(date_value: Optional[str], field_name: str) -> Optional[datetime]:
    if date_value is None or date_value == "":
        return None

    raw_value = date_value.strip()
    if raw_value.endswith("Z"):
        raw_value = raw_value.replace("Z", "+00:00")

    try:
        parsed = datetime.fromisoformat(raw_value)
    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be a valid ISO-8601 datetime"
        ) from error

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    else:
        parsed = parsed.astimezone(timezone.utc)

    return parsed


def verify_signed_in_user(username: Optional[str]) -> Dict[str, Any]:
    if not username:
        raise HTTPException(status_code=401, detail="Authentication required")

    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

    return teacher


def build_announcement_id_query(announcement_id: str) -> Dict[str, Any]:
    options: List[Any] = [announcement_id]
    try:
        options.append(ObjectId(announcement_id))
    except InvalidId:
        pass

    if len(options) == 1:
        return {"_id": announcement_id}
    return {"_id": {"$in": options}}


def map_announcement(document: Dict[str, Any]) -> Dict[str, Any]:
    starts_at = document.get("starts_at")
    expires_at = document.get("expires_at")

    return {
        "id": str(document["_id"]),
        "message": document["message"],
        "starts_at": starts_at.isoformat() if starts_at else None,
        "expires_at": expires_at.isoformat() if expires_at else None,
        "created_at": document["created_at"].isoformat() if document.get("created_at") else None,
        "updated_at": document["updated_at"].isoformat() if document.get("updated_at") else None,
    }


@router.get("", response_model=List[Dict[str, Any]])
def get_active_announcements() -> List[Dict[str, Any]]:
    now = datetime.now(timezone.utc)
    query = {
        "expires_at": {"$gte": now},
        "$or": [
            {"starts_at": None},
            {"starts_at": {"$exists": False}},
            {"starts_at": {"$lte": now}},
        ]
    }

    documents = announcements_collection.find(query).sort("expires_at", 1)
    return [map_announcement(doc) for doc in documents]


@router.get("/manage", response_model=List[Dict[str, Any]])
def get_all_announcements(username: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    verify_signed_in_user(username)

    documents = announcements_collection.find({}).sort("created_at", -1)
    return [map_announcement(doc) for doc in documents]


@router.post("", response_model=Dict[str, Any])
def create_announcement(payload: AnnouncementPayload, username: Optional[str] = Query(None)) -> Dict[str, Any]:
    verify_signed_in_user(username)

    cleaned_message = payload.message.strip()
    if not cleaned_message:
        raise HTTPException(status_code=400, detail="message is required")

    starts_at = parse_iso_datetime(payload.starts_at, "starts_at")
    expires_at = parse_iso_datetime(payload.expires_at, "expires_at")

    if expires_at is None:
        raise HTTPException(status_code=400, detail="expires_at is required")

    if starts_at and starts_at >= expires_at:
        raise HTTPException(status_code=400, detail="starts_at must be earlier than expires_at")

    now = datetime.now(timezone.utc)
    new_id = str(uuid.uuid4())
    result = announcements_collection.insert_one({
        "_id": new_id,
        "message": cleaned_message,
        "starts_at": starts_at,
        "expires_at": expires_at,
        "created_at": now,
        "updated_at": now,
    })

    created = announcements_collection.find_one({"_id": result.inserted_id})
    return map_announcement(created)


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    payload: AnnouncementPayload,
    username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    verify_signed_in_user(username)

    cleaned_message = payload.message.strip()
    if not cleaned_message:
        raise HTTPException(status_code=400, detail="message is required")

    starts_at = parse_iso_datetime(payload.starts_at, "starts_at")
    expires_at = parse_iso_datetime(payload.expires_at, "expires_at")

    if expires_at is None:
        raise HTTPException(status_code=400, detail="expires_at is required")

    if starts_at and starts_at >= expires_at:
        raise HTTPException(status_code=400, detail="starts_at must be earlier than expires_at")

    updated = announcements_collection.find_one_and_update(
        build_announcement_id_query(announcement_id),
        {
            "$set": {
                "message": cleaned_message,
                "starts_at": starts_at,
                "expires_at": expires_at,
                "updated_at": datetime.now(timezone.utc),
            }
        },
        return_document=ReturnDocument.AFTER,
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return map_announcement(updated)


@router.delete("/{announcement_id}", response_model=Dict[str, str])
def delete_announcement(announcement_id: str, username: Optional[str] = Query(None)) -> Dict[str, str]:
    verify_signed_in_user(username)

    result = announcements_collection.delete_one(build_announcement_id_query(announcement_id))
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Announcement deleted"}
