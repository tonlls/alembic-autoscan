"""
Post model for the example project.
"""

from examples.sample_project.models.post import Post
from examples.sample_project.models.article_tablename import ArticleTablename
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Article(Post, ArticleTablename):
    """Article model representing blog posts."""

    # __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    author = relationship("User", backref="posts")

    def __repr__(self):
        return f"<Post(id={self.id}, title='{self.title}')>"
