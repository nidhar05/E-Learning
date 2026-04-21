# Quiz and Notes Features Documentation

This document describes the new Quiz and Notes generation features for the E-Learning platform.

## Overview

The platform now supports two major features for video content:

### 1. **Quiz Generation**
Create interactive quizzes from video content to test student understanding.

### 2. **Notes Generation**
Generate comprehensive notes from video content organized into sections.

---

## Database Setup

Before using these features, run migrations:

```bash
# Navigate to the Django project directory
cd Learning_Platform

# Create migration files for quiz app
python manage.py makemigrations quiz

# Create migration files for notes app
python manage.py makemigrations notes

# Apply all migrations
python manage.py migrate
```

---

## API Endpoints

### Quiz APIs

#### List/Create Quizzes
- **GET** `/api/quiz/` - List all published quizzes
- **POST** `/api/quiz/` - Create a new quiz (Instructor only)

#### Quiz Detail
- **GET** `/api/quiz/<id>/` - Get quiz details with all questions
- **PUT** `/api/quiz/<id>/` - Update quiz (Instructor only)
- **DELETE** `/api/quiz/<id>/` - Delete quiz (Instructor only)

#### Get Quiz by Video
- **GET** `/api/quiz/video/<video_id>/` - Get quiz for a specific video

#### Quiz Attempts
- **POST** `/api/quiz/attempts/start_quiz/` - Start a new quiz attempt
  - Request body: `{ "quiz_id": 1 }`
  - Returns: Quiz attempt object with attempt_number

- **POST** `/api/quiz/attempts/<attempt_id>/submit_answer/` - Submit answer to a question
  - Request body: `{ "question_id": 1, "answer": "A" }`

- **POST** `/api/quiz/attempts/<attempt_id>/submit_quiz/` - Submit entire quiz for grading
  - Returns: Graded attempt with score and results

- **GET** `/api/quiz/attempts/my_attempts/` - Get all attempts by current user

- **GET** `/api/quiz/attempts/<attempt_id>/attempt_detail/` - Get detailed attempt with all answers

---

### Notes APIs

#### List/Create Notes
- **GET** `/api/notes/` - List all published notes
- **POST** `/api/notes/` - Create new notes (Instructor only)

#### Notes Detail
- **GET** `/api/notes/<id>/` - Get notes with all sections
- **PUT** `/api/notes/<id>/` - Update notes (Instructor only)
- **DELETE** `/api/notes/<id>/` - Delete notes (Instructor only)

#### Get Notes by Video
- **GET** `/api/notes/video/<video_id>/` - Get notes for a specific video

#### Note Sections
- **GET** `/api/notes/<notes_id>/sections/` - List all sections in notes
- **POST** `/api/notes/<notes_id>/sections/` - Create a new section
  - Request body:
    ```json
    {
      "title": "Section Title",
      "content": "Section content markdown",
      "order": 1,
      "icon": "📌"
    }
    ```

#### User Bookmarks
- **POST** `/api/notes/bookmarks/add_bookmark/` - Add/update a bookmark
  - Request body:
    ```json
    {
      "notes_id": 1,
      "section_id": 1,
      "title": "Bookmark title",
      "timestamp": 30
    }
    ```

- **GET** `/api/notes/bookmarks/my_bookmarks/` - Get all user bookmarks

#### User Progress
- **POST** `/api/notes/progress/track_progress/` - Update progress through notes
  - Request body:
    ```json
    {
      "notes_id": 1,
      "section_id": 1,
      "progress_percentage": 50
    }
    ```

- **POST** `/api/notes/progress/mark_section_read/` - Mark a section as read
  - Request body:
    ```json
    {
      "notes_id": 1,
      "section_id": 1
    }
    ```

- **GET** `/api/notes/progress/my_progress/` - Get all user progress

---

## Frontend Components

### QuizComponent

Display and manage quizzes for videos.

```jsx
import QuizComponent from '@/components/QuizComponent';

export default function VideoPage() {
  return (
    <QuizComponent videoId={1} />
  );
}
```

**Features:**
- Display quiz information and rules before starting
- Navigate through questions
- Support for multiple question types
- Real-time answer tracking
- Quiz submission and automatic grading
- Detailed results with score and review

---

### NotesComponent

Display and manage notes for videos.

```jsx
import NotesComponent from '@/components/NotesComponent';

export default function VideoPage() {
  return (
    <NotesComponent videoId={1} />
  );
}
```

**Features:**
- Organized sections with navigation
- Progress tracking through notes
- Bookmark specific sections
- Display key takeaways and important terms
- Progress bar showing completion percentage

---

## Data Models

### Quiz Model

