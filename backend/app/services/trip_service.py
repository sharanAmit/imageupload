from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional
from datetime import datetime

from backend.app.models import Trip, User, TripMember
from backend.app.repositories.trip_repository import TripRepository
from backend.app.repositories.user_repository import UserRepository
from backend.app.repositories.activity_repository import ActivityRepository
from backend.app.schemas.trip import TripCreate, TripUpdate, TripInviteRequest

def send_trip_invitation_email(trip_name: str, host_name: str, guest_email: str, invite_uuid: str, account_exists: bool):
    from backend.app.config import settings
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    base_url = "http://localhost:8082"
    decline_link = f"{base_url}/#/invite/{invite_uuid}/decline"
    if account_exists:
        accept_link = f"{base_url}/#/invite/{invite_uuid}/accept"
        accept_label = "Accept Invitation"
        intro = "Click below to accept or decline:"
    else:
        accept_link = f"{base_url}/#/register?invite_token={invite_uuid}"
        accept_label = "Accept & Register"
        intro = "Since you don't have an account yet, accept by registering below, or decline if this wasn't meant for you:"

    subject = f"You've been invited to join the trip \"{trip_name}\" on Trip Memories!"

    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e1e1e1; border-radius: 10px;">
                <h2 style="color: #1A73E8; text-align: center;">Trip Memories Platform</h2>
                <p>Hello,</p>
                <p><strong>{host_name}</strong> has invited you to collaborate and share your memories in the trip <strong>"{trip_name}"</strong>.</p>
                <p>{intro}</p>
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{accept_link}" style="background-color: #1A73E8; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; margin: 0 8px;">{accept_label}</a>
                    <a href="{decline_link}" style="background-color: #f1f3f4; color: #333; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block; margin: 0 8px;">Decline</a>
                </div>
                <p style="font-size: 12px; color: #666;">If the buttons don't work, copy and paste these links into your browser:<br>
                Accept: <a href="{accept_link}">{accept_link}</a><br>
                Decline: <a href="{decline_link}">{decline_link}</a></p>
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
        print(f"Accept Link: {accept_link}")
        print(f"Decline Link: {decline_link}")
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
        print(f"Accept Link: {accept_link}")
        print(f"Decline Link: {decline_link}")
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
        
        # Get invites still awaiting a response, plus declined ones (so the owner can see & clear them)
        from backend.app.models import TripInvite
        invites = db.query(TripInvite).filter(
            TripInvite.trip_id == trip.id,
            TripInvite.status.in_(["pending", "declined"])
        ).all()

        for invite in invites:
            target_user = UserRepository.get_by_email(db, invite.email)
            members_list.append(cls._invite_to_member_dict(invite, target_user))
            
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
    def _invite_to_member_dict(cls, invite, target_user: Optional[User] = None) -> dict:
        return {
            "id": -invite.id,  # Negative ID to distinguish invites from actual membership rows
            "trip_id": invite.trip_id,
            "user_id": 0,
            "role": invite.role,
            "joined_at": invite.created_at,
            "status": invite.status,
            "user": {
                "id": 0,
                "uuid": invite.uuid,
                "name": target_user.name if target_user else "Pending Invite",
                "email": invite.email,
                "created_at": invite.created_at
            }
        }

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

        # Find target user by email (may or may not already have an account)
        target_user = UserRepository.get_by_email(db, data.email)
        if target_user:
            existing_member = TripRepository.get_member(db, trip.id, target_user.id)
            if existing_member:
                raise HTTPException(status_code=400, detail="User is already a member of this trip")

        # Every invite goes through a pending state until the invitee accepts or declines by email
        from backend.app.models import TripInvite

        existing_invite = db.query(TripInvite).filter(
            TripInvite.trip_id == trip.id,
            TripInvite.email == data.email,
            TripInvite.status == "pending"
        ).first()

        if existing_invite:
            invite = existing_invite
            invite.role = data.role
            db.commit()
            db.refresh(invite)
        else:
            invite = TripInvite(trip_id=trip.id, email=data.email, role=data.role)
            db.add(invite)
            db.commit()
            db.refresh(invite)

        # Deliver email
        send_trip_invitation_email(trip.trip_name, user.name, data.email, invite.uuid, account_exists=target_user is not None)

        # Log activity
        ActivityRepository.create_log(
            db=db,
            user_id=user.id,
            trip_id=trip.id,
            action="invited_member" if target_user else "invited_guest",
            target_id=(target_user.uuid if target_user else invite.uuid)
        )

        return cls._invite_to_member_dict(invite, target_user)

    @classmethod
    def accept_invite(cls, db: Session, token: str) -> dict:
        from backend.app.models import TripInvite
        invite = db.query(TripInvite).filter(
            TripInvite.uuid == token,
            TripInvite.status == "pending"
        ).first()
        if not invite:
            raise HTTPException(status_code=404, detail="This invitation is invalid, expired, or already responded to")

        target_user = UserRepository.get_by_email(db, invite.email)
        if not target_user:
            raise HTTPException(
                status_code=400,
                detail="No account exists yet for this email. Please register using the invite link to accept."
            )

        existing_member = TripRepository.get_member(db, invite.trip_id, target_user.id)
        if not existing_member:
            TripRepository.add_member(db, invite.trip_id, target_user.id, invite.role)
            ActivityRepository.create_log(
                db=db,
                user_id=target_user.id,
                trip_id=invite.trip_id,
                action="accepted_invite",
                target_id=invite.uuid
            )

        invite.status = "accepted"
        db.commit()

        trip = TripRepository.get_by_id(db, invite.trip_id)
        return {"trip_name": trip.trip_name if trip else None, "role": invite.role}

    @classmethod
    def decline_invite(cls, db: Session, token: str) -> dict:
        from backend.app.models import TripInvite
        invite = db.query(TripInvite).filter(
            TripInvite.uuid == token,
            TripInvite.status == "pending"
        ).first()
        if not invite:
            raise HTTPException(status_code=404, detail="This invitation is invalid, expired, or already responded to")

        invite.status = "declined"
        db.commit()

        trip = TripRepository.get_by_id(db, invite.trip_id)
        return {"trip_name": trip.trip_name if trip else None}

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
                TripInvite.status != "accepted"
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
                TripInvite.status == "pending"
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

            target_user = UserRepository.get_by_email(db, invite.email)
            return cls._invite_to_member_dict(invite, target_user)
            
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

