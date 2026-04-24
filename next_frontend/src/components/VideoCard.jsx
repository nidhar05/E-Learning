'use client';

import { useState, useEffect } from 'react';
import api from '@/api/client';

export default function VideoCard({ video, onViewDetails }) {
    const [hasQuiz, setHasQuiz] = useState(false);
    const [quizStats, setQuizStats] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        checkAvailableContent();
    }, [video.id]);

    const checkAvailableContent = async () => {
        try {
            const quizResponse = await api.get(`quiz/video/${video.id}/`);
            setHasQuiz(true);

            const attemptsResponse = await api.get('quiz/attempts/my_attempts/');
            const attempts = attemptsResponse.data.filter((attempt) => attempt.quiz === quizResponse.data.id);
            if (attempts.length > 0) {
                const latestAttempt = attempts[0];
                setQuizStats({
                    attempts: attempts.length,
                    score: latestAttempt.score,
                    passed: latestAttempt.is_passed,
                });
            }
        } catch (err) {
            setHasQuiz(false);
        } finally {
            setLoading(false);
        }
    };

    const handleQuizClick = () => {
        onViewDetails?.('quiz', video.id);
    };

    return (
        <div className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-200">
            <div className="relative bg-gradient-to-br from-gray-700 to-gray-900 h-40 flex items-center justify-center group cursor-pointer">
                <div className="text-white text-center">
                    <div className="text-5xl mb-2">VIDEO</div>
                    <p className="text-sm font-medium opacity-75">Video Content</p>
                    {video.duration && (
                        <p className="text-xs opacity-50">{video.duration} min</p>
                    )}
                </div>
            </div>

            <div className="p-4">
                <h3 className="font-bold text-lg mb-2 line-clamp-2">{video.title}</h3>

                <div className="mb-4 flex flex-wrap gap-2">
                    {loading ? (
                        <span className="px-2 py-1 bg-gray-200 text-gray-700 text-xs rounded">Loading...</span>
                    ) : (
                        <>
                            {hasQuiz && (
                                <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded font-medium">
                                    Quiz Available
                                </span>
                            )}
                            {!hasQuiz && (
                                <span className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded">
                                    No quiz yet
                                </span>
                            )}
                        </>
                    )}
                </div>

                {!loading && quizStats && (
                    <div className="mb-4 space-y-2 text-sm">
                        <div className="flex items-center justify-between">
                            <span className="text-gray-600">Quiz Attempts:</span>
                            <span className="font-semibold">
                                {quizStats.attempts}x
                                {quizStats.passed && (
                                    <span className="ml-2 text-green-600">Passed</span>
                                )}
                            </span>
                        </div>
                    </div>
                )}

                <div className="grid grid-cols-1 gap-2">
                    <button
                        onClick={handleQuizClick}
                        className={`py-2 px-3 rounded-lg font-medium text-sm transition-colors ${
                            hasQuiz
                                ? 'bg-purple-100 text-purple-700 hover:bg-purple-200'
                                : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        }`}
                        disabled={!hasQuiz}
                    >
                        Quiz
                    </button>
                </div>
            </div>
        </div>
    );
}
