from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime

from backend.app.models import Trip, User, TripMember
from backend.app.repositories.trip_repository import TripRepository
from backend.app.repositories.user_repository import UserRepository
from backend.app.repositories.activity_repository import ActivityRepository
from backend.app.schemas.trip import TripCreate, TripUpdate, TripInviteRequest

def send_trip_invitation_email(trip_name: str, host_name: str, guest_email: str, invite_uuid: str):
    from backend.app.config import settings
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    invite_link = f"http://localhost:8082/#/register?invite_token={invite_uuid}"
    subject = f"You've been invited to join the trip \"{trip_name}\" on Trip Memories!"
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e1e1e1; border-radius: 10px;">
                <h2 style="color: #1A73E8; text-align: center;">Trip Memories Platform</h2>
                <p>Hello,</p>
                <p><strong>{host_name}</strong> has invited you to collaborate and share your memories in the trip <strong>"{trip_name}"</strong>.</p>
                <p>Since you don't have an account yet, click the button below to register and join the trip immediately:</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{invite_link}" style="background-color: #1A73E8; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">Accept Invitation & Register</a>
                </div>
                <p style="font-size: 12px; color: #666;">If the button doesn't work, copy and paste this link into your browser:<br>
                <a href="{invite_link}">{invite_link}</a></p>
                <hr style="border: 0; border-top: 1px solid #e1e1e1; margin: 20px 0;">
                <p style="font-size: 11px; color: #999; text-align: center;">This is a private, self-hosted Trip Memories Platform installation.</p>
            </div>
        </body>
    </html>
    """

    if not settings.SMTP_HOST:
        print("\n" + "="*80)
        print("DEVELOPER MAIL BACKEND (Console Fallback)")
        print(f"To: {guest_email}")
        print(f"Subject: {subject}")
        print(f"Invite Link: {invite_link}")
        print("="*80 + "\n")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = guest_email

        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
                server.starttls()
                server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, guest_email, msg.as_string())
    except Exception as e:
        print(f"\n[WARNING] Failed to send email via SMTP ({str(e)}). Printing invitation to console:")
        print("="*80)
        print(f"To: {guest_email}")
        print(f"Subject: {subject}")
        print(f"Invite Link: {invite_link}")
        print("="*80 + "\n")


class TripService:
    @classmethod
    def create_trip(cls, db: Session, user: User, data: TripCreate) -> Trip:
        trip = Trip(
            trip_name=data.trip_name,
            description=data.description,
            cover_image=data.cover_image,
            created_by=user.id
        )
        created_trip = TripRepository.create(db, trip)
        
        # Creator is automatically added as owner member
        TripRepository.add_member(db, created_trip.id, user.id, role="owner")
        
        # Log activity
        ActivityRepository.create_log(
            db=db, 
            user_id=user.id, 
            trip_id=created_trip.id, 
            action="created_trip",
            target_id=created_trip.uuid
        )
        return created_trip

    @classmethod
    def get_trip_details(cls, db: Session, user: User, trip_uuid: str):
        trip = TripRepository.get_by_uuid(db, trip_uuid)
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
            
        # Verify user is a member of the trip
        member = TripRepository.get_member(db, trip.id, user.id)
        if not member:
            raise HTTPException(status_code=403, detail="Not authorized to view this trip")
            
        # Get active members
        members_list = list(trip.members)
        
        # Get pending invites
        from backend.app.models import TripInvite
        invites = db.query(TripInvite).filter(
            TripInvite.trip_id == trip.id,
            TripInvite.used == False
        ).all()
        
        for invite in invites:
            mock_member = {
                "id": -invite.id,  # Negative ID to distinguish from actual database members
                "trip_id": trip.id,
                "user_id": 0,
                "role": invite.role,
                "joined_at": invite.created_at,
                "user": {
                    "id": 0,
                    "uuid": invite.uuid,
                    "name": "Pending Invite",
                    "email": invite.email,
                    "created_at": invite.created_at
                }
            }
            members_list.append(mock_member)
            
        return {
            "id": trip.id,
            "uuid": trip.uuid,
            "trip_name": trip.trip_name,
            "description": trip.description,
            "cover_image": trip.cover_image,
            "created_by": trip.created_by,
            "created_at": trip.created_at,
            "members": members_list
        }

    @classmethod
    def get_user_trips(cls, db: Session, user: User) -> List[Trip]:
        return TripRepository.get_user_trips(db, user.id)

    @classmethod
    def update_trip(cls, db: Session, user: User, trip_uuid: str, data: TripUpdate) -> Trip:
        trip = TripRepository.get_by_uuid(db, trip_uuid)
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
            
        # Verify user is the owner
        member = TripRepository.get_member(db, trip.id, user.id)
        if not member or member.role != "owner":
            raise HTTPException(status_code=403, detail="Only trip owners can update the trip")
            
        if data.trip_name is not None:
            trip.trip_name = data.trip_name
        if data.description is not None:
            trip.description = data.description
        if data.cover_image is not None:
            trip.cover_image = data.cover_image
            
        updated_trip = TripRepository.update(db, trip)
        
        # Log activity
        ActivityRepository.create_log(
            db=db, 
            user_id=user.id, 
            trip_id=trip.id, 
            action="updated_trip",
            target_id=trip.uuid
        )
        return updated_trip

    @classmethod
    def delete_trip(cls, db: Session, user: User, trip_uuid: str) -> None:
        trip = TripRepository.get_by_uuid(db, trip_uuid)
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
            
        # Verify user is the owner
        member = TripRepository.get_member(db, trip.id, user.id)
        if not member or member.role != "owner":
            raise HTTPException(status_code=403, detail="Only trip owners can delete the trip")
            
        # Delete from repository
        TripRepository.delete(db, trip)
        
        # Log activity (without trip ID since trip is deleted)
        ActivityRepository.create_log(
            db=db, 
            user_id=user.id, 
            trip_id=None, 
            action="deleted_trip",
            target_id=trip_uuid
        )

    @classmethod
    def invite_member(cls, db: Session, user: User, trip_uuid: str, data: TripInviteRequest):
        trip = TripRepository.get_by_uuid(db, trip_uuid)
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
            
        # Verify current user is owner or co-owner
        member = TripRepository.get_member(db, trip.id, user.id)
        if not member or member.role not in ["owner", "co-owner"]:
            raise HTTPException(status_code=403, detail="Only trip owners or co-owners can invite members")
            
        # Co-owners can only invite members. Only the primary owner can invite other co-owners.
        if member.role == "co-owner" and data.role != "member":
            raise HTTPException(status_code=403, detail="Co-owners can only invite regular members, not other co-owners")
            
        # Find target user by email
        target_user = UserRepository.get_by_email(db, data.email)
        if not target_user:
            # Guest invite flow
            from backend.app.models import TripInvite
            
            # Check if active invite already exists
            existing_invite = db.query(TripInvite).filter(
                TripInvite.trip_id == trip.id,
                TripInvite.email == data.email,
                TripInvite.used == False
            ).first()
            
            if existing_invite:
                invite_token = existing_invite.uuid
                created_at = existing_invite.created_at
                invite_id = existing_invite.id
            else:
                new_invite = TripInvite(
                    trip_id=trip.id,
                    email=data.email,
                    role=data.role
                )
                db.add(new_invite)
                db.commit()
                db.refresh(new_invite)
                invite_token = new_invite.uuid
                created_at = new_invite.created_at
                invite_id = new_invite.id
                
            # Deliver email
            send_trip_invitation_email(trip.trip_name, user.name, data.email, invite_token)
            
            # Log activity
            ActivityRepository.create_log(
                db=db,
                user_id=user.id,
                trip_id=trip.id,
                action="invited_guest",
                target_id=invite_token
            )
            
            # Return mock member response
            return {
                "id": -invite_id,
                "trip_id": trip.id,
                "user_id": 0,
                "role": data.role,
                "joined_at": created_at,
                "user": {
                    "id": 0,
                    "uuid": invite_token,
                    "name": "Pending Invite",
                    "email": data.email,
                    "created_at": created_at
                }
            }
            
        # Check if already a member
        existing_member = TripRepository.get_member(db, trip.id, target_user.id)
        if existing_member:
            raise HTTPException(status_code=400, detail="User is already a member of this trip")
            
        # Add member
        new_member = TripRepository.add_member(db, trip.id, target_user.id, data.role)
        
        # Log activity
        ActivityRepository.create_log(
            db=db, 
            user_id=user.id, 
            trip_id=trip.id, 
            action="invited_member",
            target_id=target_user.uuid
        )
        return new_member

    @classmethod
    def join_trip(cls, db: Session, user: User, trip_uuid: str) -> TripMember:
        trip = TripRepository.get_by_uuid(db, trip_uuid)
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
            
        # Check if already a member
        existing_member = TripRepository.get_member(db, trip.id, user.id)
        if existing_member:
            raise HTTPException(status_code=400, detail="You are already a member of this trip")
            
        new_member = TripRepository.add_member(db, trip.id, user.id, role="member")
        
        # Log activity
        ActivityRepository.create_log(
            db=db, 
            user_id=user.id, 
            trip_id=trip.id, 
            action="joined_trip",
            target_id=trip.uuid
        )
        return new_member

    @classmethod
    def remove_member(cls, db: Session, user: User, trip_uuid: str, member_id: int) -> None:
        trip = TripRepository.get_by_uuid(db, trip_uuid)
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
            
        # Verify current user is owner or co-owner
        curr_member = TripRepository.get_member(db, trip.id, user.id)
        if not curr_member or curr_member.role not in ["owner", "co-owner"]:
            raise HTTPException(status_code=403, detail="Only trip owners or co-owners can remove members")
            
        if member_id < 0:
            # It's a pending invite!
            invite_id = -member_id
            from backend.app.models import TripInvite
            invite = db.query(TripInvite).filter(
                TripInvite.trip_id == trip.id,
                TripInvite.id == invite_id,
                TripInvite.used == False
            ).first()
            if not invite:
                raise HTTPException(status_code=404, detail="Invite not found in this trip")
                
            # Co-owners cannot remove co-owner invites
            if curr_member.role == "co-owner" and invite.role in ["owner", "co-owner"]:
                raise HTTPException(status_code=403, detail="Co-owners cannot remove co-owner invites")
                
            invite_uuid = invite.uuid
            db.delete(invite)
            db.commit()
            
            # Log activity
            ActivityRepository.create_log(
                db=db,
                user_id=user.id,
                trip_id=trip.id,
                action="removed_invite",
                target_id=invite_uuid
            )
            return

        # Find target member relationship
        target_member = db.query(TripMember).filter(
            TripMember.trip_id == trip.id,
            TripMember.id == member_id
        ).first()
        
        if not target_member:
            raise HTTPException(status_code=404, detail="Member not found in this trip")
            
        # Co-owners cannot remove the primary owner or other co-owners
        if curr_member.role == "co-owner" and target_member.role in ["owner", "co-owner"]:
            raise HTTPException(status_code=403, detail="Co-owners cannot remove the trip owner or other co-owners")
            
        # Prevent removing the primary owner
        if target_member.role == "owner":
            raise HTTPException(status_code=400, detail="Cannot remove the primary trip owner")
                
        target_user_uuid = target_member.user.uuid
        TripRepository.remove_member(db, target_member)
        
        # Log activity
        ActivityRepository.create_log(
            db=db, 
            user_id=user.id, 
            trip_id=trip.id, 
            action="removed_member",
            target_id=target_user_uuid
        )

    @classmethod
    def update_member_role(cls, db: Session, user: User, trip_uuid: str, member_id: int, role: str):
        trip = TripRepository.get_by_uuid(db, trip_uuid)
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found")
            
        # Verify current user is owner (only primary owner can change roles!)
        curr_member = TripRepository.get_member(db, trip.id, user.id)
        if not curr_member or curr_member.role != "owner":
            raise HTTPException(status_code=403, detail="Only trip owners can change member roles")
            
        if member_id < 0:
            # It's a pending invite!
            invite_id = -member_id
            from backend.app.models import TripInvite
            invite = db.query(TripInvite).filter(
                TripInvite.trip_id == trip.id,
                TripInvite.id == invite_id,
                TripInvite.used == False
            ).first()
            if not invite:
                raise HTTPException(status_code=404, detail="Pending invitation not found")
            invite.role = role
            db.commit()
            db.refresh(invite)
            
            # Log activity
            ActivityRepository.create_log(
                db=db,
                user_id=user.id,
                trip_id=trip.id,
                action="updated_invite_role",
                target_id=invite.uuid
            )
            
            # Return mock member response
            return {
                "id": -invite.id,
                "trip_id": trip.id,
                "user_id": 0,
                "role": invite.role,
                "joined_at": invite.created_at,
                "user": {
                    "id": 0,
                    "uuid": invite.uuid,
                    "name": "Pending Invite",
                    "email": invite.email,
                    "created_at": invite.created_at
                }
            }
            
        # Regular member
        target_member = db.query(TripMember).filter(
            TripMember.trip_id == trip.id,
            TripMember.id == member_id
        ).first()
        
        if not target_member:
            raise HTTPException(status_code=404, detail="Member not found in this trip")
            
        # Cannot change the primary owner's role
        if target_member.role == "owner":
            raise HTTPException(status_code=400, detail="Cannot change the role of the primary owner")
            
        target_member.role = role
        db.commit()
        db.refresh(target_member)
        
        # Log activity
        ActivityRepository.create_log(
            db=db,
            user_id=user.id,
            trip_id=trip.id,
            action="updated_member_role",
            target_id=target_member.user.uuid
        )
        return target_member

