from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class QuizQuestion(BaseModel):
    id: int = Field(..., description="Question ID")
    question: str = Field(..., description="The question text")
    type: Literal["multiple_choices", "open_ended"]
    choices: Optional[List[str]] = None
    correct_answer: str = Field(..., description="for multiple_choices: choice text")
    difficulty: Optional[Literal["easy", "medium", "hard"]]
    source_page: int = Field(..., description="PDF page number where the question is grounded")


class QuizOutput(BaseModel):
    title: str = Field(..., description="Title or short description of the quiz")
    questions: List[QuizQuestion]