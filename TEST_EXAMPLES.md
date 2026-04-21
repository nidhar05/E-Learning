# Test Examples - Quiz and Notes Features

This file contains examples for testing the Quiz and Notes features.

## Prerequisites

- Django development server running
- Authentication token (get by logging in)
- Sample video created
- Generated quiz and notes for the video

## Getting Authentication Token

### Using cURL

```bash
curl -X POST http://localhost:8000/api/users/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

### Using Python

```python
import requests

response = requests.post(
    'http://localhost:8000/api/users/login/',
    json={'username': 'your_username', 'password': 'your_password'}
)
token = response.json()['access']
print(f"Token: {token}")
```

---

## Quiz Testing

### Test 1: List All Quizzes

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/quiz/
```

**Expected Response:**
```json
[
  {
    "id": 1,
    "title": "Python Basics Quiz",
    "description": "Test your Python knowledge",
    "passing_score": 70,
    "max_attempts": 3,
    "question_count": 5,
    "is_published": true,
    "generated_at": "2024-04-20T10:30:00Z"
  }
]
```

### Test 2: Get Quiz for Specific Video

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/quiz/video/1/
```

**Expected Response:**
```json
{
  "id": 1,
  "title": "Python Basics Quiz",
  "description": "Test your Python knowledge",
  "passing_score": 70,
  "time_limit": null,
  "max_attempts": 3,
  "is_published": true,
  "questions": [
    {
      "id": 1,
      "question_type": "multiple_choice",
      "question_text": "What is Python?",
      "option_a": "A programming language",
      "option_b": "A snake",
      "option_c": "A website",
      "option_d": "A game",
      "explanation": "Python is a programming language",
      "order": 1,
      "points": 1
    }
  ],
  "generated_at": "2024-04-20T10:30:00Z"
}
```

### Test 3: Start Quiz Attempt

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"quiz_id": 1}' \
  http://localhost:8000/api/quiz/attempts/start_quiz/
```

**Expected Response:**
```json
{
  "id": 1,
  "quiz": 1,
  "quiz_title": "Python Basics Quiz",
  "attempt_number": 1,
  "start_time": "2024-04-20T10:35:00Z",
  "end_time": null,
  "score": null,
  "total_points": null,
  "earned_points": null,
  "is_passed": false,
  "status": "in_progress",
  "answers": []
}
```

### Test 4: Submit Answer to Question

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question_id": 1, "answer": "A"}' \
  http://localhost:8000/api/quiz/attempts/1/submit_answer/
```

**Expected Response:**
```json
{
  "status": "Answer recorded",
  "question_id": 1
}
```

### Test 5: Submit Quiz for Grading

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/quiz/attempts/1/submit_quiz/
```

**Expected Response:**
```json
{
  "id": 1,
  "quiz": 1,
  "quiz_title": "Python Basics Quiz",
  "attempt_number": 1,
  "start_time": "2024-04-20T10:35:00Z",
  "end_time": "2024-04-20T10:45:00Z",
  "score": 80.0,
  "total_points": 5,
  "earned_points": 4,
  "is_passed": true,
  "status": "graded",
  "answers": [
    {
      "id": 1,
      "question": 1,
      "question_text": "What is Python?",
      "user_answer": "A",
      "correct_answer": "A",
      "is_correct": true,
      "points_earned": 1
    }
  ]
}
```

### Test 6: Get User Quiz Attempts

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/quiz/attempts/my_attempts/
```

**Expected Response:**
```json
[
  {
    "id": 1,
    "quiz": 1,
    "quiz_title": "Python Basics Quiz",
    "attempt_number": 1,
    "start_time": "2024-04-20T10:35:00Z",
    "end_time": "2024-04-20T10:45:00Z",
    "score": 80.0,
    "is_passed": true,
    "status": "graded"
  }
]
```

---

## Notes Testing

### Test 1: List All Notes

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/notes/
```

**Expected Response:**
```json
[
  {
    "id": 1,
    "video": 1,
    "video_title": "Python Basics",
    "title": "Python Basics Notes",
    "is_ai_generated": true,
    "is_published": true,
    "section_count": 3,
    "created_at": "2024-04-20T10:30:00Z",
    "updated_at": "2024-04-20T10:30:00Z"
  }
]
```

### Test 2: Get Notes for Specific Video

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/notes/video/1/
```

**Expected Response:**
```json
{
  "id": 1,
  "video": 1,
  "video_title": "Python Basics",
  "title": "Python Basics Notes",
  "content": "# Python Basics\n\nPython is a powerful programming language...",
  "key_takeaways": "- Easy to learn\n- Widely used\n- Great community",
  "important_terms": "- Variable\n- Function\n- Loop",
  "is_ai_generated": true,
  "is_published": true,
  "created_by": 1,
  "created_by_username": "instructor",
  "sections": [
    {
      "id": 1,
      "title": "Introduction",
      "content": "# Introduction\n\nWelcome to Python basics...",
      "order": 1,
      "icon": "📌",
      "created_at": "2024-04-20T10:30:00Z",
      "updated_at": "2024-04-20T10:30:00Z"
    }
  ],
  "created_at": "2024-04-20T10:30:00Z",
  "updated_at": "2024-04-20T10:30:00Z"
}
```

### Test 3: Get Note Sections

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/notes/1/sections/
```