```python
class Quiz(models.Model):
    video = ForeignKey(Video)  # One-to-one relationship
    title = CharField(max_length=255)
    description = TextField(blank=True, null=True)
    generated_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    passing_score = IntegerField(default=70)  # Percentage
    time_limit = IntegerField(blank=True, null=True)  # In minutes
    max_attempts = IntegerField(default=3)
    is_published = BooleanField(default=True)
```

### QuizQuestion Model

```python
class QuizQuestion(models.Model):
    QUESTION_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('short_answer', 'Short Answer'),
        ('essay', 'Essay'),
    ]
    
    quiz = ForeignKey(Quiz)
    question_type = CharField(choices=QUESTION_TYPES)
    question_text = TextField()
    option_a/b/c/d = CharField(max_length=500)  # For MCQ
    correct_answer = CharField(max_length=100)
    explanation = TextField(blank=True, null=True)
    order = IntegerField(default=0)
    points = IntegerField(default=1)
```

### VideoNotes Model

```python
class VideoNotes(models.Model):
    video = ForeignKey(Video)  # One-to-one relationship
    title = CharField(max_length=255)
    content = TextField()
    key_takeaways = TextField(blank=True, null=True)
    important_terms = TextField(blank=True, null=True)
    is_ai_generated = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    created_by = ForeignKey(User, null=True)
    is_published = BooleanField(default=True)
```

### NoteSection Model

```python
class NoteSection(models.Model):
    notes = ForeignKey(VideoNotes)
    title = CharField(max_length=255)
    content = TextField()
    order = IntegerField(default=0)
    icon = CharField(max_length=50, blank=True, null=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
```

---

## Usage Examples

### Creating a Quiz (Backend)

```python
from quiz.models import Quiz, QuizQuestion

# Create quiz
quiz = Quiz.objects.create(
    video_id=1,
    title="Python Basics Quiz",
    description="Test your knowledge of Python basics",
    passing_score=70,
    max_attempts=3
)

# Add questions
QuizQuestion.objects.create(
    quiz=quiz,
    question_type='multiple_choice',
    question_text='What is Python?',
    option_a='A programming language',
    option_b='A snake',
    option_c='A website',
    option_d='A game',
    correct_answer='A',
    explanation='Python is a popular programming language.',
    order=1,
    points=1
)
```

### Creating Notes (Backend)

```python
from notes.models import VideoNotes, NoteSection

# Create notes
notes = VideoNotes.objects.create(
    video_id=1,
    title='Python Basics Notes',
    content='# Introduction to Python\n\nPython is...',
    key_takeaways='- Python is versatile\n- Easy to learn',
    is_ai_generated=True,
    created_by=user
)

# Add sections
NoteSection.objects.create(
    notes=notes,
    title='Getting Started',
    content='# Getting Started\n\nTo install Python...',
    order=1,
    icon='🚀'
)
```

---

## Admin Panel

Both Quiz and Notes models are registered in Django admin:

- **Quiz Admin** - Manage quizzes, questions, and user attempts
- **Notes Admin** - Manage notes, sections, and user progress

Access via `/admin/` after logging in as a superuser.

---

## Permissions

### Quiz Permissions
- **Read:** All authenticated users can view published quizzes
- **Create:** Only instructors can create quizzes
- **Update/Delete:** Only instructors who own the video's course

### Notes Permissions
- **Read:** All authenticated users can view published notes
- **Create:** Only instructors can create notes
- **Update/Delete:** Only instructors who created the notes

---

## Features to Implement

### AI-Powered Generation (Future)
- Auto-generate quiz questions from video transcripts
- Auto-generate notes from video content
- Intelligent question difficulty assessment

### Advanced Features
- Timer for quizzes with auto-submission
- Partial credit scoring for open-ended questions
- AI-powered answer evaluation for essays
- Export notes to PDF/Markdown
- Analytics dashboard for instructors
- Adaptive learning based on quiz results

---

## Troubleshooting

### Migrations
If you encounter migration issues:
```bash
# Reset migrations (development only)
python manage.py migrate quiz zero
python manage.py migrate notes zero
python manage.py migrate

# Or create fresh migrations
python manage.py makemigrations --empty quiz --name reset_migrations
python manage.py makemigrations --empty notes --name reset_migrations
```

### API Errors
- **401 Unauthorized:** Make sure you're authenticated
- **403 Forbidden:** You don't have permission for that action
- **404 Not Found:** Resource doesn't exist
- **400 Bad Request:** Check your request body

### Frontend Issues
- Clear browser cache if components don't update
- Check API_BASE_URL in client.js matches your backend
- Verify authentication tokens in localStorage
