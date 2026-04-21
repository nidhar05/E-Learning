# Installation & Setup Guide - Quiz and Notes Features

## Step 1: Backend Setup

### 1.1 Run Database Migrations

```bash
cd d:\E-Learning\Learning_Platform

# Create migration files
python manage.py makemigrations quiz
python manage.py makemigrations notes

# Apply migrations
python manage.py migrate
```

This creates the following tables:
- `quiz_quiz` - Quiz information
- `quiz_quizquestion` - Quiz questions
- `quiz_userquizattempt` - User quiz attempts
- `quiz_useranswer` - User answers to quiz questions
- `notes_videonotes` - Video notes
- `notes_notesection` - Sections within notes
- `notes_notebookmark` - User bookmarks
- `notes_usernoteprogress` - User progress tracking

### 1.2 Create Superuser (if not already created)

```bash
python manage.py createsuperuser
```

### 1.3 Start Django Server

```bash
python manage.py runserver
```

Visit http://localhost:8000/admin to access the admin panel.

---

## Step 2: Generate Sample Data

### Using Management Commands

#### Generate Quiz for a Video

```bash
# Basic usage
python manage.py generate_quiz 1

# With custom title and number of questions
python manage.py generate_quiz 1 --title "Python Basics Quiz" --num-questions 5
```

#### Generate Notes for a Video

```bash
# Basic usage
python manage.py generate_notes 1

# With custom title and number of sections
python manage.py generate_notes 1 --title "Python Basics Notes" --num-sections 4
```

### Using Django Admin

1. Navigate to http://localhost:8000/admin
2. Go to Quiz section
3. Click "Add Quiz"
4. Select a video
5. Fill in quiz details
6. Add questions using the inline interface
7. Save

---

## Step 3: Frontend Setup

### 3.1 Update Video Page Component

Add the Quiz and Notes components to your video detail page:

```jsx
// components/VideoDetail.jsx
'use client';

import VideoPlayer from '@/components/VideoPlayer';
import QuizComponent from '@/components/QuizComponent';
import NotesComponent from '@/components/NotesComponent';

export default function VideoDetail({ params }) {
  const videoId = params.videoId;

  return (
    <div className="max-w-7xl mx-auto p-4">
      <div className="mb-8">
        <VideoPlayer videoId={videoId} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Quiz Section */}
        <div className="bg-gray-50 p-6 rounded-lg">
          <h2 className="text-2xl font-bold mb-4">Quiz</h2>
          <QuizComponent videoId={videoId} />
        </div>

        {/* Notes Section */}
        <div className="bg-gray-50 p-6 rounded-lg">
          <h2 className="text-2xl font-bold mb-4">Notes</h2>
          <NotesComponent videoId={videoId} />
        </div>
      </div>
    </div>
  );
}
```

### 3.2 Frontend Components Already Created

The following components are ready to use:

- **QuizComponent** - Displays and manages quizzes (`src/components/QuizComponent.jsx`)
- **NotesComponent** - Displays and manages notes (`src/components/NotesComponent.jsx`)

### 3.3 Start Next.js Frontend

```bash
cd d:\E-Learning\next_frontend

npm install   # If not already installed
npm run dev   # Start development server
```

Visit http://localhost:3000

---

## Step 4: Testing the Features

### Test Quiz Feature

1. Navigate to a video page
2. Click "Start Quiz" button
3. Answer questions
4. Click "Submit Quiz"
5. View results

### Test Notes Feature

1. Navigate to a video page
2. Browse through note sections
3. Click "Bookmark" to save sections
4. Scroll to see progress bar
5. Track completion percentage

---

## API Quick Reference

### Quiz Endpoints

```bash
# Get all quizzes
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/quiz/

# Get quiz for a video
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/quiz/video/1/

# Start a quiz attempt
curl -X POST -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"quiz_id": 1}' \
  http://localhost:8000/api/quiz/attempts/start_quiz/

# Submit an answer
curl -X POST -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"question_id": 1, "answer": "A"}' \
  http://localhost:8000/api/quiz/attempts/1/submit_answer/

# Submit quiz
curl -X POST -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/quiz/attempts/1/submit_quiz/

# Get my attempts
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/quiz/attempts/my_attempts/
```

### Notes Endpoints

