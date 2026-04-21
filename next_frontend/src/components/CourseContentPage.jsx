'use client';

import { useState, useEffect } from 'react';
import api from '@/api/client';
import VideoLessonPage from './VideoLessonPage';

export default function CourseContentPage({ courseId }) {
    const [videos, setVideos] = useState([]);
    const [selectedVideoId, setSelectedVideoId] = useState(null);
    const [selectedVideo, setSelectedVideo] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [courseInfo, setCourseInfo] = useState(null);

    useEffect(() => {
        fetchCourseData();
    }, [courseId]);

    const fetchCourseData = async () => {
        try {
            setLoading(true);
            // Fetch course info
            const courseResponse = await api.get(`courses/${courseId}/`);
            setCourseInfo(courseResponse.data);

            // Fetch videos for this course
            const videosResponse = await api.get(`videos/?course_id=${courseId}`);
            setVideos(videosResponse.data);

            // Set first video as selected
            if (videosResponse.data.length > 0) {
                setSelectedVideoId(videosResponse.data[0].id);
                setSelectedVideo(videosResponse.data[0]);
            }
        } catch (err) {
            setError('Failed to load course content');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleVideoSelect = (video) => {
        setSelectedVideoId(video.id);
        setSelectedVideo(video);
    };

    if (loading) {
        return <div className="flex items-center justify-center p-8">Loading course content...</div>;
    }

    if (error) {
        return <div className="text-red-500 p-4">{error}</div>;
    }

    return (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 p-4">
            {/* Sidebar - Course Content List */}
            <div className="lg:col-span-1">
                <div className="sticky top-4 bg-white rounded-lg shadow-md p-4">
                    <h2 className="text-xl font-bold mb-4">Course Content</h2>

                    {courseInfo && (
                        <div className="mb-4 pb-4 border-b">
                            <h3 className="font-semibold text-gray-700">{courseInfo.title}</h3>
                            <p className="text-sm text-gray-500 mt-1">{videos.length} Videos</p>
                        </div>
                    )}

                    <div className="space-y-2 max-h-96 overflow-y-auto">
                        {videos.map((video, index) => (
                            <button
                                key={video.id}
                                onClick={() => handleVideoSelect(video)}
                                className={`w-full text-left p-3 rounded-lg transition-all duration-200 ${selectedVideoId === video.id
                                        ? 'bg-blue-600 text-white shadow-md'
                                        : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                    }`}
                            >
                                <div className="flex items-start gap-3">
                                    <span className="text-lg flex-shrink-0">
                                        {selectedVideoId === video.id ? '▶️' : '📹'}
                                    </span>
                                    <div className="flex-1 min-w-0">
                                        <p className="font-medium text-sm truncate">
                                            {index + 1}. {video.title}
                                        </p>
                                        <p className={`text-xs mt-1 ${selectedVideoId === video.id ? 'text-blue-100' : 'text-gray-500'
                                            }`}>
                                            ⏱️ {video.duration} mins
                                        </p>
                                    </div>
                                </div>
                            </button>
                        ))}
                    </div>

                    {videos.length === 0 && (
                        <p className="text-gray-500 text-sm text-center py-8">
                            No videos available
                        </p>
                    )}
                </div>
            </div>

            {/* Main Content - Video Lesson */}
            <div className="lg:col-span-3">
                {selectedVideo ? (
                    <VideoLessonPage
                        videoId={selectedVideoId}
                        videoData={selectedVideo}
                    />
                ) : (
                    <div className="bg-gray-50 rounded-lg p-8 text-center">
                        <p className="text-gray-500 text-lg">Select a video to get started</p>
                    </div>
                )}
            </div>
        </div>
    );
}
