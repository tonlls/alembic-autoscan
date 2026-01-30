"""
Post model for the example project.
"""

# from models.post import Post
from models.article_tablename import ArticleTablename
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Article(Base,ArticleTablename):
    """Article model representing blog posts."""


    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    author = relationship("User", backref="articles")

    def __repr__(self):
        return f"<Article(id={self.id}, title='{self.title}')>"
