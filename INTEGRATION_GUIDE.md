# Integration Guide - Quiz & Notes on Student Progress Page

## Overview

The new components allow you to display quiz and notes for each video on your student progress page with:
- 🎬 Video player integration
- 📝 Study notes with sections
- 📋 Interactive quizzes
- 📊 Progress tracking
- 🎯 Attempt history

---

## Components Created

### 1. **StudentProgressPage** 
Main page showing all videos with quiz/notes access
- `src/components/StudentProgressPage.jsx`
- Displays videos in a grid with progress tracking
- Links to full video lesson pages

### 2. **VideoCard**
Individual video card component
- `src/components/VideoCard.jsx`
- Shows video info and quick access buttons
- Displays quiz/notes status and user progress

### 3. **VideoLessonPage** (Updated)
Full video lesson view with tabs
- `src/components/VideoLessonPage.jsx`
- Tabbed interface (Notes/Quiz)
- Supports switching between content types

### 4. **CourseContentPage**
Sidebar-based course navigation
- `src/components/CourseContentPage.jsx`
- Video list sidebar
- Main content area for lessons

---

## Implementation Options

### Option 1: Replace Entire Course Page (Recommended)

Use `StudentProgressPage` to replace your whole course viewing experience:

```jsx
// app/course/[courseId]/page.jsx
'use client';

import StudentProgressPage from '@/components/StudentProgressPage';

export default function CoursePage({ params }) {
  return <StudentProgressPage courseId={params.courseId} />;
}
```

### Option 2: Use on Dashboard

Display on a dashboard or progress overview page:

```jsx
// app/dashboard/page.jsx
'use client';

import StudentProgressPage from '@/components/StudentProgressPage';

export default function Dashboard() {
  const courseId = 1; // Get from context or params
  return (
    <div>
      <h1>My Courses</h1>
      <StudentProgressPage courseId={courseId} />
    </div>
  );
}
```

### Option 3: Two-Column Layout

Use `CourseContentPage` for sidebar navigation:

```jsx
// app/course/[courseId]/lessons/page.jsx
'use client';

import CourseContentPage from '@/components/CourseContentPage';

export default function LessonsPage({ params }) {
  return <CourseContentPage courseId={params.courseId} />;
}
```

### Option 4: Individual Video Modal

Show VideoLessonPage in a modal:

```jsx
'use client';

import { useState } from 'react';
import VideoCard from '@/components/VideoCard';
import VideoLessonPage from '@/components/VideoLessonPage';

export default function VideosWithModal({ videos, courseId }) {
  const [selectedVideo, setSelectedVideo] = useState(null);

  return (
    <div>
      <div className="grid grid-cols-3 gap-4">
        {videos.map(video => (
          <VideoCard
            key={video.id}
            video={video}
            onViewDetails={(type, videoId) => {
              const video = videos.find(v => v.id === videoId);
              setSelectedVideo({ video, type });
            }}
          />
        ))}
      </div>

      {/* Modal */}
      {selectedVideo && (
        <Modal onClose={() => setSelectedVideo(null)}>
          <VideoLessonPage
            videoId={selectedVideo.video.id}
            videoData={selectedVideo.video}
            defaultTab={selectedVideo.type}
          />
        </Modal>
      )}
    </div>
  );
}
```

---

## Component Hierarchy

```
StudentProgressPage
└── VideoCard (for each video)
    ├── Quiz/Notes stats
    └── Quick action buttons
        ├── When clicked → VideoLessonPage with Quiz tab
        └── When clicked → VideoLessonPage with Notes tab

VideoLessonPage
├── Video player
├── Tab navigation
├── Tabs:
│   ├── Notes Tab → NotesComponent
│   └── Quiz Tab → QuizComponent
└── Course progress summary

CourseContentPage
├── Sidebar (video list)
└── Main content (VideoLessonPage)
```

---

## API Calls Made

### StudentProgressPage
```
GET /api/courses/{courseId}/         - Get course info
GET /api/videos/?course_id={id}      - Get all videos
```

### VideoCard
```
GET /api/quiz/video/{videoId}/       - Check if quiz exists
GET /api/quiz/attempts/my_attempts/  - Get user's quiz attempts
GET /api/notes/video/{videoId}/      - Check if notes exist
GET /api/notes/progress/my_progress/ - Get user's notes progress
```

### VideoLessonPage
```
Uses QuizComponent and NotesComponent
Which call their respective APIs
```

---

## Usage Examples

### Display Progress Page
```jsx
import StudentProgressPage from '@/components/StudentProgressPage';

export default function StudentProgress() {
  return <StudentProgressPage courseId={1} />;
}
```

