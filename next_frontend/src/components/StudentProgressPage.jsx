'use client';

import { useState, useEffect } from 'react';
import api from '@/api/client';
import VideoCard from './VideoCard';
import VideoLessonPage from './VideoLessonPage';

export default function StudentProgressPage({ courseId }) {
    const [videos, setVideos] = useState([]);
    const [courseInfo, setCourseInfo] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedView, setSelectedView] = useState(null); // { type: 'lesson', videoId }
    const [selectedVideos, setSelectedVideos] = useState([]);

    useEffect(() => {
        fetchCourseData();
    }, [courseId]);

    const fetchCourseData = async () => {
        try {
            setLoading(true);
            const courseResponse = await api.get(`courses/${courseId}/`);
            setCourseInfo(courseResponse.data);

            const videosResponse = await api.get(`videos/?course_id=${courseId}`);
            setVideos(videosResponse.data);
            setSelectedVideos(videosResponse.data);
        } catch (err) {
            setError('Failed to load course');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleViewDetails = (type, videoId) => {
        if (type !== 'lesson') {
            return;
        }
        setSelectedView({ type, videoId });
    };

    const handleGoBack = () => {
        setSelectedView(null);
    };

    const getVideoData = (videoId) => videos.find((video) => video.id === videoId);

    if (loading) {
        return (
            <div className="flex items-center justify-center min-h-screen">
                <div className="text-center">
                    <p className="text-gray-600">Loading course content...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-4 bg-red-50 text-red-600 rounded-lg">
                {error}
            </div>
        );
    }

    if (selectedView) {
        const video = getVideoData(selectedView.videoId);
        return (
            <div>
                <button
                    onClick={handleGoBack}
                    className="mb-4 px-4 py-2 text-blue-600 hover:text-blue-700 font-medium flex items-center gap-2"
                >
                    Back to Course
                </button>

                {selectedView.type === 'lesson' && video && (
                    <div>
                        <h2 className="text-2xl font-bold mb-4">{video.title}</h2>
                        <VideoLessonPage
                            videoData={video}
                        />
                    </div>
                )}
            </div>
        );
    }

    return (
        <div className="p-6 bg-gradient-to-br from-blue-50 to-indigo-50 min-h-screen">
            <div className="mb-8">
                <h1 className="text-4xl font-bold text-gray-900 mb-2">
                    {courseInfo?.title || 'Course Content'}
                </h1>
                <p className="text-gray-600">
                    Browse and open lesson videos.
                </p>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6 mb-8">
                <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold text-gray-700">Course Progress</h3>
                    <span className="text-sm font-bold text-blue-600">
                        {videos.length > 0 ? Math.round((videos.length / videos.length) * 100) : 0}% Complete
                    </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                    <div className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-500" style={{ width: '100%' }} />
                </div>
                <p className="text-sm text-gray-600 mt-3">
                    {videos.length} videos available
                </p>
            </div>

            <div className="space-y-6">
                <h2 className="text-2xl font-bold text-gray-900">Video Lessons</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {selectedVideos.map((video) => (
                        <VideoCard
                            key={video.id}
                            video={video}
                            onViewDetails={handleViewDetails}
                        />
                    ))}
                </div>
            </div>
        </div>
    );
}
