from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Workflow(Base):
    __tablename__ = "workflows"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    graph_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    executions = relationship("Execution", back_populates="workflow")


class Execution(Base):
    __tablename__ = "executions"
    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("workflows.id"), nullable=False)
    status = Column(String(50), nullable=False, default="running")
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)

    workflow = relationship("Workflow", back_populates="executions")
    steps = relationship("StepResult", back_populates="execution")


class StepResult(Base):
    __tablename__ = "step_results"
    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("executions.id"), nullable=False)
    node_id = Column(String(255), nullable=False)
    node_type = Column(String(100), nullable=False)
    input = Column(JSON)
    output = Column(JSON)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    execution = relationship("Execution", back_populates="steps")


class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(512), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    chunks = relationship("DocumentChunk", back_populates="document")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=False)

    document = relationship("Document", back_populates="chunks")
