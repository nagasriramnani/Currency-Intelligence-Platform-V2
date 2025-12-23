"""
Database Models for Newsletter Automation

SQLAlchemy models for:
- newsletter_subs: Subscriber management
- company_news_cache: AI-generated news cache
- newsletter_history: Sent newsletter log
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, timedelta
import os

Base = declarative_base()


class NewsletterSubscriber(Base):
    """Newsletter subscriber model."""
    __tablename__ = 'newsletter_subs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), unique=True, nullable=False)
    email = Column(String(255), nullable=False)
    frequency = Column(String(20), default='weekly')  # daily, weekly, monthly
    next_send_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(days=7))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    unsubscribed_at = Column(DateTime, nullable=True)
    
    # Relationship to newsletter history
    newsletters = relationship('NewsletterHistory', back_populates='subscriber')
    
    def __repr__(self):
        return f"<NewsletterSubscriber(email='{self.email}', frequency='{self.frequency}')>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'email': self.email,
            'frequency': self.frequency,
            'next_send_at': self.next_send_at.isoformat() if self.next_send_at else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class CompanyNewsCache(Base):
    """Cache for AI-generated company news summaries."""
    __tablename__ = 'company_news_cache'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    company_number = Column(String(20), nullable=False, index=True)
    company_name = Column(String(255))
    ai_summary = Column(Text)
    raw_news_json = Column(Text)  # JSON string of raw news data
    eis_score = Column(Integer)
    eis_status = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, default=lambda: datetime.utcnow() + timedelta(hours=24))
    
    def __repr__(self):
        return f"<CompanyNewsCache(company='{self.company_name}', score={self.eis_score})>"
    
    def is_fresh(self):
        """Check if cache is still valid (less than 24 hours old)."""
        if not self.expires_at:
            return False
        return datetime.utcnow() < self.expires_at
    
    def to_dict(self):
        return {
            'id': self.id,
            'company_number': self.company_number,
            'company_name': self.company_name,
            'ai_summary': self.ai_summary,
            'eis_score': self.eis_score,
            'eis_status': self.eis_status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_fresh': self.is_fresh()
        }


class NewsletterHistory(Base):
    """Log of sent newsletters."""
    __tablename__ = 'newsletter_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    subscriber_id = Column(Integer, ForeignKey('newsletter_subs.id'))
    sent_at = Column(DateTime, default=datetime.utcnow)
    companies_included = Column(Integer, default=0)
    delivery_status = Column(String(20), default='pending')  # pending, sent, failed
    error_message = Column(Text, nullable=True)
    
    # Relationship
    subscriber = relationship('NewsletterSubscriber', back_populates='newsletters')
    
    def __repr__(self):
        return f"<NewsletterHistory(subscriber_id={self.subscriber_id}, status='{self.delivery_status}')>"


# Database connection management
class DatabaseManager:
    """Manages database connections and sessions."""
    
    _engine = None
    _Session = None
    
    @classmethod
    def get_engine(cls, db_url=None):
        """Get or create database engine."""
        if cls._engine is None:
            db_url = db_url or os.getenv('DATABASE_URL', 'sqlite:///newsletter.db')
            cls._engine = create_engine(db_url, echo=False)
        return cls._engine
    
    @classmethod
    def get_session(cls):
        """Get a new database session."""
        if cls._Session is None:
            cls._Session = sessionmaker(bind=cls.get_engine())
        return cls._Session()
    
    @classmethod
    def init_db(cls):
        """Create all tables."""
        engine = cls.get_engine()
        Base.metadata.create_all(engine)
        return engine


# Convenience functions
def get_db_session():
    """Get a database session."""
    return DatabaseManager.get_session()


def init_database():
    """Initialize the database (create tables)."""
    DatabaseManager.init_db()
    print("Database initialized successfully.")
