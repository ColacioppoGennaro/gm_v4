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
            query += " AND e.start_datetime >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND e.end_datetime <= %s"
            params.append(end_date)
        
        if search:
            query += " AND (e.title LIKE %s OR e.description LIKE %s OR e.location LIKE %s)"
            search_term = f"%{search}%"
            params.extend([search_term, search_term, search_term])
        
        query += " ORDER BY e.start_datetime DESC"
        
        # Get total count
        count_query = query.replace('SELECT e.*, c.name as category_name, c.color as category_color, c.icon as category_icon', 'SELECT COUNT(*) as total')
        count_result = db.execute_query(count_query, params, fetch_one=True)
        total = count_result['total'] if count_result and 'total' in count_result else 0
        
        # Apply pagination
        offset = (page - 1) * per_page
        query += " LIMIT %s OFFSET %s"
        params.extend([per_page, offset])
        
        # Execute query
        events = db.execute_query(query, params)
        
        # Handle None or empty results
        if events is None:
            events = []
        
        # Serialize datetime fields
        for event in events:
            if event.get('start_datetime'):
                event['start_datetime'] = serialize_datetime(event['start_datetime'])
            if event.get('end_datetime'):
                event['end_datetime'] = serialize_datetime(event['end_datetime'])
            if event.get('created_at'):
                event['created_at'] = serialize_datetime(event['created_at'])
            if event.get('updated_at'):
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
        import traceback
        logger.error(traceback.format_exc())
        return jsonify(create_response(
            error="Failed to get events",
            status_code=500
        )), 500


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
            AND DATE(e.start_datetime) = %s
            ORDER BY e.start_datetime ASC
        """
        
        events = db.execute_query(query, [current_user['id'], today])
        
        # Serialize datetime fields
        for event in events:
            event['start_datetime'] = serialize_datetime(event['start_datetime'])
            event['end_datetime'] = serialize_datetime(event['end_datetime'])
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
            AND e.start_datetime BETWEEN %s AND %s
            ORDER BY e.start_datetime ASC
            LIMIT 10
        """
        
        events = db.execute_query(query, [current_user['id'], today, next_week])
        
        # Serialize datetime fields
        for event in events:
            event['start_datetime'] = serialize_datetime(event['start_datetime'])
            event['end_datetime'] = serialize_datetime(event['end_datetime'])
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
        event['start_datetime'] = serialize_datetime(event['start_datetime'])
        event['end_datetime'] = serialize_datetime(event['end_datetime'])
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
        validate_required_fields(data, ['title', 'start_datetime', 'end_datetime'])
        
        title = data['title'].strip()
        description = data.get('description', '').strip()
        start_datetime = data['start_datetime']
        end_datetime = data['end_datetime']
        category_id = data.get('category_id')
        is_all_day = data.get('is_all_day', False)
        color = data.get('color', '#3B82F6')
        status = data.get('status', 'pending')
        amount = data.get('amount')
        
        # Validate dates
        try:
            start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
            
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
        
        # Generate UUID for the event
        from modules.utils.database import generate_uuid
        event_id = generate_uuid()
        
        # Insert event with explicit ID
        query = """
            INSERT INTO events (
                id, user_id, title, description, start_datetime, end_datetime,
                category_id, all_day, color, status, amount
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        db.execute_query(
            query,
            [
                event_id, current_user['id'], title, description, start_datetime, end_datetime,
                category_id, is_all_day, color, status, amount
            ],
            fetch_all=False
        )
        
        logger.info(f"Event inserted with ID: {event_id}")
        
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
        
        logger.info(f"Retrieved created event: {created_event}")
        
        if not created_event:
            raise Exception(f"Failed to retrieve created event with ID {event_id}")
        
        # Serialize datetime
        if created_event.get('start_datetime'):
            created_event['start_datetime'] = serialize_datetime(created_event['start_datetime'])
        if created_event.get('end_datetime'):
            created_event['end_datetime'] = serialize_datetime(created_event['end_datetime'])
        if created_event.get('created_at'):
            created_event['created_at'] = serialize_datetime(created_event['created_at'])
        if created_event.get('updated_at'):
            created_event['updated_at'] = serialize_datetime(created_event['updated_at'])
        
        logger.info(f"Event created: {event_id} by user {current_user['id']}")
        
        # Sync with Google Calendar if connected
        if current_user.get('google_calendar_connected'):
            try:
                from modules.services.google_calendar_service import GoogleCalendarService
                google_event_id = GoogleCalendarService.create_event(current_user['id'], {
                    'title': title,
                    'description': description,
                    'start_datetime': start_datetime,
                    'end_datetime': end_datetime,
                    'is_all_day': is_all_day
                })
                
                # Update event with Google Calendar ID
                db.execute_query(
                    "UPDATE events SET google_event_id = %s, last_synced_at = NOW() WHERE id = %s",
                    [google_event_id, event_id],
                    fetch_all=False
                )
                
                created_event['google_event_id'] = google_event_id
                logger.info(f"Event synced to Google Calendar: {google_event_id}")
            except Exception as e:
                logger.warning(f"Failed to sync event to Google Calendar: {str(e)}")
                # Don't fail the request if Google sync fails
        
        return jsonify(create_response(
            data=created_event,
            message="Event created successfully",
            status_code=201
        ))
        
    except Exception as e:
        logger.error(f"Error creating event: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify(create_response(
            error=f"Failed to create event: {str(e)}",
            status_code=500
        )), 500


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
        
        if 'start_datetime' in data:
            update_fields.append("start_datetime = %s")
            params.append(data['start_datetime'])
        
        if 'end_datetime' in data:
            update_fields.append("end_datetime = %s")
            params.append(data['end_datetime'])
        
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
            update_fields.append("all_day = %s")
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
        
        db.execute_query(query, params, fetch_all=False)
        
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
        updated_event['start_datetime'] = serialize_datetime(updated_event['start_datetime'])
        updated_event['end_datetime'] = serialize_datetime(updated_event['end_datetime'])
        updated_event['created_at'] = serialize_datetime(updated_event['created_at'])
        updated_event['updated_at'] = serialize_datetime(updated_event['updated_at'])
        
        logger.info(f"Event updated: {event_id} by user {current_user['id']}")
        
        # Sync with Google Calendar if connected
        if current_user.get('google_calendar_connected') and updated_event.get('google_event_id'):
            try:
                from modules.services.google_calendar_service import GoogleCalendarService
                GoogleCalendarService.update_event(
                    current_user['id'],
                    updated_event['google_event_id'],
                    data
                )
                
                # Update sync timestamp
                db.execute_query(
                    "UPDATE events SET last_synced_at = NOW() WHERE id = %s",
                    [event_id],
                    fetch_all=False
                )
                
                logger.info(f"Event synced to Google Calendar: {updated_event['google_event_id']}")
            except Exception as e:
                logger.warning(f"Failed to sync event to Google Calendar: {str(e)}")
        
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
            "SELECT id, google_event_id FROM events WHERE id = %s AND user_id = %s AND deleted_at IS NULL",
            [event_id, current_user['id']],
            fetch_one=True
        )
        
        if not existing:
            return jsonify(create_response(
                error="Event not found",
                status_code=404
            ))
        
        # Delete from Google Calendar if synced
        if current_user.get('google_calendar_connected') and existing.get('google_event_id'):
            try:
                from modules.services.google_calendar_service import GoogleCalendarService
                GoogleCalendarService.delete_event(current_user['id'], existing['google_event_id'])
                logger.info(f"Event deleted from Google Calendar: {existing['google_event_id']}")
            except Exception as e:
                logger.warning(f"Failed to delete event from Google Calendar: {str(e)}")
        
        # Soft delete
        db.execute_query(
            "UPDATE events SET deleted_at = NOW() WHERE id = %s",
            [event_id],
            fetch_all=False
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


# ================================
# CATEGORIES ENDPOINTS
# ================================

@events_bp.route('/categories', methods=['GET'])
@require_auth
def get_categories(current_user):
    """Get all categories for current user"""
    try:
        query = """
            SELECT 
                c.id,
                c.name,
                c.color,
                c.icon,
                c.is_default,
                c.display_order,
                COUNT(e.id) as event_count
            FROM categories c
            LEFT JOIN events e ON c.id = e.category_id AND e.user_id = %s
            WHERE c.user_id = %s
            GROUP BY c.id, c.name, c.color, c.icon, c.is_default, c.display_order
            ORDER BY c.display_order ASC, c.created_at ASC
        """
        
        categories = db.execute_query(query, [current_user['id'], current_user['id']], fetch_all=True)
        
        # Convert decimal/other types to JSON-serializable
        for cat in categories:
            cat['event_count'] = int(cat['event_count']) if cat['event_count'] else 0
            cat['is_default'] = bool(cat['is_default'])
        
        return jsonify(create_response(
            data={'categories': categories},
            message=f"Found {len(categories)} categories"
        ))
        
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        return jsonify(create_response(
            error="Failed to fetch categories",
            status_code=500
        ))


@events_bp.route('/categories', methods=['POST'])
@require_auth
def create_category(current_user):
    """Create a new category"""
    try:
        data = request.get_json()
        validate_required_fields(data, ['name', 'color', 'icon'])
        
        # Check if category name already exists for user
        existing = db.execute_query(
            "SELECT id FROM categories WHERE user_id = %s AND name = %s",
            [current_user['id'], data['name']],
            fetch_one=True
        )
        
        if existing:
            return jsonify(create_response(
                error="Category with this name already exists",
                status_code=409
            )), 409
        
        # Get max display order
        max_order = db.execute_query(
            "SELECT MAX(display_order) as max_order FROM categories WHERE user_id = %s",
            [current_user['id']],
            fetch_one=True
        )
        
        next_order = (max_order['max_order'] if max_order and max_order['max_order'] else 0) + 1
        
        # Create category
        import uuid
        category_id = str(uuid.uuid4())
        
        db.execute_query(
            """INSERT INTO categories 
               (id, user_id, name, color, icon, is_default, display_order) 
               VALUES (%s, %s, %s, %s, %s, %s, %s)""",
            [category_id, current_user['id'], data['name'], data['color'], 
             data['icon'], False, next_order],
            fetch_all=False
        )
        
        # Return created category
        category = db.execute_query(
            "SELECT * FROM categories WHERE id = %s",
            [category_id],
            fetch_one=True
        )
        
        category['event_count'] = 0
        category['is_default'] = bool(category['is_default'])
        
        return jsonify(create_response(
            data={'category': category},
            message="Category created successfully",
            status_code=201
        )), 201
        
    except ValueError as e:
        return jsonify(create_response(
            error=str(e),
            status_code=400
        )), 400
    except Exception as e:
        logger.error(f"Error creating category: {str(e)}")
        return jsonify(create_response(
            error="Failed to create category",
            status_code=500
        ))


@events_bp.route('/categories/<category_id>', methods=['DELETE'])
@require_auth
def delete_category(current_user, category_id):
    """Delete a category (must be owned by user and not default)"""
    try:
        # Check if category exists and belongs to user
        category = db.execute_query(
            "SELECT * FROM categories WHERE id = %s AND user_id = %s",
            [category_id, current_user['id']],
            fetch_one=True
        )
        
        if not category:
            return jsonify(create_response(
                error="Category not found",
                status_code=404
            )), 404
        
        # Don't allow deleting default categories
        if category['is_default']:
            return jsonify(create_response(
                error="Cannot delete default categories",
                status_code=403
            )), 403
        
        # Delete category (events will have category_id set to NULL due to ON DELETE SET NULL)
        db.execute_query(
            "DELETE FROM categories WHERE id = %s",
            [category_id],
            fetch_all=False
        )
        
        return jsonify(create_response(
            message="Category deleted successfully"
        ))
        
    except Exception as e:
        logger.error(f"Error deleting category: {str(e)}")
        return jsonify(create_response(
            error="Failed to delete category",
            status_code=500
        ))


# ================================
# DOCUMENTS ENDPOINTS
# ================================

@events_bp.route('/documents', methods=['GET'])
@require_auth
def get_documents(current_user):
    """Get all documents for current user"""
    try:
        query = """
            SELECT 
                d.id,
                d.filename,
                d.file_path,
                d.file_type,
                d.file_size,
                d.ai_summary,
                d.extracted_amount,
                d.extracted_date,
                d.extracted_reason,
                d.upload_date,
                d.event_id,
                e.title as event_title
            FROM documents d
            LEFT JOIN events e ON d.event_id = e.id
            WHERE d.user_id = %s
            ORDER BY d.upload_date DESC
        """
        
        documents = db.execute_query(query, [current_user['id']], fetch_all=True)
        
        # Serialize dates and amounts
        for doc in documents:
            doc['upload_date'] = serialize_datetime(doc['upload_date'])
            doc['extracted_date'] = serialize_datetime(doc['extracted_date']) if doc.get('extracted_date') else None
            doc['extracted_amount'] = float(doc['extracted_amount']) if doc.get('extracted_amount') else None
            doc['file_size'] = int(doc['file_size']) if doc.get('file_size') else 0
        
        return jsonify(create_response(
            data={'documents': documents},
            message=f"Found {len(documents)} documents"
        ))
        
    except Exception as e:
        logger.error(f"Error fetching documents: {str(e)}")
        return jsonify(create_response(
            error="Failed to fetch documents",
            status_code=500
        ))
