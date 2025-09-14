"""
Interview management endpoints
"""
import uuid
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, File, UploadFile, Form, Depends
from fastapi.responses import FileResponse, HTMLResponse
import json
import os
from datetime import datetime

from app.models.interview import InterviewCreate, InterviewResponse, AnswerSubmission
from app.db.postgres import get_db_session
from app.workers.evaluator_worker import enqueue_evaluation
from app.utils.file_io import save_uploaded_file, generate_report
from app.utils.scoring import load_questions, get_next_question
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/interviews", response_model=InterviewResponse)
async def create_interview(interview_data: InterviewCreate):
    """Create a new interview session"""
    try:
        interview_id = str(uuid.uuid4())
        candidate_id = str(uuid.uuid4())
        
        # Load questions based on role and difficulty
        questions = load_questions(interview_data.role, interview_data.difficulty)
        
        if not questions:
            raise HTTPException(status_code=400, detail="No questions available for specified criteria")
        
        # Initialize interview session
        session_data = {
            "interview_id": interview_id,
            "candidate_id": candidate_id,
            "candidate_name": interview_data.candidate_name,
            "role": interview_data.role,
            "difficulty": interview_data.difficulty,
            "questions": questions[:6],  # Limit to 6 questions
            "current_question_index": 0,
            "answers": [],
            "created_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
        # Save to database
        async with get_db_session() as db:
            query = """
                INSERT INTO interviews (id, candidate_id, candidate_name, role, difficulty, session_data, status)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """
            await db.execute(query, interview_id, candidate_id, interview_data.candidate_name,
                           interview_data.role, interview_data.difficulty, json.dumps(session_data), "active")
        
        first_question = session_data["questions"][0]
        
        return InterviewResponse(
            interview_id=interview_id,
            first_question={
                "id": first_question["id"],
                "text": first_question["text"],
                "type": first_question["type"],
                "time_limit": first_question.get("time_limit", 300)
            }
        )
        
    except Exception as e:
        logger.error(f"Error creating interview: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/interviews/{interview_id}/next")
async def get_next_question(interview_id: str):
    """Get next question or final status"""
    try:
        async with get_db_session() as db:
            query = "SELECT session_data, status FROM interviews WHERE id = $1"
            row = await db.fetchrow(query, interview_id)
            
            if not row:
                raise HTTPException(status_code=404, detail="Interview not found")
            
            session_data = json.loads(row["session_data"])
            
            if row["status"] == "completed":
                return {
                    "status": "completed",
                    "report_url": f"/api/v1/interviews/{interview_id}/report"
                }
            
            next_question = get_next_question(session_data)
            
            if not next_question:
                # Mark interview as completed
                await db.execute("UPDATE interviews SET status = $1 WHERE id = $2", "completed", interview_id)
                return {
                    "status": "completed",
                    "report_url": f"/api/v1/interviews/{interview_id}/report"
                }
            
            return {
                "question": {
                    "id": next_question["id"],
                    "text": next_question["text"],
                    "type": next_question["type"],
                    "time_limit": next_question.get("time_limit", 300)
                },
                "progress": {
                    "current": session_data["current_question_index"] + 1,
                    "total": len(session_data["questions"])
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting next question: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/interviews/{interview_id}/answer")
async def submit_answer(
    interview_id: str,
    answer_text: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    """Submit an answer with optional file upload"""
    try:
        async with get_db_session() as db:
            query = "SELECT session_data FROM interviews WHERE id = $1"
            row = await db.fetchrow(query, interview_id)
            
            if not row:
                raise HTTPException(status_code=404, detail="Interview not found")
            
            session_data = json.loads(row["session_data"])
            current_index = session_data["current_question_index"]
            
            if current_index >= len(session_data["questions"]):
                raise HTTPException(status_code=400, detail="No more questions available")
            
            current_question = session_data["questions"][current_index]
            
            # Save uploaded file if provided
            file_path = None
            if file:
                file_path = await save_uploaded_file(file, interview_id, current_question["id"])
            
            # Create answer record
            answer_data = {
                "question_id": current_question["id"],
                "answer_text": answer_text,
                "file_path": file_path,
                "submitted_at": datetime.utcnow().isoformat(),
                "evaluation_status": "pending"
            }
            
            session_data["answers"].append(answer_data)
            session_data["current_question_index"] += 1
            
            # Update session data
            await db.execute(
                "UPDATE interviews SET session_data = $1 WHERE id = $2",
                json.dumps(session_data), interview_id
            )
            
            # Enqueue evaluation job
            job_id = await enqueue_evaluation(interview_id, current_question["id"], answer_data)
            
            return {
                "evaluation_pending": True,
                "estimated_time_sec": 15,
                "job_id": job_id
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting answer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/interviews/{interview_id}/report")
async def get_report(interview_id: str, format: str = "html"):
    """Generate and return interview report"""
    try:
        async with get_db_session() as db:
            query = "SELECT * FROM interviews WHERE id = $1"
            row = await db.fetchrow(query, interview_id)
            
            if not row:
                raise HTTPException(status_code=404, detail="Interview not found")
            
            session_data = json.loads(row["session_data"])
            
            # Generate report
            report_content = await generate_report(session_data, format)
            
            if format.lower() == "pdf":
                return FileResponse(
                    report_content,
                    media_type="application/pdf",
                    filename=f"interview_report_{interview_id}.pdf"
                )
            else:
                return HTMLResponse(content=report_content)
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail=str(e))
