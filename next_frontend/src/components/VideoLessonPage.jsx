'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import QuizComponent from './QuizComponent';

export default function VideoLessonPage({ videoId, videoData, defaultTab = 'quiz' }) {
    const [activeTab, setActiveTab] = useState(defaultTab); // 'quiz'
    const [error, setError] = useState(null);
    const { user } = useAuth();
    const canAccessQuiz = user?.role === 'student';

    useEffect(() => {
        if (!canAccessQuiz && activeTab === 'quiz') {
            setActiveTab('quiz');
        }
    }, [canAccessQuiz, activeTab]);

    if (error) {
        return <div className="text-red-500 p-4">{error}</div>;
    }

    return (
        <div className="max-w-7xl mx-auto p-4">
            <div className="mb-8">
                <div className="bg-gray-100 rounded-lg overflow-hidden shadow-lg">
                    <div className="aspect-video bg-black flex items-center justify-center">
                        <iframe
                            width="100%"
                            height="100%"
                            src={`${videoData?.videoUrl || 'about:blank'}`}
                            title={videoData?.title || 'Video Player'}
                            frameBorder="0"
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                            allowFullScreen
                            className="w-full h-full"
                        />
                    </div>
                </div>

                <div className="mt-4">
                    <h1 className="text-3xl font-bold mb-2">{videoData?.title}</h1>
                    <p className="text-gray-600">{videoData?.description}</p>
                    {videoData?.duration && (
                        <p className="text-sm text-gray-500 mt-2">Duration: {videoData.duration} minutes</p>
                    )}
                </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
                {canAccessQuiz ? (
                    <div className="animate-fadeIn">
                        <QuizComponent videoId={videoId} />
                    </div>
                ) : (
                    <div className="rounded-lg border border-slate-200 bg-slate-50 p-5 text-slate-700">
                        Quiz is available only for students.
                    </div>
                )}
            </div>
        </div>
    );
}
