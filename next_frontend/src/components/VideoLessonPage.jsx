'use client';

import { useState, useEffect } from 'react';
import QuizComponent from './QuizComponent';
import NotesComponent from './NotesComponent';

export default function VideoLessonPage({ videoId, videoData, defaultTab = 'notes' }) {
    const [activeTab, setActiveTab] = useState(defaultTab); // 'notes', 'quiz'
    const [error, setError] = useState(null);

    if (error) {
        return <div className="text-red-500 p-4">{error}</div>;
    }

    return (
        <div className="max-w-7xl mx-auto p-4">
            {/* Video Player Section */}
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
                        ></iframe>
                    </div>
                </div>

                {/* Video Information */}
                <div className="mt-4">
                    <h1 className="text-3xl font-bold mb-2">{videoData?.title}</h1>
                    <p className="text-gray-600">{videoData?.description}</p>
                    {videoData?.duration && (
                        <p className="text-sm text-gray-500 mt-2">Duration: {videoData.duration} minutes</p>
                    )}
                </div>
            </div>

            {/* Tabs Navigation */}
            <div className="mb-6 border-b border-gray-200">
                <div className="flex gap-8">
                    <button
                        onClick={() => setActiveTab('notes')}
                        className={`py-3 px-4 font-medium transition-colors ${activeTab === 'notes'
                            ? 'border-b-2 border-blue-600 text-blue-600'
                            : 'text-gray-600 hover:text-gray-900'
                            }`}
                    >
                        <span className="text-lg">📝</span> Notes
                    </button>
                    <button
                        onClick={() => setActiveTab('quiz')}
                        className={`py-3 px-4 font-medium transition-colors ${activeTab === 'quiz'
                            ? 'border-b-2 border-blue-600 text-blue-600'
                            : 'text-gray-600 hover:text-gray-900'
                            }`}
                    >
                        <span className="text-lg">📋</span> Quiz
                    </button>
                </div>
            </div>

            {/* Content Sections */}
            <div className="bg-white rounded-lg shadow-md p-6">
                {/* Notes Tab */}
                {activeTab === 'notes' && (
                    <div className="animate-fadeIn">
                        <NotesComponent videoId={videoId} />
                    </div>
                )}

                {/* Quiz Tab */}
                {activeTab === 'quiz' && (
                    <div className="animate-fadeIn">
                        <QuizComponent videoId={videoId} />
                    </div>
                )}
            </div>

            {/* Course Progress Summary */}
            <div className="mt-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="text-center">
                        <div className="text-3xl font-bold text-blue-600">📚</div>
                        <p className="text-sm text-gray-600 mt-2">Learning Material Available</p>
                    </div>
                    <div className="text-center">
                        <div className="text-3xl font-bold text-blue-600">✅</div>
                        <p className="text-sm text-gray-600 mt-2">Review & Practice</p>
                    </div>
                    <div className="text-center">
                        <div className="text-3xl font-bold text-blue-600">🎯</div>
                        <p className="text-sm text-gray-600 mt-2">Test Your Knowledge</p>
                    </div>
                </div>
            </div>
        </div>
    );
}
