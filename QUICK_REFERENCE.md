# Quick Reference - Quiz & Notes Features

## 🚀 Quick Start (5 minutes)

### 1. Run Migrations
```bash
cd d:\E-Learning\Learning_Platform
python manage.py makemigrations quiz notes
python manage.py migrate
```

### 2. Start Django Server
```bash
python manage.py runserver
```

### 3. Start Next.js Frontend
```bash
cd d:\E-Learning\next_frontend
npm run dev
```

### 4. Access Services
- Django Admin: http://localhost:8000/admin
- Frontend: http://localhost:3000

---

## 📚 Create Sample Data

### Option A: Using Management Commands (Recommended)
```bash
# Generate quiz for video 1
python manage.py generate_quiz 1 --title "My Quiz" --num-questions 5

# Generate notes for video 1
python manage.py generate_notes 1 --title "My Notes" --num-sections 3
```

### Option B: Using Admin Panel
1. Go to http://localhost:8000/admin
2. Login with superuser credentials
3. Navigate to Quiz/Notes sections
4. Click "Add" to create manually

---

## 📁 Key Files

### Backend
- **Models:** `Learning_Platform/quiz/models.py`, `Learning_Platform/notes/models.py`
- **Views:** `Learning_Platform/quiz/views.py`, `Learning_Platform/notes/views.py`
- **URLs:** `Learning_Platform/quiz/urls.py`, `Learning_Platform/notes/urls.py`
- **Admin:** `Learning_Platform/quiz/admin.py`, `Learning_Platform/notes/admin.py`

### Frontend
- **Quiz Component:** `next_frontend/src/components/QuizComponent.jsx`
- **Notes Component:** `next_frontend/src/components/NotesComponent.jsx`

---

## 💻 API Endpoints Quick Reference

### Quiz Endpoints
```bash
# List quizzes
GET /api/quiz/

# Get quiz for video
GET /api/quiz/video/{video_id}/

# Start quiz attempt
POST /api/quiz/attempts/start_quiz/
Body: {"quiz_id": 1}

# Submit answer
POST /api/quiz/attempts/{attempt_id}/submit_answer/
Body: {"question_id": 1, "answer": "A"}

# Submit quiz
POST /api/quiz/attempts/{attempt_id}/submit_quiz/

# Get my attempts
GET /api/quiz/attempts/my_attempts/
```

### Notes Endpoints
```bash
# List notes
GET /api/notes/

# Get notes for video
GET /api/notes/video/{video_id}/

# Get sections
GET /api/notes/{notes_id}/sections/

# Add bookmark
POST /api/notes/bookmarks/add_bookmark/
Body: {"notes_id": 1, "section_id": 1, "title": "Bookmark"}

# Track progress
POST /api/notes/progress/track_progress/
Body: {"notes_id": 1, "section_id": 1, "progress_percentage": 50}

# Get my progress
GET /api/notes/progress/my_progress/
```

---

## 🎨 Frontend Integration

### Add to Video Page
```jsx
import QuizComponent from '@/components/QuizComponent';
import NotesComponent from '@/components/NotesComponent';

export default function VideoPage({ params }) {
  const videoId = params.videoId;
  
  return (
    <div>
      <h1>Video Player Here</h1>
      
      {/* Quiz Section */}
      <QuizComponent videoId={videoId} />
      
      {/* Notes Section */}
      <NotesComponent videoId={videoId} />
    </div>
  );
}
```

---

## 🗂️ Database Models Summary

### Quiz Model Hierarchy
```
Quiz
├── QuizQuestion (multiple per quiz)
│   └── UserQuizAnswer (multiple answers per question)
├── UserQuizAttempt (multiple attempts per user)
└── (tracks overall attempt info)
```

### Notes Model Hierarchy
```
VideoNotes
├── NoteSection (multiple per notes)
├── NoteBookmark (user bookmarks)
└── UserNoteProgress (tracks user progress)
```

---

## 🔑 Key Features

### Quiz
✅ Multiple question types (MCQ, True/False, Short Answer, Essay)
✅ Auto-grading
✅ Attempt limiting
✅ Score tracking
✅ Result review

### Notes
✅ Organized sections
✅ Bookmarking
✅ Progress tracking
✅ Key takeaways
✅ Important terms

---

## 🐛 Troubleshooting

### Migration Issues
```bash
# Reset and retry
python manage.py migrate quiz zero
python manage.py migrate notes zero
python manage.py migrate
```

### CORS Errors
- Already configured in `settings.py`
- Allowed: localhost:3000, 8080, 5173

