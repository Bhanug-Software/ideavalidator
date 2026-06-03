import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from app.utils.logger import logger

load_dotenv()

def get_db_connection():
    """create and return a postgresql database connection"""
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL not found in .env")
        conn = psycopg2.connect(database_url)
        logger.debug("✅ Database connected")
        return conn
    except Exception as e :
        logger.error(f"❌ Database connection failed: {str(e)}")
        raise


def save_conversation(project_idea,final_analysis):
    """save a new conversation to the database
    
    args:
        project_idea: the project idea description
        final_analysis : Claude's final recommendation
    returns:
        conversation_id: the ID of the saved conversation
    """

    conn =None
    try:
        conn = get_db_connection()
        cursor =conn.cursor()

        #insert new conversation
        query = """
            INSERT INTO conversations (project_idea, final_analysis,status) 
            VALUES (%s, %s, 'active')
            RETURNING id;
        """
        cursor.execute(query,(project_idea,final_analysis))
        conversation_id =cursor.fetchone()[0]

        conn.commit()
        logger.info(f"✅ Conversation saved with ID: {conversation_id}")
        return conversation_id
    
    except Exception as e :
        logger.error(f"❌ Failed to save conversation: {str(e)}")
        if conn:
            conn.rollback()
        raise
    
    finally:
        if conn:
            conn.close()

def save_message(conversation_id,role,content):
    """save a message (user or assistant) to the database

    args:
        conversation_id: the ID of the the conversation
        role: "user" or "assistant"
        content: the message text
    
    Returns:
            message_id: the ID of the saved message
    """

    conn =None
    try:
        conn = get_db_connection()
        cursor =conn.cursor()

        #insert new message
        query = """
                INSERT INTO messages (conversation_id, role, content)
                VALUES (%s, %s, %s)
                RETURNING id;
            """
        cursor.execute(query,((conversation_id, role, content)))
        message_id =cursor.fetchone()[0]

        conn.commit()

        logger.debug(f"✅ Message saved with ID: {message_id}")
        return message_id
    
    except Exception as e :
        logger.error(f"❌ Failed to save message: {str(e)}")
        if conn:
            conn.rollback()
        raise

    finally:
        if conn:
            conn.close()



def load_conversations(limit=10):
    """Get all conversations from the database

    Returns:
        List of conversations with id, project_idea, created_at, status
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get all conversations, ordered by newest first
        query = """
            SELECT id, project_idea, created_at, status
            FROM conversations
            ORDER BY created_at DESC
            LIMIT {limit};;
        """
        cursor.execute(query)
        conversations = cursor.fetchall()

        logger.info(f"✅ Loaded {len(conversations)} conversations")
        return conversations

    except Exception as e:
        logger.error(f"❌ Failed to load conversations: {str(e)}")
        return []

    finally:
        if conn:
            conn.close()


def load_conversation_messages(conversation_id):
    """Get all messages for a specific conversation

    Args:
        conversation_id: The ID of the conversation

    Returns:
        List of messages with role and content
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Get all messages for this conversation, ordered by oldest first
        query = """
            SELECT id, role, content, created_at
            FROM messages
            WHERE conversation_id = %s
            ORDER BY created_at ASC;
        """
        cursor.execute(query, (conversation_id,))
        messages = cursor.fetchall()

        logger.info(f"✅ Loaded {len(messages)} messages for conversation {conversation_id}")
        return messages

    except Exception as e:
        logger.error(f"❌ Failed to load messages: {str(e)}")
        return []

    finally:
        if conn:
            conn.close()

def update_conversation_status(conversation_id, status):
    """Update the status of a conversation (active, completed, archived)

    Args:
        conversation_id: The ID of the conversation
        status: New status ("active", "completed", or "archived")

    Returns:
        True if successful, False otherwise
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Update conversation status
        query = """
            UPDATE conversations
            SET status = %s
            WHERE id = %s;
        """
        cursor.execute(query, (status, conversation_id))
        conn.commit()

        logger.info(f"✅ Conversation {conversation_id} status updated to: {status}")
        return True

    except Exception as e:
        logger.error(f"❌ Failed to update conversation status: {str(e)}")
        if conn:
            conn.rollback()
        return False

    finally:
        if conn:
            conn.close()
