"""
Events routes for SmartLife Organizer
Gestione completa eventi: CRUD, filtri, ricerca, paginazione
"""

from flask import Blueprint, request, jsonify
from modules.utils.auth import require_auth
from modules.utils.database import db, create_response, validate_required_fields, serialize_datetime
import logging
from datetime import datetime, timedelta

# Create blueprint
events_bp = Blueprint('events', __name__, url_prefix='/api/events')

# Configure logging
logger = logging.getLogger(__name__)


@events_bp.route('', methods=['GET'])
@require_auth
def get_events(current_user):
    """
    Get all events for current user with filters
    Query params: category_id, start_date, end_date, search, page, per_page
    """
    try:
        # Get query parameters
        category_id = request.args.get('category_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        search = request.args.get('search', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # Build query
        query = """
            SELECT 
                e.*,
                c.name as category_name,
                c.color as category_color,
                c.icon as category_icon
            FROM events e
            LEFT JOIN categories c ON e.category_id = c.id
            WHERE e.user_id = %s AND e.deleted_at IS NULL
        """
        params = [current_user['id']]
        
        # Apply filters
        if category_id:
            query += " AND e.category_id = %s"
            params.append(category_id)
        
        if start_date:
            query += " AND e.start_time >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND e.end_time <= %s"
            params.append(end_date)
        
        if search:
            query += " AND (e.title LIKE %s OR e.description LIKE %s OR e.location LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        
        query += " ORDER BY e.start_time DESC"
        
        # Get total count
        count_query = query.replace('SELECT e.*, c.name as category_name, c.color as category_color, c.icon as category_icon', 'SELECT COUNT(*)')
        total = db.execute_query(count_query, params, fetch_one=True)['COUNT(*)']
        
        # Apply pagination
        offset = (page - 1) * per_page
        query += " LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        
        # Execute query
        events = db.execute_query(query, params)
        
        # Serialize datetime fields
        for event in events:
            event['start_time'] = serialize_datetime(event['start_time'])
            event['end_time'] = serialize_datetime(event['end_time'])
            event['created_at'] = serialize_datetime(event['created_at'])
            event['updated_at'] = serialize_datetime(event['updated_at'])
        
        return jsonify(create_response(
            data={
                'events': events,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'pages': (total + per_page - 1) // per_page
                }
            },
            message=f"Found {len(events)} events"
        ))
        
    except Exception as e:
        logger.error(f"Error getting events: {str(e)}")
        return jsonify(create_response(
            error="Failed to get events",
            status_code=500
        ))


@events_bp.route('/today', methods=['GET'])
@require_auth
def get_today_events(current_user):
    """Get events for today"""
    try:
        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)
        
        query = """
            SELECT 
                e.*,
                c.name as category_name,
                c.color as category_color,
                c.icon as category_icon
            FROM events e
            LEFT JOIN categories c ON e.category_id = c.id
            WHERE e.user_id = %s 
            AND e.deleted_at IS NULL
            AND DATE(e.start_time) = %s
            ORDER BY e.start_time ASC
        """
        
        events = db.execute_query(query, [current_user['id'], today])
        
        # Serialize datetime fields
        for event in events:
            event['start_time'] = serialize_datetime(event['start_time'])
            event['end_time'] = serialize_datetime(event['end_time'])
            event['created_at'] = serialize_datetime(event['created_at'])
            event['updated_at'] = serialize_datetime(event['updated_at'])
        
        return jsonify(create_response(
            data={'events': events, 'count': len(events)},
            message=f"Found {len(events)} events for today"
        ))
        
    except Exception as e:
        logger.error(f"Error getting today events: {str(e)}")
        return jsonify(create_response(
            error="Failed to get today's events",
            status_code=500
        ))


@events_bp.route('/upcoming', methods=['GET'])
@require_auth
def get_upcoming_events(current_user):
    """Get upcoming events (next 7 days)"""
    try:
        today = datetime.now()
        next_week = today + timedelta(days=7)
        
        query = """
            SELECT 
                e.*,
                c.name as category_name,
                c.color as category_color,
                c.icon as category_icon
            FROM events e
            LEFT JOIN categories c ON e.category_id = c.id
            WHERE e.user_id = %s 
            AND e.deleted_at IS NULL
            AND e.start_time BETWEEN %s AND %s
            ORDER BY e.start_time ASC
            LIMIT 10
        """
        
        events = db.execute_query(query, [current_user['id'], today, next_week])
        
        # Serialize datetime fields
        for event in events:
            event['start_time'] = serialize_datetime(event['start_time'])
            event['end_time'] = serialize_datetime(event['end_time'])
            event['created_at'] = serialize_datetime(event['created_at'])
            event['updated_at'] = serialize_datetime(event['updated_at'])
        
        return jsonify(create_response(
            data={'events': events, 'count': len(events)},
            message=f"Found {len(events)} upcoming events"
        ))
        
    except Exception as e:
        logger.error(f"Error getting upcoming events: {str(e)}")
        return jsonify(create_response(
            error="Failed to get upcoming events",
            status_code=500
        ))


