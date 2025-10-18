"""
Database connection and utility functions for SmartLife Organizer
"""

import pymysql
import json
import logging
from datetime import datetime, date
from decimal import Decimal
from config import Config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and operations"""
    
    def __init__(self):
        self.connection_config = {
            'host': Config.DB_HOST,
            'user': Config.DB_USER,
            'password': Config.DB_PASS,
            'database': Config.DB_NAME,
            'charset': 'utf8mb4',
            'autocommit': True,
            'cursorclass': pymysql.cursors.DictCursor
        }
    
    def get_connection(self):
        """Get a new database connection"""
        try:
            connection = pymysql.connect(**self.connection_config)
            return connection
        except Exception as e:
            logger.error(f"Database connection failed: {str(e)}")
            raise
    
    def execute_query(self, query, params=None, fetch_one=False, fetch_all=True):
        """Execute a query and return results"""
        connection = None
        try:
            connection = self.get_connection()
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                
                if fetch_one:
                    result = cursor.fetchone()
                elif fetch_all:
                    result = cursor.fetchall()
                else:
                    result = cursor.rowcount
                
                connection.commit()
                return result
                
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Query execution failed: {str(e)}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            raise
        finally:
            if connection:
                connection.close()
    
    def insert_and_get_id(self, query, params=None):
        """Insert a record and return the inserted ID"""
        connection = None
        try:
            connection = self.get_connection()
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                # For UUID primary keys, we need to get the last inserted UUID
                cursor.execute("SELECT LAST_INSERT_ID() as id")
                result = cursor.fetchone()
                connection.commit()
                return result['id'] if result else None
                
        except Exception as e:
            if connection:
                connection.rollback()
            logger.error(f"Insert query failed: {str(e)}")
            raise
        finally:
            if connection:
                connection.close()

# Global database manager instance
db = DatabaseManager()

def serialize_datetime(obj):
    """JSON serializer for datetime objects"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    elif isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def generate_uuid():
    """Generate a UUID string (MySQL compatible)"""
    import uuid
    return str(uuid.uuid4())

def format_mysql_datetime(dt):
    """Format datetime for MySQL insertion"""
    if isinstance(dt, datetime):
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return dt

def parse_json_safe(json_str):
    """Safely parse JSON string"""
    if not json_str:
        return {}
    try:
        return json.loads(json_str) if isinstance(json_str, str) else json_str
    except (json.JSONDecodeError, TypeError):
        return {}

def create_response(data=None, message=None, status_code=200, error=None):
    """Create standardized API response"""
    response = {}
    
    if data is not None:
        response['data'] = data
    
    if message:
        response['message'] = message
    
    if error:
        response['error'] = error
        
    response['success'] = status_code < 400
    response['timestamp'] = datetime.utcnow().isoformat()
    
    # Return only the dict - Flask will handle status code via jsonify
    return response

def validate_required_fields(data, required_fields):
    """Validate that all required fields are present"""
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            missing_fields.append(field)
    
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    return True