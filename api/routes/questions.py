"""Questions API routes.

Single-library architecture: questions operate on the configured library root.
See ADR 0005 for details.
"""

import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from api.dependencies import get_storage_backend, MockBackend
from storage.backend import StorageBackend


router = APIRouter(prefix="/questions", tags=["questions"])

# In-memory question store for retrieval
_question_store: dict[str, dict] = {}


# Request/Response Schemas
class QuestionOptions(BaseModel):
    """Options for question answering."""
    include_evidence: bool = Field(default=True, description="Include evidence in response")
    include_trace: bool = Field(default=True, description="Include evidence trace")
    max_evidence_items: int = Field(default=10, ge=1, le=100, description="Max evidence items")


class QuestionRequest(BaseModel):
    """Request schema for asking a question."""
    question: str = Field(..., min_length=1, max_length=1000, description="The question to answer")
    options: Optional[QuestionOptions] = Field(default_factory=QuestionOptions)


class AnswerData(BaseModel):
    """Answer data structure."""
    text: str
    confidence: float


class QuestionResponse(BaseModel):
    """Response schema for question answering."""
    id: str
    status: str = "completed"
    answer: AnswerData
    evidence: dict = Field(default_factory=dict)
    trace: list = Field(default_factory=list)


class QuestionHistoryResponse(BaseModel):
    """Response schema for question history retrieval."""
    id: str
    question: str
    status: str
    answer: AnswerData
    evidence: dict
    trace: list
    created_at: str


def generate_question_id() -> str:
    """Generate a unique question ID."""
    return f"q-{uuid.uuid4().hex[:8]}"


# Routes
@router.post(
    "",
    response_model=QuestionResponse,
    status_code=status.HTTP_200_OK,
    responses={
        422: {"description": "Validation error"}
    }
)
async def ask_question(
    request: QuestionRequest,
    backend: StorageBackend = Depends(get_storage_backend)
) -> QuestionResponse:
    """
    Ask a question about the library.
    
    This endpoint processes a natural language question against the configured
    library and returns an answer along with supporting evidence.
    """
    # Generate question ID
    question_id = generate_question_id()
    
    # Import the core ask function
    try:
        from core.ask import ask
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "Core ask module not available",
                "details": []
            }
        )
    
    # Call the core ask function
    try:
        result = ask(question=request.question, backend=backend)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "code": "PROCESSING_ERROR",
                "message": f"Error processing question: {str(e)}",
                "details": []
            }
        )
    
    # Extract answer from result
    answer_data = result.get("answer", {})
    answer_text = answer_data.get("answer", "I couldn't find an answer to your question.")
    confidence = answer_data.get("confidence", 0.0)
    
    # Build response
    response = QuestionResponse(
        id=question_id,
        status="completed",
        answer=AnswerData(
            text=answer_text,
            confidence=confidence
        )
    )
    
    # Add evidence if requested
    if request.options and request.options.include_evidence:
        evidence = result.get("evidence", {})
        response.evidence = {
            "documents": evidence.get("documents", []),
            "entities": evidence.get("entities", []),
            "events": evidence.get("events", []),
            "locations": evidence.get("locations", []),
            "relationships": evidence.get("relationships", [])
        }
    
    # Add trace if requested
    if request.options and request.options.include_trace:
        try:
            from core.evidence_trace import build_trace
            trace = build_trace(response.evidence)
            max_items = request.options.max_evidence_items if request.options else 10
            response.trace = trace[:max_items]
        except ImportError:
            response.trace = []
    
    # Store for history retrieval
    _question_store[question_id] = {
        "id": question_id,
        "question": request.question,
        "status": "completed",
        "answer": response.answer.model_dump(),
        "evidence": response.evidence,
        "trace": response.trace,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return response


@router.get(
    "/{question_id}",
    response_model=QuestionHistoryResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {"description": "Question not found"}
    }
)
async def get_question(
    question_id: str
) -> QuestionHistoryResponse:
    """
    Get a previously asked question with its answer and evidence.
    
    Returns the full response including answer, evidence, and trace.
    """
    if question_id not in _question_store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "NOT_FOUND",
                "message": f"Question {question_id} not found",
                "details": []
            }
        )
    
    stored = _question_store[question_id]
    return QuestionHistoryResponse(
        id=stored["id"],
        question=stored["question"],
        status=stored["status"],
        answer=AnswerData(**stored["answer"]),
        evidence=stored["evidence"],
        trace=stored["trace"],
        created_at=stored["created_at"]
    )