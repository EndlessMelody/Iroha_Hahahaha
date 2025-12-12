"""
Database module for Iroha AI - Chat history storage
Using SQLite + SQLAlchemy for simplicity
"""

import os
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from loguru import logger

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./iroha_chat.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ===== MODELS =====

class ChatSession(Base):
    """Chat session - represents a conversation thread"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), default="New Chat")
    persona = Column(String(50), default="iroha")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_archived = Column(Boolean, default=False)
    
    # Relationship
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "persona": self.persona,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_archived": self.is_archived,
            "message_count": len(self.messages) if self.messages else 0
        }


class ChatMessage(Base):
    """Individual chat message"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Optional metadata
    voice_used = Column(String(50), nullable=True)
    response_time = Column(String(20), nullable=True)
    
    # Relationship
    session = relationship("ChatSession", back_populates="messages")
    
    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "voice_used": self.voice_used,
            "response_time": self.response_time
        }


# ===== DATABASE OPERATIONS =====

class ChatDatabase:
    """Database operations for chat history"""
    
    def __init__(self):
        # Create tables if not exist
        Base.metadata.create_all(bind=engine)
        logger.info("Chat database initialized")
    
    def get_db(self):
        """Get database session"""
        db = SessionLocal()
        try:
            return db
        except:
            db.close()
            raise
    
    # ===== SESSION OPERATIONS =====
    
    def create_session(self, title: str = "New Chat", persona: str = "iroha") -> ChatSession:
        """Create a new chat session"""
        db = self.get_db()
        try:
            session = ChatSession(title=title, persona=persona)
            db.add(session)
            db.commit()
            db.refresh(session)
            logger.info(f"Created chat session: {session.id}")
            return session
        finally:
            db.close()
    
    def get_session(self, session_id: int) -> Optional[ChatSession]:
        """Get session by ID"""
        db = self.get_db()
        try:
            return db.query(ChatSession).filter(ChatSession.id == session_id).first()
        finally:
            db.close()
    
    def get_all_sessions(self, include_archived: bool = False) -> List[dict]:
        """Get all chat sessions with message counts"""
        db = self.get_db()
        try:
            query = db.query(ChatSession)
            if not include_archived:
                query = query.filter(ChatSession.is_archived == False)
            sessions = query.order_by(ChatSession.updated_at.desc()).all()
            # Convert to dict while session is still active to avoid lazy load
            result = []
            for s in sessions:
                result.append({
                    "id": s.id,
                    "title": s.title,
                    "persona": s.persona,
                    "created_at": s.created_at.isoformat(),
                    "updated_at": s.updated_at.isoformat(),
                    "is_archived": s.is_archived,
                    "message_count": len(s.messages) if s.messages else 0
                })
            return result
        finally:
            db.close()
    
    def update_session_title(self, session_id: int, title: str) -> Optional[ChatSession]:
        """Update session title"""
        db = self.get_db()
        try:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session:
                session.title = title
                session.updated_at = datetime.utcnow()
                db.commit()
                db.refresh(session)
            return session
        finally:
            db.close()
    
    def archive_session(self, session_id: int) -> bool:
        """Archive a session"""
        db = self.get_db()
        try:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session:
                session.is_archived = True
                db.commit()
                return True
            return False
        finally:
            db.close()
    
    def delete_session(self, session_id: int) -> bool:
        """Permanently delete a session"""
        db = self.get_db()
        try:
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session:
                db.delete(session)
                db.commit()
                logger.info(f"Deleted chat session: {session_id}")
                return True
            return False
        finally:
            db.close()
    
    # ===== MESSAGE OPERATIONS =====
    
    def add_message(
        self, 
        session_id: int, 
        role: str, 
        content: str,
        voice_used: Optional[str] = None,
        response_time: Optional[str] = None
    ) -> Optional[ChatMessage]:
        """Add a message to a session"""
        db = self.get_db()
        try:
            # Update session timestamp
            session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if not session:
                return None
            
            session.updated_at = datetime.utcnow()
            
            # Auto-generate title from first user message
            if session.title == "New Chat" and role == "user":
                session.title = content[:50] + ("..." if len(content) > 50 else "")
            
            # Create message
            message = ChatMessage(
                session_id=session_id,
                role=role,
                content=content,
                voice_used=voice_used,
                response_time=response_time
            )
            db.add(message)
            db.commit()
            db.refresh(message)
            return message
        finally:
            db.close()
    
    def get_session_messages(self, session_id: int) -> List[ChatMessage]:
        """Get all messages for a session"""
        db = self.get_db()
        try:
            return db.query(ChatMessage)\
                .filter(ChatMessage.session_id == session_id)\
                .order_by(ChatMessage.created_at.asc())\
                .all()
        finally:
            db.close()
    
    def get_session_history(self, session_id: int) -> List[dict]:
        """Get session messages as history format for AI"""
        messages = self.get_session_messages(session_id)
        return [{"role": m.role, "content": m.content} for m in messages]
    
    def clear_session_messages(self, session_id: int) -> bool:
        """Clear all messages in a session"""
        db = self.get_db()
        try:
            db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
            db.commit()
            return True
        finally:
            db.close()


# Singleton instance
chat_db = ChatDatabase()