**Expected Response:**
```json
[
  {
    "id": 1,
    "title": "Introduction",
    "content": "# Introduction\n\nWelcome to Python basics...",
    "order": 1,
    "icon": "📌",
    "created_at": "2024-04-20T10:30:00Z",
    "updated_at": "2024-04-20T10:30:00Z"
  },
  {
    "id": 2,
    "title": "Main Concepts",
    "content": "# Main Concepts\n\nKey concepts in Python...",
    "order": 2,
    "icon": "💡",
    "created_at": "2024-04-20T10:30:00Z",
    "updated_at": "2024-04-20T10:30:00Z"
  }
]
```

### Test 4: Add Bookmark

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notes_id": 1, "section_id": 1, "title": "Important Section"}' \
  http://localhost:8000/api/notes/bookmarks/add_bookmark/
```

**Expected Response:**
```json
{
  "id": 1,
  "notes": 1,
  "section": 1,
  "title": "Important Section",
  "timestamp": null,
  "created_at": "2024-04-20T10:35:00Z"
}
```

### Test 5: Get My Bookmarks

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/notes/bookmarks/my_bookmarks/
```

**Expected Response:**
```json
[
  {
    "id": 1,
    "notes": 1,
    "section": 1,
    "title": "Important Section",
    "timestamp": null,
    "created_at": "2024-04-20T10:35:00Z"
  }
]
```

### Test 6: Track Progress

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notes_id": 1, "section_id": 1, "progress_percentage": 50}' \
  http://localhost:8000/api/notes/progress/track_progress/
```

**Expected Response:**
```json
{
  "id": 1,
  "notes": 1,
  "notes_title": "Python Basics Notes",
  "sections_read": 0,
  "last_read_section": 1,
  "last_read_section_title": "Introduction",
  "progress_percentage": 50.0,
  "is_completed": false,
  "first_accessed": "2024-04-20T10:35:00Z",
  "last_accessed": "2024-04-20T10:35:00Z"
}
```

### Test 7: Mark Section Read

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"notes_id": 1, "section_id": 1}' \
  http://localhost:8000/api/notes/progress/mark_section_read/
```

**Expected Response:**
```json
{
  "id": 1,
  "notes": 1,
  "notes_title": "Python Basics Notes",
  "sections_read": 1,
  "last_read_section": 1,
  "last_read_section_title": "Introduction",
  "progress_percentage": 33.33,
  "is_completed": false,
  "first_accessed": "2024-04-20T10:35:00Z",
  "last_accessed": "2024-04-20T10:35:00Z"
}
```

### Test 8: Get My Progress

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/notes/progress/my_progress/
```

**Expected Response:**
```json
[
  {
    "id": 1,
    "notes": 1,
    "notes_title": "Python Basics Notes",
    "sections_read": 2,
    "last_read_section": 2,
    "last_read_section_title": "Main Concepts",
    "progress_percentage": 66.67,
    "is_completed": false,
    "first_accessed": "2024-04-20T10:35:00Z",
    "last_accessed": "2024-04-20T10:35:00Z"
  }
]
```

---

## Error Testing

### Test 1: Unauthorized Request (No Token)

```bash
curl http://localhost:8000/api/quiz/
```

**Expected Response (401):**
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### Test 2: Invalid Quiz ID

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/quiz/999/
```

**Expected Response (404):**
```json
{
  "detail": "Not found."
}
```

### Test 3: Exceeded Max Attempts

```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"quiz_id": 1}' \
  http://localhost:8000/api/quiz/attempts/start_quiz/
```

**After 3 attempts, Expected Response (400):**
```json
{
  "detail": "You have reached the maximum number of attempts (3)"
}
```

---

## Python Testing Script

