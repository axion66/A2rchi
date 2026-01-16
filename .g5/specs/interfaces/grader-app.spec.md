---
id: interfaces-grader-app
title: Grader App Interface
version: 1.0.0
status: extracted
sources:
  - src/interfaces/grader_app/app.py
---

# Grader App Interface

Flask-based web application for AI-assisted grading of student submissions.

## ImageToTextWrapper

Wrapper for extracting text from images using vision models.

```python
class ImageToTextWrapper:
    def __init__(self):
        self.config: Dict
        self.pg_config: Dict
        self.conn: Optional[psycopg2.connection]
        self.cursor: Optional[psycopg2.cursor]
        self.lock: Lock
        self.image_processor: A2rchi  # Using ImageProcessingPipeline
```

### Methods

#### `__call__(images: List[str]) -> str`
Extract text from base64-encoded images.

**Contract:**
- PRE: `images` is list of base64-encoded image strings
- POST: Returns extracted text from all images
- POST: Lock acquired during processing
- POST: On error, returns "Error processing images"

---

## GradingWrapper

Wrapper for the AI grading pipeline.

```python
class GradingWrapper:
    def __init__(self):
        self.config: Dict
        self.pg_config: Dict
        self.conn: Optional[psycopg2.connection]
        self.cursor: Optional[psycopg2.cursor]
        self.lock: Lock
        self.grader: A2rchi  # Using GradingPipeline
```

### Methods

#### `__call__(student_solution: str, official_explanation: str, additional_comments: str = "") -> str`
Grade a student submission against official solution.

**Contract:**
- PRE: `student_solution` is student's answer text
- PRE: `official_explanation` is rubric/solution text
- POST: Returns final evaluation/feedback text
- POST: Lock acquired during grading
- POST: On error, returns "Error during grading pipeline"

**Pipeline Flow:**
1. Summarize student submission
2. Analyze against rubric
3. Generate final decision/feedback

---

## Flask Application

### User Management

Uses Flask-Login for authentication:
- Admin users can manage assignments
- Grader users can grade submissions
- Session-based authentication

### Routes

#### `GET /`
Redirect to login or dashboard.

#### `GET /login`
Render login page.

#### `POST /login`
Authenticate user.

#### `GET /logout`
Clear session and logout.

#### `GET /dashboard`
Main grading dashboard.

#### Assignment Management

#### `GET /assignments`
List all assignments.

#### `POST /assignments`
Create new assignment.

#### `GET /assignments/<id>`
View assignment details.

#### `DELETE /assignments/<id>`
Delete assignment.

#### Submission Handling

#### `POST /submissions/upload`
Upload student submissions (CSV format).

#### `GET /submissions/<id>`
View submission details.

#### `POST /submissions/<id>/grade`
Trigger AI grading for submission.

#### `POST /submissions/<id>/feedback`
Submit manual feedback/override.

#### Batch Operations

#### `POST /assignments/<id>/grade-all`
Grade all submissions for assignment.

#### `GET /assignments/<id>/export`
Export grading results as CSV.

---

## Data Models

### Assignment
- `id` - Unique identifier
- `name` - Assignment name
- `rubric` - Grading rubric text
- `created_at` - Timestamp

### Submission
- `id` - Unique identifier
- `assignment_id` - Foreign key
- `student_id` - Student identifier
- `content` - Submission text
- `images` - Base64 images (optional)
- `ai_grade` - AI-generated grade
- `ai_feedback` - AI-generated feedback
- `final_grade` - Instructor-approved grade
- `status` - pending/graded/reviewed

---

## Matching Algorithm

For matching student responses to rubric items:

### TF-IDF Fallback
Uses sklearn's TfidfVectorizer for semantic matching when embeddings unavailable.

### Fuzzy Matching
Uses RapidFuzz for string similarity on short answers.

### Hungarian Algorithm
Uses scipy's linear_sum_assignment for optimal rubric-response matching.

---

## Configuration

From `config["services"]["grader"]`:
- Pipeline settings
- Matching thresholds
- Export formats
