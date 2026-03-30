from flask_sqlalchemy import SQLAlchemy # type: ignore
from datetime import datetime

db = SQLAlchemy()

class ConsultationRequest(db.Model):
    """Model for storing consultation requests"""
    __tablename__ = "consultation_requests"
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(160), nullable=False, index=True)
    email = db.Column(db.String(160), nullable=False, index=True)
    phone = db.Column(db.String(30), nullable=False)
    message = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default="pending", nullable=False)  # pending, in_review, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "message": self.message,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<ConsultationRequest {self.id}: {self.name}>"
