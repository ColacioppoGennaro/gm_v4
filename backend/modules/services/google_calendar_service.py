"""
Google Calendar Integration Service
Handles OAuth2 authentication and event synchronization
"""

import logging
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import Config
from modules.utils.database import db
import json

logger = logging.getLogger(__name__)


class GoogleCalendarService:
    """Service for Google Calendar integration"""
    
    SCOPES = ['https://www.googleapis.com/auth/calendar.events']
    
    @staticmethod
    def get_oauth_flow(state=None):
        """
        Create OAuth2 flow for Google Calendar
        
        Args:
            state: Optional state parameter for OAuth
            
        Returns:
            Flow: Google OAuth2 flow instance
        """
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": Config.GOOGLE_CLIENT_ID,
                    "client_secret": Config.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [Config.GOOGLE_REDIRECT_URI]
                }
            },
            scopes=GoogleCalendarService.SCOPES,
            redirect_uri=Config.GOOGLE_REDIRECT_URI
        )
        
        if state:
            flow.state = state
            
        return flow
    
    @staticmethod
    def get_authorization_url(user_id):
        """
        Generate Google OAuth authorization URL
        
        Args:
            user_id: User ID to include in state
            
        Returns:
            str: Authorization URL
        """
        flow = GoogleCalendarService.get_oauth_flow()
        
        # Include user_id in state for security
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            prompt='consent',  # Force consent to get refresh token
            state=user_id
        )
        
        logger.info(f"Generated OAuth URL for user {user_id}")
        return authorization_url
    
    @staticmethod
    def handle_oauth_callback(authorization_code, state):
        """
        Handle OAuth callback and store tokens
        
        Args:
            authorization_code: Authorization code from Google
            state: State parameter (contains user_id)
            
        Returns:
            dict: User data with updated Google Calendar connection
        """
        try:
            user_id = state
            
            # Exchange code for tokens
            flow = GoogleCalendarService.get_oauth_flow()
            flow.fetch_token(code=authorization_code)
            
            credentials = flow.credentials
            
            # Store tokens in database
            query = """
                UPDATE users 
                SET google_calendar_connected = TRUE,
                    google_access_token = %s,
                    google_refresh_token = %s,
                    google_token_expires = %s,
                    updated_at = NOW()
                WHERE id = %s
            """
            
            expires_at = datetime.now() + timedelta(seconds=credentials.expiry.timestamp() - datetime.now().timestamp()) if credentials.expiry else None
            
            db.execute_query(
                query,
                [
                    credentials.token,
                    credentials.refresh_token,
                    expires_at,
                    user_id
                ],
                fetch_all=False
            )
            
            logger.info(f"Google Calendar connected for user {user_id}")
            
            # Return updated user
            user = db.execute_query(
                "SELECT * FROM users WHERE id = %s",
                [user_id],
                fetch_one=True
            )
            
            return user
            
        except Exception as e:
            logger.error(f"OAuth callback error: {str(e)}")
            raise
    
    @staticmethod
    def disconnect_calendar(user_id):
        """
        Disconnect Google Calendar for user
        
        Args:
            user_id: User ID
        """
        query = """
            UPDATE users 
            SET google_calendar_connected = FALSE,
                google_access_token = NULL,
                google_refresh_token = NULL,
                google_token_expires = NULL,
                updated_at = NOW()
            WHERE id = %s
        """
        
        db.execute_query(query, [user_id], fetch_all=False)
        logger.info(f"Google Calendar disconnected for user {user_id}")
    
    @staticmethod
    def get_credentials(user_id):
        """
        Get valid Google credentials for user
        Refreshes token if expired
        
        Args:
            user_id: User ID
            
        Returns:
            Credentials: Google OAuth2 credentials
        """
        user = db.execute_query(
            """
            SELECT google_access_token, google_refresh_token, google_token_expires
            FROM users 
            WHERE id = %s AND google_calendar_connected = TRUE
            """,
            [user_id],
            fetch_one=True
        )
        
        if not user or not user['google_access_token']:
            raise ValueError("User not connected to Google Calendar")
        
        # Create credentials object
        credentials = Credentials(
            token=user['google_access_token'],
            refresh_token=user['google_refresh_token'],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=Config.GOOGLE_CLIENT_ID,
            client_secret=Config.GOOGLE_CLIENT_SECRET,
            scopes=GoogleCalendarService.SCOPES
        )
        
        # Check if token is expired and refresh if needed
        if credentials.expired and credentials.refresh_token:
            from google.auth.transport.requests import Request
            credentials.refresh(Request())
            
            # Update tokens in database
            db.execute_query(
                """
                UPDATE users 
                SET google_access_token = %s,
                    google_token_expires = %s
                WHERE id = %s
                """,
                [
                    credentials.token,
                    datetime.now() + timedelta(seconds=3600),
                    user_id
                ],
                fetch_all=False
            )
            
            logger.info(f"Refreshed Google token for user {user_id}")
        
        return credentials
    
    @staticmethod
    def create_event(user_id, event_data):
        """
        Create event in Google Calendar
        
        Args:
            user_id: User ID
            event_data: Event data dict with title, description, start_time, end_time, location
            
        Returns:
            str: Google Calendar event ID
        """
        try:
            credentials = GoogleCalendarService.get_credentials(user_id)
            service = build('calendar', 'v3', credentials=credentials)
            
            # Format event for Google Calendar
            start_time = datetime.fromisoformat(event_data['start_time'].replace('Z', '+00:00'))
            end_time = datetime.fromisoformat(event_data['end_time'].replace('Z', '+00:00'))
            
            google_event = {
                'summary': event_data['title'],
                'description': event_data.get('description', ''),
                'location': event_data.get('location', ''),
                'start': {
                    'dateTime': start_time.isoformat(),
                    'timeZone': 'Europe/Rome',
                },
                'end': {
                    'dateTime': end_time.isoformat(),
                    'timeZone': 'Europe/Rome',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'popup', 'minutes': event_data.get('reminder_minutes', 30)},
                    ],
                },
            }
            
            # Handle all-day events
            if event_data.get('is_all_day'):
                google_event['start'] = {'date': start_time.date().isoformat()}
                google_event['end'] = {'date': end_time.date().isoformat()}
            
            # Create event
            event = service.events().insert(calendarId='primary', body=google_event).execute()
            
            logger.info(f"Created Google Calendar event: {event['id']} for user {user_id}")
            return event['id']
            
        except HttpError as e:
            logger.error(f"Google Calendar API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error creating Google Calendar event: {str(e)}")
            raise
    
    @staticmethod
    def update_event(user_id, google_event_id, event_data):
        """
        Update event in Google Calendar
        
        Args:
            user_id: User ID
            google_event_id: Google Calendar event ID
            event_data: Updated event data
            
        Returns:
            bool: Success status
        """
        try:
            credentials = GoogleCalendarService.get_credentials(user_id)
            service = build('calendar', 'v3', credentials=credentials)
            
            # Get existing event
            event = service.events().get(calendarId='primary', eventId=google_event_id).execute()
            
            # Update fields
            if 'title' in event_data:
                event['summary'] = event_data['title']
            if 'description' in event_data:
                event['description'] = event_data['description']
            if 'location' in event_data:
                event['location'] = event_data['location']
            if 'start_time' in event_data:
                start_time = datetime.fromisoformat(event_data['start_time'].replace('Z', '+00:00'))
                if event_data.get('is_all_day'):
                    event['start'] = {'date': start_time.date().isoformat()}
                else:
                    event['start'] = {'dateTime': start_time.isoformat(), 'timeZone': 'Europe/Rome'}
            if 'end_time' in event_data:
                end_time = datetime.fromisoformat(event_data['end_time'].replace('Z', '+00:00'))
                if event_data.get('is_all_day'):
                    event['end'] = {'date': end_time.date().isoformat()}
                else:
                    event['end'] = {'dateTime': end_time.isoformat(), 'timeZone': 'Europe/Rome'}
            
            # Update event
            updated_event = service.events().update(
                calendarId='primary',
                eventId=google_event_id,
                body=event
            ).execute()
            
            logger.info(f"Updated Google Calendar event: {google_event_id} for user {user_id}")
            return True
            
        except HttpError as e:
            logger.error(f"Google Calendar API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error updating Google Calendar event: {str(e)}")
            raise
    
    @staticmethod
    def delete_event(user_id, google_event_id):
        """
        Delete event from Google Calendar
        
        Args:
            user_id: User ID
            google_event_id: Google Calendar event ID
            
        Returns:
            bool: Success status
        """
        try:
            credentials = GoogleCalendarService.get_credentials(user_id)
            service = build('calendar', 'v3', credentials=credentials)
            
            service.events().delete(calendarId='primary', eventId=google_event_id).execute()
            
            logger.info(f"Deleted Google Calendar event: {google_event_id} for user {user_id}")
            return True
            
        except HttpError as e:
            if e.resp.status == 404:
                logger.warning(f"Event {google_event_id} not found in Google Calendar")
                return True  # Event doesn't exist, consider it deleted
            logger.error(f"Google Calendar API error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error deleting Google Calendar event: {str(e)}")
            raise