### API Not Working
- Check auth token in localStorage
- Verify API_BASE_URL in `client.js`
- Check Django server is running

### Component Not Showing
- Verify quiz/notes exist for video
- Check browser console
- Ensure video_id is correct

---

## 📊 Admin Panel Quick Tour

### Quiz Admin
- View/Create/Edit/Delete quizzes
- Manage questions inline
- Monitor user attempts
- View scores and results

### Notes Admin
- View/Create/Edit/Delete notes
- Manage sections inline
- Track user bookmarks
- Monitor progress

### Access
- URL: http://localhost:8000/admin
- Requires superuser login

---

## 🧪 Testing Quick Commands

### Get Auth Token
```bash
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_user", "password": "your_pass"}'
```

### Test Quiz API
```bash
TOKEN="your_token_here"

# List quizzes
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/quiz/

# Get quiz for video 1
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/quiz/video/1/
```

### Test Notes API
```bash
# List notes
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/notes/

# Get notes for video 1
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/notes/video/1/
```

---

## 📖 Documentation Files

| File | Purpose |
|------|---------|
| IMPLEMENTATION_SUMMARY.md | Overview and architecture |
| QUIZ_AND_NOTES_FEATURES.md | Complete API documentation |
| SETUP_GUIDE.md | Installation and setup |
| TEST_EXAMPLES.md | Testing guide and examples |
| This file | Quick reference |

---

## 🎯 Common Tasks

### Create a Quiz via Admin
1. Go to Admin > Quiz > Add Quiz
2. Select video
3. Enter title and description
4. Add questions inline
5. Save

### Create Notes via Admin
1. Go to Admin > Video Notes > Add
2. Select video
3. Enter title and content
4. Add key takeaways
5. Add sections inline
6. Save

### Generate Sample Data
```bash
# Quiz
python manage.py generate_quiz 1

# Notes
python manage.py generate_notes 1
```

### View User Results
1. Go to Admin > User Quiz Attempt
2. Filter by user or quiz
3. Click to view detailed results
4. View individual answers and scores

---

## 🚨 Common Issues

| Issue | Fix |
|-------|-----|
| "Not found" on quiz/notes | Ensure quiz/notes exist for video |
| 401 Unauthorized | Login and get valid token |
| CORS error | Check allowed origins in settings |
| Component blank | Check browser console for errors |
| No questions showing | Create questions in admin first |

---

## 🔐 Security Reminders

✅ Token-based authentication on all endpoints
✅ Permission checks on create/update/delete
✅ Instructor-only create permissions
✅ Owner-only edit/delete permissions
✅ CORS configured for frontend domains

---

## 📈 Scalability

- Efficient database queries
- Indexed foreign keys
- Pagination support
- Async-ready architecture
- Ready for production deployment

---

## 🔄 Development Workflow

1. Create quiz/notes in admin
2. Test API endpoints with curl/Postman
3. Integrate components in frontend
4. Test user workflows
5. Customize styling as needed

---

## 💡 Tips & Tricks

### Bulk Operations
- Use management commands for quick setup
- Admin inline editing for rapid changes

### Testing
- Use curl for quick endpoint testing
- Browser DevTools Network tab for frontend debugging

### Performance
- Cache quiz questions in frontend
- Use pagination on list endpoints

### Debugging
- Check Django logs for backend errors
- Check browser console for frontend errors
- Use admin panel to verify data

---

## 🎓 Learning Resources

- Django Docs: https://docs.djangoproject.com/
- DRF Docs: https://www.django-rest-framework.org/
- React Docs: https://react.dev/
- Next.js Docs: https://nextjs.org/docs

---

## 📞 Quick Help

### For Setup Issues
→ See SETUP_GUIDE.md

### For API Questions
→ See QUIZ_AND_NOTES_FEATURES.md

### For Testing
→ See TEST_EXAMPLES.md

### For Architecture
→ See IMPLEMENTATION_SUMMARY.md

---

## ✅ Pre-Launch Checklist

- [ ] Migrations completed
- [ ] Sample data generated
- [ ] Django server running
- [ ] Frontend server running
- [ ] Components integrated
- [ ] Admin panel works
- [ ] API endpoints tested
- [ ] Frontend components render
- [ ] Quiz flow tested
- [ ] Notes flow tested
- [ ] Error handling verified
- [ ] Styling customized

---

## 🚀 Next Steps

1. Complete pre-launch checklist ↑
2. Customize styling
3. Add more sample data
4. Test with real users
5. Implement AI features (optional)
6. Deploy to production

---

**Version:** 1.0 | **Last Updated:** April 2026