### Get Just Video Cards
```jsx
import VideoCard from '@/components/VideoCard';

export default function VideoList({ videos }) {
  return (
    <div className="grid grid-cols-3 gap-4">
      {videos.map(video => (
        <VideoCard 
          key={video.id} 
          video={video}
          onViewDetails={(type, videoId) => {
            console.log(`${type} for video ${videoId}`);
          }}
        />
      ))}
    </div>
  );
}
```

### Show Specific Video Lesson
```jsx
import VideoLessonPage from '@/components/VideoLessonPage';

export default function SingleLesson() {
  const videoData = {
    id: 1,
    title: 'Python Basics',
    description: 'Learn the basics of Python',
    duration: 45,
    videoUrl: 'https://example.com/video.mp4'
  };

  return (
    <VideoLessonPage 
      videoId={1}
      videoData={videoData}
      defaultTab="notes"
    />
  );
}
```

---

## Styling Customization

All components use Tailwind CSS. Customize by:

### Change Primary Color
Replace `blue-600` with your color:
```jsx
// In components, replace:
className="bg-blue-600" // → className="bg-purple-600"
```

### Change Component Spacing
Modify padding/margins:
```jsx
<div className="p-6"> // → <div className="p-8">
<div className="gap-6"> // → <div className="gap-8">
```

### Add Custom Theme
```jsx
const theme = {
  primary: 'blue-600',
  secondary: 'purple-600',
  success: 'green-600',
};

// Use throughout components
className={`bg-${theme.primary}`}
```

---

## Features

### StudentProgressPage Features
✅ Course header with title and description
✅ Overall progress bar
✅ Statistics cards (videos, quizzes, notes)
✅ Video grid with cards
✅ Click to view full lesson
✅ Back button to grid view
✅ Help section at bottom

### VideoCard Features
✅ Video duration display
✅ Status badges (Quiz/Notes available)
✅ User stats (attempts, progress)
✅ Quick action buttons
✅ Disabled state for missing content
✅ Hover effects

### VideoLessonPage Features
✅ Video player integration
✅ Video information display
✅ Tab navigation (Notes/Quiz)
✅ Dynamic content switching
✅ Progress summary cards

### QuizComponent Features
✅ Multiple question types
✅ Progress indicator
✅ Auto-grading
✅ Result review
✅ Score display

### NotesComponent Features
✅ Section navigation
✅ Progress tracking
✅ Bookmarking system
✅ Key takeaways display

---

## Error Handling

Components handle these scenarios:

### No Quiz/Notes Available
```
✅ Shows "Not available" state
✅ Disables buttons
✅ Displays message
```

### API Errors
```
✅ Shows error message
✅ Retry options available
✅ Graceful degradation
```

### Failed to Load
```
✅ Loading state shown
✅ Error component displayed
✅ User can refresh
```

---

## Database Requirements

Quiz and Notes must be created first:

```bash
# Create sample quiz and notes
python manage.py generate_quiz 1
python manage.py generate_notes 1

# Or via admin panel
http://localhost:8000/admin/
```

---

## Next Steps

1. **Choose Implementation Option** from section above
2. **Create the route/page** that uses the component
3. **Replace video player element** with actual player if needed
4. **Customize styling** to match your brand
5. **Test with sample data** generated via management command
6. **Deploy to production**

---

## Troubleshooting

### Components Not Showing
- Check if quiz/notes exist for video
- Verify API endpoints are working
- Check browser console for errors

### Styling Issues
- Ensure Tailwind CSS is configured
- Check CSS imports
- Clear browser cache

### Data Not Loading
- Verify courseId is correct
- Check API response in Network tab
- Ensure user is authenticated

### Quiz/Notes Buttons Disabled
- Generate quiz: `python manage.py generate_quiz <videoId>`
- Generate notes: `python manage.py generate_notes <videoId>`
- Check Django admin to verify creation

---

## File Locations

```
src/components/
├── StudentProgressPage.jsx      ← Main page for course
├── VideoCard.jsx                ← Individual video card
├── VideoLessonPage.jsx          ← Full lesson view
├── CourseContentPage.jsx        ← Sidebar layout
├── QuizComponent.jsx            ← Quiz functionality
└── NotesComponent.jsx           ← Notes functionality
```

---

## Complete Example

```jsx
// app/course/[courseId]/page.jsx
'use client';

import { useParams } from 'next/navigation';
import StudentProgressPage from '@/components/StudentProgressPage';

export default function CoursePage() {
  const { courseId } = useParams();
  
  return (
    <div className="min-h-screen bg-gray-50">
      <StudentProgressPage courseId={parseInt(courseId)} />
    </div>
  );
}
```

---

**Ready to integrate!** Choose your implementation option and start using the new quiz and notes components. 🚀