```bash
# Get all notes
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/notes/

# Get notes for a video
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/notes/video/1/

# Get note sections
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/notes/1/sections/

# Add bookmark
curl -X POST -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"notes_id": 1, "section_id": 1, "title": "My Bookmark"}' \
  http://localhost:8000/api/notes/bookmarks/add_bookmark/

# Track progress
curl -X POST -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"notes_id": 1, "section_id": 1, "progress_percentage": 50}' \
  http://localhost:8000/api/notes/progress/track_progress/

# Mark section read
curl -X POST -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"notes_id": 1, "section_id": 1}' \
  http://localhost:8000/api/notes/progress/mark_section_read/

# Get my progress
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/notes/progress/my_progress/
```

---

## Admin Panel Guide

### Quiz Administration

1. **Quiz Management**
   - View all quizzes
   - Create/Edit/Delete quizzes
   - Set passing scores and attempt limits
   - View question statistics

2. **Question Management**
   - Add/Edit questions inline
   - Support multiple question types
   - Set correct answers and explanations

3. **User Attempts**
   - Monitor student attempts
   - View scores and pass/fail status
   - Review individual answers
   - Track attempt history

### Notes Administration

1. **Notes Management**
   - Create/Edit/Delete notes
   - Mark as AI-generated or instructor-created
   - Publish/unpublish notes

2. **Section Management**
   - Organize sections with icons
   - Add rich-text content
   - Reorder sections

3. **User Progress**
   - Track section completion
   - Monitor reading progress
   - View last accessed information

---

## Troubleshooting

### Database Issues

**Problem:** Migration errors
```bash
# Solution: Rollback and retry
python manage.py migrate quiz zero
python manage.py migrate notes zero
python manage.py makemigrations quiz notes
python manage.py migrate
```

### API Authentication Issues

**Problem:** 401 Unauthorized errors
```bash
# Ensure you have a valid token
# Check localStorage for access_token
# Login again if token expired
```

### Component Not Showing

**Problem:** Quiz or Notes component not displaying
1. Check API_BASE_URL in client.js
2. Ensure quiz/notes exist for the video
3. Check browser console for errors
4. Verify authentication token

### CORS Errors

**Problem:** Cross-Origin requests failing
```python
# Solution: Already configured in settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

---

## Features Summary

### Quiz Features
✅ Multiple question types (MCQ, True/False, Short Answer, Essay)
✅ Automatic grading for objective questions
✅ Attempt limiting
✅ Time limits (configurable)
✅ Progress tracking
✅ Detailed results with explanations
✅ User answer history
✅ Score analytics

### Notes Features
✅ Organized sections
✅ Rich text content
✅ Progress tracking
✅ Bookmarking system
✅ Key takeaways and important terms
✅ AI-generated or instructor-created
✅ Section ordering with icons
✅ Completion percentage

---

## Future Enhancements

### AI Integration
- [ ] Auto-generate quiz questions from video transcripts
- [ ] Auto-generate notes from video content
- [ ] AI-powered answer evaluation
- [ ] Difficulty level assessment

### Advanced Features
- [ ] Timer with auto-submission
- [ ] Partial credit scoring
- [ ] PDF export for notes
- [ ] Markdown support
- [ ] Image/video in quiz questions
- [ ] Analytics dashboard for instructors
- [ ] Adaptive learning paths
- [ ] Mobile app optimization

---

## Support & Documentation

- Main Documentation: See QUIZ_AND_NOTES_FEATURES.md
- Django Admin: http://localhost:8000/admin
- API Documentation: Available at endpoints
- Code Examples: Check management commands

---

## File Structure

```
Learning_Platform/
├── quiz/
│   ├── migrations/
│   ├── management/
│   │   ├── commands/
│   │   │   └── generate_quiz.py
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── urls.py
│   ├── admin.py
│   └── tests.py
├── notes/
│   ├── migrations/
│   ├── management/
│   │   ├── commands/
│   │   │   └── generate_notes.py
│   ├── models.py
│   ├── views.py
│   ├── serializers.py
│   ├── urls.py
│   ├── admin.py
│   └── tests.py

next_frontend/
├── src/
│   └── components/
│       ├── QuizComponent.jsx
│       └── NotesComponent.jsx
```

---

## Next Steps

1. ✅ Run migrations
2. ✅ Create sample data using management commands
3. ✅ Add components to video pages
4. ✅ Test quiz and notes features
5. ✅ Customize styling and functionality as needed
6. ⏳ Implement AI generation features
7. ⏳ Add instructor analytics dashboard