```python
import requests
import json

BASE_URL = "http://localhost:8000/api"
USERNAME = "your_username"
PASSWORD = "your_password"
VIDEO_ID = 1

class QuizNotesClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.token = self.login(username, password)
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def login(self, username, password):
        response = requests.post(
            f"{self.base_url}/users/login/",
            json={"username": username, "password": password}
        )
        return response.json()['access']
    
    def get_quizzes(self):
        response = requests.get(
            f"{self.base_url}/quiz/",
            headers=self.headers
        )
        return response.json()
    
    def get_quiz_for_video(self, video_id):
        response = requests.get(
            f"{self.base_url}/quiz/video/{video_id}/",
            headers=self.headers
        )
        return response.json()
    
    def start_quiz(self, quiz_id):
        response = requests.post(
            f"{self.base_url}/quiz/attempts/start_quiz/",
            headers=self.headers,
            json={"quiz_id": quiz_id}
        )
        return response.json()
    
    def submit_answer(self, attempt_id, question_id, answer):
        response = requests.post(
            f"{self.base_url}/quiz/attempts/{attempt_id}/submit_answer/",
            headers=self.headers,
            json={"question_id": question_id, "answer": answer}
        )
        return response.json()
    
    def submit_quiz(self, attempt_id):
        response = requests.post(
            f"{self.base_url}/quiz/attempts/{attempt_id}/submit_quiz/",
            headers=self.headers
        )
        return response.json()
    
    def get_notes_for_video(self, video_id):
        response = requests.get(
            f"{self.base_url}/notes/video/{video_id}/",
            headers=self.headers
        )
        return response.json()
    
    def add_bookmark(self, notes_id, section_id, title):
        response = requests.post(
            f"{self.base_url}/notes/bookmarks/add_bookmark/",
            headers=self.headers,
            json={
                "notes_id": notes_id,
                "section_id": section_id,
                "title": title
            }
        )
        return response.json()
    
    def track_progress(self, notes_id, section_id, percentage):
        response = requests.post(
            f"{self.base_url}/notes/progress/track_progress/",
            headers=self.headers,
            json={
                "notes_id": notes_id,
                "section_id": section_id,
                "progress_percentage": percentage
            }
        )
        return response.json()

# Usage Example
if __name__ == "__main__":
    client = QuizNotesClient(BASE_URL, USERNAME, PASSWORD)
    
    # Test quiz
    print("=== QUIZ TESTS ===")
    quizzes = client.get_quizzes()
    print(f"All quizzes: {json.dumps(quizzes[:1], indent=2)}")
    
    quiz = client.get_quiz_for_video(VIDEO_ID)
    print(f"Quiz for video {VIDEO_ID}: {json.dumps(quiz, indent=2)}")
    
    attempt = client.start_quiz(quiz['id'])
    print(f"Quiz attempt started: {attempt['id']}")
    
    # Submit answers
    for question in quiz['questions']:
        if question['question_type'] == 'multiple_choice':
            answer = 'A'
        else:
            answer = 'True'
        
        result = client.submit_answer(attempt['id'], question['id'], answer)
        print(f"Answer submitted: {result}")
    
    # Submit quiz
    result = client.submit_quiz(attempt['id'])
    print(f"Quiz submitted - Score: {result['score']}%")
    
    # Test notes
    print("\n=== NOTES TESTS ===")
    notes = client.get_notes_for_video(VIDEO_ID)
    print(f"Notes for video {VIDEO_ID}: {json.dumps(notes, indent=2)[:200]}...")
    
    if notes.get('sections'):
        section = notes['sections'][0]
        bookmark = client.add_bookmark(notes['id'], section['id'], "Test Bookmark")
        print(f"Bookmark added: {bookmark}")
        
        progress = client.track_progress(notes['id'], section['id'], 50)
        print(f"Progress tracked: {progress['progress_percentage']}%")
```

---

## Automated Testing with pytest

```python
# tests/test_quiz.py
import pytest
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from videos.models import Video
from courses.models import Course
from quiz.models import Quiz, QuizQuestion

User = get_user_model()

class QuizAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass',
            role='student'
        )
        self.instructor = User.objects.create_user(
            username='instructor',
            password='instpass',
            role='instructor'
        )
        self.course = Course.objects.create(
            instructor=self.instructor,
            title='Test Course',
            description='Test'
        )
        self.video = Video.objects.create(
            course=self.course,
            title='Test Video',
            duration=300,
            order=1
        )
        self.quiz = Quiz.objects.create(
            video=self.video,
            title='Test Quiz'
        )
        QuizQuestion.objects.create(
            quiz=self.quiz,
            question_type='multiple_choice',
            question_text='Test?',
            option_a='A',
            option_b='B',
            correct_answer='A'
        )
    
    def test_list_quizzes(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/quiz/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
    
    def test_start_quiz_attempt(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            '/api/quiz/attempts/start_quiz/',
            {'quiz_id': self.quiz.id}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['status'], 'in_progress')
```

---

## Manual Testing Checklist

- [ ] Create quiz via admin panel
- [ ] Create notes via admin panel
- [ ] Start quiz attempt
- [ ] Submit MCQ answer
- [ ] Submit True/False answer
- [ ] Submit short answer
- [ ] Submit essay answer
- [ ] Submit quiz and check grading
- [ ] View results and review answers
- [ ] Verify score calculation
- [ ] Exceed max attempts error
- [ ] Add bookmark to notes
- [ ] Track progress through notes
- [ ] Mark section as read
- [ ] 403 error on unauthorized edits
- [ ] 401 error without token
- [ ] 404 error for non-existent quiz
- [ ] Verify admin panel functions
