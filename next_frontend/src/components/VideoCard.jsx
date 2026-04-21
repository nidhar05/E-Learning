'use client';

import { useState, useEffect } from 'react';
import api from '@/api/client';

export default function VideoCard({ video, onViewDetails }) {
    const [hasQuiz, setHasQuiz] = useState(false);
    const [hasNotes, setHasNotes] = useState(false);
    const [quizStats, setQuizStats] = useState(null);
    const [notesStats, setNotesStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        checkAvailableContent();
    }, [video.id]);

    const checkAvailableContent = async () => {
        try {
            // Check for quiz
            try {
                const quizResponse = await api.get(`quiz/video/${video.id}/`);
                setHasQuiz(true);

                // Fetch quiz stats
                const attemptsResponse = await api.get('quiz/attempts/my_attempts/');
                const attempts = attemptsResponse.data.filter(a => a.quiz === quizResponse.data.id);
                if (attempts.length > 0) {
                    const latestAttempt = attempts[0];
                    setQuizStats({
                        attempts: attempts.length,
                        score: latestAttempt.score,
                        passed: latestAttempt.is_passed
                    });
                }
            } catch (err) {
                setHasQuiz(false);
            }

            // Check for notes
            try {
                const notesResponse = await api.get(`notes/video/${video.id}/`);
                setHasNotes(true);

                // Fetch notes progress
                const progressResponse = await api.get('notes/progress/my_progress/');
                const progress = progressResponse.data.find(p => p.notes === notesResponse.data.id);
                if (progress) {
                    setNotesStats({
                        progress: progress.progress_percentage,
                        completed: progress.is_completed
                    });
                }
            } catch (err) {
                setHasNotes(false);
            }
        } catch (err) {
            console.error('Failed to check content:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleQuizClick = () => {
        onViewDetails?.('quiz', video.id);
    };

    const handleNotesClick = () => {
        onViewDetails?.('notes', video.id);
    };

    return (
        <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-200">
            {/* Video Thumbnail Placeholder */}
            <div className="relative bg-gradient-to-br from-gray-700 to-gray-900 h-40 flex items-center justify-center group cursor-pointer">
                <div className="text-white text-center">
                    <div className="text-5xl mb-2">🎬</div>
                    <p className="text-sm font-medium opacity-75">Video Content</p>
                    {video.duration && (
                        <p className="text-xs opacity-50">⏱️ {video.duration} min</p>
                    )}
                </div>
                <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all flex items-center justify-center opacity-0 group-hover:opacity-100">
                    <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-full flex items-center gap-2">
                        ▶️ Watch
                    </button>
                </div>
            </div>

            {/* Video Info */}
            <div className="p-4">
                <h3 className="font-bold text-lg mb-2 line-clamp-2">{video.title}</h3>

                {/* Status Badge */}
                <div className="mb-4 flex flex-wrap gap-2">
                    {loading ? (
                        <span className="px-2 py-1 bg-gray-200 text-gray-700 text-xs rounded">Loading...</span>
                    ) : (
                        <>
                            {hasQuiz && (
                                <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded font-medium">
                                    📋 Quiz Available
                                </span>
                            )}
                            {hasNotes && (
                                <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded font-medium">
                                    📝 Notes Available
                                </span>
                            )}
                            {!hasQuiz && !hasNotes && (
                                <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                                    No content yet
                                </span>
                            )}
                        </>
                    )}
                </div>

                {/* Stats */}
                {!loading && (
                    <div className="mb-4 space-y-2 text-sm">
                        {quizStats && (
                            <div className="flex items-center justify-between">
                                <span className="text-gray-600">Quiz Attempts:</span>
                                <span className="font-semibold">
                                    {quizStats.attempts}x
                                    {quizStats.passed && (
                                        <span className="ml-2 text-green-600">✅ Passed</span>
                                    )}
                                </span>
                            </div>
                        )}
                        {notesStats && (
                            <div className="flex items-center justify-between">
                                <span className="text-gray-600">Notes Progress:</span>
                                <span className="font-semibold">{notesStats.progress.toFixed(0)}%</span>
                            </div>
                        )}
                    </div>
                )}

                {/* Action Buttons */}
                <div className="grid grid-cols-2 gap-2">
                    <button
                        onClick={handleNotesClick}
                        className={`py-2 px-3 rounded-lg font-medium text-sm transition-colors ${hasNotes
                                ? 'bg-green-100 text-green-700 hover:bg-green-200'
                                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            }`}
                        disabled={!hasNotes}
                    >
                        📝 Notes
                    </button>
                    <button
                        onClick={handleQuizClick}
                        className={`py-2 px-3 rounded-lg font-medium text-sm transition-colors ${hasQuiz
                                ? 'bg-purple-100 text-purple-700 hover:bg-purple-200'
                                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            }`}
                        disabled={!hasQuiz}
                    >
                        📋 Quiz
                    </button>
                </div>
            </div>
        </div>
    );
}
