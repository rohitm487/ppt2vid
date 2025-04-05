from sqlalchemy.orm import Session
from ppt2vid.database import SessionLocal
from ppt2vid.models.user import User, UserRole, SubscriptionTier

def create_superuser(email: str):
    db = SessionLocal()
    try:
        # Check if user already exists
        user = db.query(User).filter(User.email == email).first()
        if user:
            # Update existing user to superuser
            user.role = UserRole.SUPERUSER
            user.subscription_tier = SubscriptionTier.PREMIUM
            print(f"Updated existing user {email} to superuser")
        else:
            # Create new superuser
            user = User(
                email=email,
                role=UserRole.SUPERUSER,
                subscription_tier=SubscriptionTier.PREMIUM,
                name="Super Admin"
            )
            db.add(user)
            print(f"Created new superuser {email}")
        
        db.commit()
    except Exception as e:
        print(f"Error creating superuser: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python create_superuser.py <email>")
        sys.exit(1)
    
    email = sys.argv[1]
    create_superuser(email) 