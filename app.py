from flask import Flask, request, jsonify # type: ignore
from flask_cors import CORS # type: ignore
from flask_migrate import Migrate # type: ignore
from models import db, ConsultationRequest
from config import config
from marshmallow import Schema, fields, ValidationError, validates # type: ignore
from dotenv import load_dotenv # type: ignore
import os
import logging
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConsultationSchema(Schema):
    """Marshmallow schema for consultation validation"""
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    email = fields.Email(required=True)
    phone = fields.Str(required=True)
    message = fields.Str(required=False, allow_none=True)
    status = fields.Str(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    @validates("phone")
    def validate_phone(self, value):
        """Validate phone number has at least 10 digits"""
        digits = "".join(filter(str.isdigit, value))
        if len(digits) < 10:
            raise ValidationError("Invalid phone number (must have at least 10 digits)")

    @validates("name")
    def validate_name(self, value):
        """Validate name is not empty"""
        if not value or not value.strip():
            raise ValidationError("Name cannot be empty")


def create_app(config_name=None):
    """Application factory"""
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, resources={
        r"/*": {
            "origins": ["*"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    Migrate(app, db)
    
    # Create all database tables
    with app.app_context():
        os.makedirs(app.instance_path, exist_ok=True)
        db.create_all()
    
    # Initialize schema
    consultation_schema = ConsultationSchema()
    consultations_schema = ConsultationSchema(many=True)
    
    # Routes
    @app.route("/", methods=["GET"])
    def home():
        """Home endpoint"""
        return jsonify({
            "message": "Credit Deletion Backend API",
            "version": "1.0",
            "status": "running"
        }), 200
    
    @app.route("/health", methods=["GET"])
    def health_check():
        """Health check endpoint"""
        try:
            db.session.execute("SELECT 1")
            db_status = "healthy"
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
            logger.error(f"Database health check failed: {e}")
        
        return jsonify({
            "status": "healthy" if db_status == "healthy" else "unhealthy",
            "database": db_status,
            "timestamp": datetime.now().isoformat(),
        }), 200 if db_status == "healthy" else 503
    
    @app.route("/consultation", methods=["POST"])
    def create_consultation():
        """Create a new consultation request"""
        try:
            payload = request.get_json(force=True)
            data = consultation_schema.load(payload)
        except ValidationError as err:
            return jsonify({
                "success": False,
                "errors": err.messages
            }), 400
        except Exception as e:
            logger.error(f"Invalid JSON: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Invalid JSON"
            }), 400
        
        try:
            consultation = ConsultationRequest(
                name=data["name"],
                email=data["email"],
                phone=data["phone"],
                message=data.get("message", ""),
                status="pending"
            )
            db.session.add(consultation)
            db.session.commit()
            
            logger.info(f"New consultation created: {consultation.id}")
            
            return jsonify({
                "success": True,
                "message": "Consultation request saved successfully",
                "data": consultation.to_dict()
            }), 201
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating consultation: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error creating consultation request"
            }), 500
    
    @app.route("/consultation", methods=["GET"])
    def list_consultations():
        """Get all consultation requests"""
        try:
            page = request.args.get("page", 1, type=int)
            per_page = request.args.get("per_page", 20, type=int)
            status_filter = request.args.get("status", None, type=str)
            
            query = ConsultationRequest.query.order_by(
                ConsultationRequest.created_at.desc()
            )
            
            if status_filter:
                query = query.filter_by(status=status_filter)
            
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            consultations = pagination.items
            
            return jsonify({
                "success": True,
                "data": consultations_schema.dump(consultations),
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": pagination.total,
                    "pages": pagination.pages
                }
            }), 200
        
        except Exception as e:
            logger.error(f"Error fetching consultations: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error fetching consultations"
            }), 500
    
    @app.route("/consultation/<int:consultation_id>", methods=["GET"])
    def get_consultation(consultation_id):
        """Get a specific consultation by ID"""
        try:
            consultation = ConsultationRequest.query.get(consultation_id)
            if not consultation:
                return jsonify({
                    "success": False,
                    "message": "Consultation not found"
                }), 404
            
            return jsonify({
                "success": True,
                "data": consultation.to_dict()
            }), 200
        
        except Exception as e:
            logger.error(f"Error fetching consultation {consultation_id}: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error fetching consultation"
            }), 500
    
    @app.route("/consultation/<int:consultation_id>", methods=["PUT"])
    def update_consultation(consultation_id):
        """Update a consultation request"""
        try:
            consultation = ConsultationRequest.query.get(consultation_id)
            if not consultation:
                return jsonify({
                    "success": False,
                    "message": "Consultation not found"
                }), 404
            
            payload = request.get_json()
            
            # Update status if provided
            if "status" in payload:
                allowed_statuses = ["pending", "in_review", "completed"]
                if payload["status"] not in allowed_statuses:
                    return jsonify({
                        "success": False,
                        "message": f"Invalid status. Must be one of: {', '.join(allowed_statuses)}"
                    }), 400
                consultation.status = payload["status"]
            
            # Update message if provided
            if "message" in payload:
                consultation.message = payload["message"]
            
            db.session.commit()
            
            logger.info(f"Consultation {consultation_id} updated")
            
            return jsonify({
                "success": True,
                "message": "Consultation updated successfully",
                "data": consultation.to_dict()
            }), 200
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating consultation {consultation_id}: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error updating consultation"
            }), 500
    
    @app.route("/consultation/<int:consultation_id>", methods=["DELETE"])
    def delete_consultation(consultation_id):
        """Delete a consultation request"""
        try:
            consultation = ConsultationRequest.query.get(consultation_id)
            if not consultation:
                return jsonify({
                    "success": False,
                    "message": "Consultation not found"
                }), 404
            
            db.session.delete(consultation)
            db.session.commit()
            
            logger.info(f"Consultation {consultation_id} deleted")
            
            return jsonify({
                "success": True,
                "message": "Consultation deleted successfully"
            }), 200
        
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting consultation {consultation_id}: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error deleting consultation"
            }), 500
    
    @app.route("/consultation/stats", methods=["GET"])
    def consultation_stats():
        """Get consultation statistics"""
        try:
            total = ConsultationRequest.query.count()
            pending = ConsultationRequest.query.filter_by(status="pending").count()
            in_review = ConsultationRequest.query.filter_by(status="in_review").count()
            completed = ConsultationRequest.query.filter_by(status="completed").count()
            
            return jsonify({
                "success": True,
                "data": {
                    "total": total,
                    "pending": pending,
                    "in_review": in_review,
                    "completed": completed
                }
            }), 200
        
        except Exception as e:
            logger.error(f"Error fetching stats: {str(e)}")
            return jsonify({
                "success": False,
                "message": "Error fetching statistics"
            }), 500
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "message": "Endpoint not found"
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {str(error)}")
        return jsonify({
            "success": False,
            "message": "Internal server error"
        }), 500
    
    return app

app = create_app()
if __name__ == "__main__":
    app = create_app()
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.getenv("FLASK_ENV", "development") == "development")
