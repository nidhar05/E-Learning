AUTO-CREATION DOCUMENTATION
============================

## Overview

Quiz and Notes are now **automatically created** when students study videos. No manual configuration needed!

## How It Works

### 1. **Signal-Based Auto-Creation (Recommended)**
When a new video is added to the system, quiz and notes are automatically created immediately:
```
Video Created → Signal Triggered → Quiz Auto-Created + Notes Auto-Created
```

**Benefits:**
- Automatic and instant
- No additional commands needed
- Works seamlessly in background
- Perfect for bulk video uploads

### 2. **On-First-Access Auto-Creation (Fallback)**
If quiz/notes don't exist when a student tries to access them:
```
Student Views Video → API Request to GET quiz/notes
→ Auto-Create if Missing → Return to Student
```

**Endpoints that trigger auto-creation:**
- `GET /api/quiz/video/{video_id}/` - Auto-creates quiz if missing
- `GET /api/notes/video/{video_id}/` - Auto-creates notes if missing

### 3. **Bulk Command (For Existing Videos)**
Run once to create quiz/notes for all existing videos:
```bash
python manage.py create_quiz_notes_for_all_videos
```

## Implementation Details

### Signal Registration

File: `Learning_Platform/videos/signals.py`
- Listens to `post_save` signal from Video model
- Auto-creates Quiz with default sample question
- Auto-creates VideoNotes with default section
- Runs only when `created=True` (new video)

### Auto-Create Functions

**Quiz (quiz/views.py):**
```python
def auto_create_quiz(video):
    quiz, created = Quiz.objects.get_or_create(
        video=video,
        defaults={
            'title': f"Quiz: {video.title}",
            'description': f"Auto-generated quiz for: {video.title}",
            'passing_score': 70,
            'time_limit': 30,
            'max_attempts': 3,
            'is_published': True
        }
    )
    # Add sample question if newly created
    return quiz
```

**Notes (notes/views.py):**
```python
def auto_create_notes(video):
    notes, created = VideoNotes.objects.get_or_create(
        video=video,
        defaults={
            'title': f"Notes: {video.title}",
            'content': f"Notes for: {video.title}...",
            'is_ai_generated': True,
            'is_published': True
        }
    )
    # Add sample section if newly created
    return notes
```

### Views Updated

**QuizByVideoView** - Auto-creates quiz on first access:
```python
class QuizByVideoView(generics.RetrieveAPIView):
    def get_object(self):
        video_id = self.kwargs.get('video_id')
        video = get_object_or_404(Video, pk=video_id)
        return auto_create_quiz(video)  # Creates if missing
```

**NotesByVideoView** - Auto-creates notes on first access:
```python
class NotesByVideoView(generics.RetrieveAPIView):
    def get_object(self):
        video_id = self.kwargs.get('video_id')
        video = get_object_or_404(Video, pk=video_id)
        return auto_create_notes(video)  # Creates if missing
```

## Usage Examples

### Example 1: Adding a New Video (Auto-Creation)
```bash
# In Django shell or admin interface
from videos.models import Video
from courses.models import Course

course = Course.objects.first()
video = Video.objects.create(
    course=course,
    title="Python Basics",
    duration=1200,
    order=1
)
# Quiz and Notes are automatically created here! ✓
```

### Example 2: Bulk Create for All Existing Videos
```bash
python manage.py create_quiz_notes_for_all_videos

# Output:
# ✓ Completed:
#   - Quizzes created: 15
#   - Notes created: 15
#   - Videos skipped: 2
#   - Total quizzes: 45
#   - Total notes: 45
```

### Example 3: Force Recreate (Overwrite Existing)
```bash
python manage.py create_quiz_notes_for_all_videos --force

# This will recreate quiz and notes even if they already exist
```

### Example 4: Student Accesses Video (Auto-Creates on Access)
```bash
# Frontend makes request
fetch('/api/quiz/video/16/')
// If quiz doesn't exist, it's created automatically
// Student gets quiz data immediately

fetch('/api/notes/video/16/')
// If notes don't exist, they're created automatically
// Student gets notes data immediately
```

## What Gets Auto-Created?

### For Each Video:

**Quiz:**
- Title: "Quiz: {video_title}"
- Default sample question (Essay type)
- Passing score: 70%
- Time limit: 30 minutes
- Max attempts: 3
- Published: Yes

**Notes:**
- Title: "Notes: {video_title}"
- Default Introduction section
- Key takeaways: Template format
- Important terms: Glossary template
- Published: Yes

## Instructor Customization

After auto-creation, instructors can customize:

1. **Via Admin Interface:**
   - Go to http://localhost:8000/admin/
   - Edit Quiz questions, options, answers
   - Edit Notes sections, content
   - Manage key takeaways and glossary

2. **Via API (if instructor):**
   ```python
   # Update quiz
   PUT /api/quiz/{quiz_id}/
   {
       "title": "Custom Quiz Title",
       "passing_score": 80,
       "max_attempts": 5
   }

   # Add more questions
   POST /api/quiz/{quiz_id}/questions/
   # Questions auto-added to quiz
   ```

## Student Experience

1. **Student logs in** → Navigates to course
2. **Student clicks video** → Loads StudentProgressPage
3. **Student clicks "📋 Quiz"** → GET /api/quiz/video/{id}/ → Auto-created if missing → Quiz appears
4. **Student clicks "📝 Notes"** → GET /api/notes/video/{id}/ → Auto-created if missing → Notes appear

All automatic! No waiting for instructor setup.

## Troubleshooting

### Quiz/Notes not auto-creating after creating video?

**Check 1: Signals registered?**
```bash
python manage.py shell
>>> from django.db.models.signals import receiver
>>> # Verify videos.signals imported
>>> import videos.signals
>>> from videos.models import Video
>>> print(Video._meta.app_config.verbose_name)
```

**Check 2: Test signal manually:**
```bash
python manage.py shell
>>> from videos.models import Video
>>> from courses.models import Course
>>> course = Course.objects.first()
>>> v = Video.objects.create(
...     course=course,
...     title="Test",
...     duration=100,
...     order=1
... )
>>> v.quiz  # Should exist
>>> v.notes  # Should exist
```

**Check 3: Run bulk command:**
```bash
python manage.py create_quiz_notes_for_all_videos
python manage.py create_quiz_notes_for_all_videos --force
```

### API returns 404 for quiz/notes?

Old views that weren't updated. Verify endpoints use `QuizByVideoView` and `NotesByVideoView`:

```python
# In urls.py, check this:
path('quiz/video/<int:video_id>/', QuizByVideoView.as_view()),
path('notes/video/<int:video_id>/', NotesByVideoView.as_view()),
```

## Performance Notes

- Signal processing is synchronous (immediate)
- For large bulk imports (1000+ videos), use management command for better control
- Auto-creation adds ~50ms per video (database inserts)
- Caching recommended for high-traffic scenarios

## Migration Notes

For existing databases:

1. Create migrations: `python manage.py makemigrations`
2. Apply migrations: `python manage.py migrate`
3. Register signals: Run app migrations (auto)
4. Create for existing videos: `python manage.py create_quiz_notes_for_all_videos`

## Summary

✅ **Automatic** - No manual setup needed
✅ **Instant** - Quiz/Notes ready immediately
✅ **Smart** - Includes default templates
✅ **Scalable** - Works for bulk operations
✅ **Customizable** - Instructors can edit after creation