@events_bp.route('/<event_id>', methods=['GET'])
@require_auth
def get_event(current_user, event_id):
    """Get single event by ID"""
    try:
        query = """
            SELECT 
                e.*,
                c.name as category_name,
                c.color as category_color,
                c.icon as category_icon
            FROM events e
            LEFT JOIN categories c ON e.category_id = c.id
            WHERE e.id = %s AND e.user_id = %s AND e.deleted_at IS NULL
        """
        
        event = db.execute_query(query, [event_id, current_user['id']], fetch_one=True)
        
        if not event:
            return jsonify(create_response(
                error="Event not found",
                status_code=404
            ))
        
        # Serialize datetime fields
        event['start_time'] = serialize_datetime(event['start_time'])
        event['end_time'] = serialize_datetime(event['end_time'])
        event['created_at'] = serialize_datetime(event['created_at'])
        event['updated_at'] = serialize_datetime(event['updated_at'])
        
        return jsonify(create_response(
            data=event,
            message="Event retrieved successfully"
        ))
        
    except Exception as e:
        logger.error(f"Error getting event: {str(e)}")
        return jsonify(create_response(
            error="Failed to get event",
            status_code=500
        ))


@events_bp.route('', methods=['POST'])
@require_auth
def create_event(current_user):
    """Create new event"""
    try:
        data = request.get_json()
        
        # Validate required fields
        validate_required_fields(data, ['title', 'start_time', 'end_time'])
        
        title = data['title'].strip()
        description = data.get('description', '').strip()
        start_time = data['start_time']
        end_time = data['end_time']
        location = data.get('location', '').strip()
        category_id = data.get('category_id')
        is_all_day = data.get('is_all_day', False)
        recurrence_rule = data.get('recurrence_rule')
        reminder_minutes = data.get('reminder_minutes')
        color = data.get('color', '#3B82F6')
        
        # Validate dates
        try:
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            if end_dt <= start_dt:
                return jsonify(create_response(
                    error="End time must be after start time",
                    status_code=400
                ))
        except ValueError:
            return jsonify(create_response(
                error="Invalid date format. Use ISO 8601 format",
                status_code=400
            ))
        
        # Validate category if provided
        if category_id:
            category = db.execute_query(
                "SELECT id FROM categories WHERE id = %s AND user_id = %s",
                [category_id, current_user['id']],
                fetch_one=True
            )
            if not category:
                return jsonify(create_response(
                    error="Category not found",
                    status_code=404
                ))
        
        # Insert event
        query = """
            INSERT INTO events (
                user_id, title, description, start_time, end_time,
                location, category_id, is_all_day, recurrence_rule,
                reminder_minutes, color
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        event_id = db.execute_query(
            query,
            [
                current_user['id'], title, description, start_time, end_time,
                location, category_id, is_all_day, recurrence_rule,
                reminder_minutes, color
            ],
            commit=True
        )
        
        # Get created event
        created_event = db.execute_query(
            """
            SELECT 
                e.*,
                c.name as category_name,
                c.color as category_color,
                c.icon as category_icon
            FROM events e
            LEFT JOIN categories c ON e.category_id = c.id
            WHERE e.id = %s
            """,
            [event_id],
            fetch_one=True
        )
        
        # Serialize datetime
        created_event['start_time'] = serialize_datetime(created_event['start_time'])
        created_event['end_time'] = serialize_datetime(created_event['end_time'])
        created_event['created_at'] = serialize_datetime(created_event['created_at'])
        created_event['updated_at'] = serialize_datetime(created_event['updated_at'])
        
        logger.info(f"Event created: {event_id} by user {current_user['id']}")
        
        return jsonify(create_response(
            data=created_event,
            message="Event created successfully",
            status_code=201
        ))
        
    except Exception as e:
        logger.error(f"Error creating event: {str(e)}")
        return jsonify(create_response(
            error="Failed to create event",
            status_code=500
        ))


@events_bp.route('/<event_id>', methods=['PUT'])
@require_auth
def update_event(current_user, event_id):
    """Update existing event"""
    try:
        # Check if event exists and belongs to user
        existing = db.execute_query(
            "SELECT id FROM events WHERE id = %s AND user_id = %s AND deleted_at IS NULL",
            [event_id, current_user['id']],
            fetch_one=True
        )
        
        if not existing:
            return jsonify(create_response(
                error="Event not found",
                status_code=404
            ))
        
        data = request.get_json()
        
        # Build update query dynamically
        update_fields = []
        params = []
        
        if 'title' in data:
            update_fields.append("title = %s")
            params.append(data['title'].strip())
        
        if 'description' in data:
            update_fields.append("description = %s")
            params.append(data['description'].strip())
        
        if 'start_time' in data:
            update_fields.append("start_time = %s")
            params.append(data['start_time'])
        
        if 'end_time' in data:
            update_fields.append("end_time = %s")
            params.append(data['end_time'])
        
        if 'location' in data:
            update_fields.append("location = %s")
            params.append(data['location'].strip())
        
        if 'category_id' in data:
            # Validate category
            if data['category_id']:
                category = db.execute_query(
                    "SELECT id FROM categories WHERE id = %s AND user_id = %s",
                    [data['category_id'], current_user['id']],
                    fetch_one=True
                )
                if not category:
                    return jsonify(create_response(
                        error="Category not found",
                        status_code=404
                    ))
            update_fields.append("category_id = %s")
            params.append(data['category_id'])
        
        if 'is_all_day' in data:
            update_fields.append("is_all_day = %s")
            params.append(data['is_all_day'])
        
        if 'recurrence_rule' in data:
            update_fields.append("recurrence_rule = %s")
            params.append(data['recurrence_rule'])
        
        if 'reminder_minutes' in data:
            update_fields.append("reminder_minutes = %s")
            params.append(data['reminder_minutes'])
        
        if 'color' in data:
            update_fields.append("color = %s")
            params.append(data['color'])
        
        if not update_fields:
            return jsonify(create_response(
                error="No fields to update",
                status_code=400
            ))
        
        # Add updated_at
        update_fields.append("updated_at = NOW()")
        
        # Execute update
        query = f"UPDATE events SET {', '.join(update_fields)} WHERE id = %s"
        params.append(event_id)
        
        db.execute_query(query, params, commit=True)
        
        # Get updated event
        updated_event = db.execute_query(
            """
            SELECT 
                e.*,
                c.name as category_name,
                c.color as category_color,
                c.icon as category_icon
            FROM events e
            LEFT JOIN categories c ON e.category_id = c.id
            WHERE e.id = %s
            """,
            [event_id],
            fetch_one=True
        )
        
        # Serialize datetime
        updated_event['start_time'] = serialize_datetime(updated_event['start_time'])
        updated_event['end_time'] = serialize_datetime(updated_event['end_time'])
        updated_event['created_at'] = serialize_datetime(updated_event['created_at'])
        updated_event['updated_at'] = serialize_datetime(updated_event['updated_at'])
        
        logger.info(f"Event updated: {event_id} by user {current_user['id']}")
        
        return jsonify(create_response(
            data=updated_event,
            message="Event updated successfully"
        ))
        
    except Exception as e:
        logger.error(f"Error updating event: {str(e)}")
        return jsonify(create_response(
            error="Failed to update event",
            status_code=500
        ))


@events_bp.route('/<event_id>', methods=['DELETE'])
@require_auth
def delete_event(current_user, event_id):
    """Delete event (soft delete)"""
    try:
        # Check if event exists and belongs to user
        existing = db.execute_query(
            "SELECT id FROM events WHERE id = %s AND user_id = %s AND deleted_at IS NULL",
            [event_id, current_user['id']],
            fetch_one=True
        )
        
        if not existing:
            return jsonify(create_response(
                error="Event not found",
                status_code=404
            ))
        
        # Soft delete
        db.execute_query(
            "UPDATE events SET deleted_at = NOW() WHERE id = %s",
            [event_id],
            commit=True
        )
        
        logger.info(f"Event deleted: {event_id} by user {current_user['id']}")
        
        return jsonify(create_response(
            message="Event deleted successfully"
        ))
        
    except Exception as e:
        logger.error(f"Error deleting event: {str(e)}")
        return jsonify(create_response(
            error="Failed to delete event",
            status_code=500
        ))
