'use client';

import { useState, useEffect } from 'react';
import api from '@/api/client';

export default function QuizComponent({ videoId }) {
    const [quiz, setQuiz] = useState(null);
    const [currentAttempt, setCurrentAttempt] = useState(null);
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [answers, setAnswers] = useState({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [submitted, setSubmitted] = useState(false);
    const [result, setResult] = useState(null);

    useEffect(() => {
        fetchQuiz();
    }, [videoId]);

    const fetchQuiz = async () => {
        try {
            setLoading(true);
            const response = await api.get(`quiz/video/${videoId}/`);
            setQuiz(response.data);
        } catch (err) {
            setError('Failed to load quiz');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const startQuiz = async () => {
        try {
            setLoading(true);
            const response = await api.post('quiz/attempts/start_quiz/', {
                quiz_id: quiz.id,
            });
            setCurrentAttempt(response.data);
            setAnswers({});
            setCurrentQuestionIndex(0);
            setSubmitted(false);
        } catch (err) {
            setError('Failed to start quiz');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const handleAnswerChange = (questionId, answer) => {
        setAnswers({
            ...answers,
            [questionId]: answer,
        });
    };

    const handleSubmitAnswer = async (questionId, answer) => {
        try {
            await api.post(`quiz/attempts/${currentAttempt.id}/submit_answer/`, {
                question_id: questionId,
                answer: answer,
            });
        } catch (err) {
            console.error('Failed to submit answer:', err);
        }
    };

    const handleNextQuestion = async () => {
        const currentQuestion = quiz.questions[currentQuestionIndex];
        if (answers[currentQuestion.id]) {
            await handleSubmitAnswer(currentQuestion.id, answers[currentQuestion.id]);
        }

        if (currentQuestionIndex < quiz.questions.length - 1) {
            setCurrentQuestionIndex(currentQuestionIndex + 1);
        }
    };

    const handlePreviousQuestion = () => {
        if (currentQuestionIndex > 0) {
            setCurrentQuestionIndex(currentQuestionIndex - 1);
        }
    };

    const handleSubmitQuiz = async () => {
        try {
            setLoading(true);
            const response = await api.post(
                `quiz/attempts/${currentAttempt.id}/submit_quiz/`,
                {}
            );
            setResult(response.data);
            setSubmitted(true);
        } catch (err) {
            setError('Failed to submit quiz');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    if (loading && !quiz) {
        return <div className="flex items-center justify-center p-8">Loading quiz...</div>;
    }

    if (error) {
        return <div className="text-red-500 p-4">{error}</div>;
    }

    if (!quiz) {
        return <div className="p-4">No quiz available for this video.</div>;
    }

    if (!currentAttempt) {
        return (
            <div className="p-6 bg-white rounded-lg shadow">
                <h2 className="text-2xl font-bold mb-4">{quiz.title}</h2>
                {quiz.description && <p className="mb-4 text-gray-600">{quiz.description}</p>}
                <div className="bg-blue-50 p-4 rounded mb-6">
                    <p className="mb-2">
                        <strong>Questions:</strong> {quiz.question_count}
                    </p>
                    <p className="mb-2">
                        <strong>Passing Score:</strong> {quiz.passing_score}%
                    </p>
                    {quiz.time_limit && (
                        <p className="mb-2">
                            <strong>Time Limit:</strong> {quiz.time_limit} minutes
                        </p>
                    )}
                    <p>
                        <strong>Attempts Allowed:</strong> {quiz.max_attempts}
                    </p>
                </div>
                <button
                    onClick={startQuiz}
                    disabled={loading}
                    className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
                >
                    Start Quiz
                </button>
            </div>
        );
    }

    if (submitted && result) {
        return (
            <div className="p-6 bg-white rounded-lg shadow">
                <h2 className="text-2xl font-bold mb-4">Quiz Completed!</h2>
                <div className={`p-4 rounded mb-6 ${result.is_passed ? 'bg-green-100' : 'bg-red-100'}`}>
                    <p className="text-lg font-bold mb-2">
                        {result.is_passed ? '✓ PASSED' : '✗ FAILED'}
                    </p>
                    <p className="text-xl font-bold">
                        Score: {result.score?.toFixed(2)}%
                    </p>
                    <p className="text-sm mt-2">
                        Points: {result.earned_points} / {result.total_points}
                    </p>
                </div>

                <div className="mb-6">
                    <h3 className="text-lg font-bold mb-4">Review Answers</h3>
                    {result.answers?.map((answer, idx) => (
                        <div key={idx} className="mb-4 p-4 border rounded">
                            <p className="font-bold mb-2">Q{idx + 1}: {answer.question_text}</p>
                            <p className="mb-2">
                                <span className={answer.is_correct ? 'text-green-600' : 'text-red-600'}>
                                    Your Answer: {answer.user_answer}
                                </span>
                            </p>
                            {!answer.is_correct && (
                                <p className="text-green-600">Correct Answer: {answer.correct_answer}</p>
                            )}
                            <p className="text-sm text-gray-600 mt-2">
                                Points: {answer.points_earned}
                            </p>
                        </div>
                    ))}
                </div>

                <button
                    onClick={() => {
                        setCurrentAttempt(null);
                        setSubmitted(false);
                        setResult(null);
                    }}
                    className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
                >
                    Back to Quiz
                </button>
            </div>
        );
    }

    const currentQuestion = quiz.questions[currentQuestionIndex];

    return (
        <div className="p-6 bg-white rounded-lg shadow">
            <div className="mb-6">
                <h2 className="text-2xl font-bold mb-2">{quiz.title}</h2>
                <p className="text-gray-600">
                    Question {currentQuestionIndex + 1} of {quiz.questions.length}
                </p>
            </div>

            <div className="mb-8 w-full bg-gray-200 rounded-full h-2">
                <div
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{
                        width: `${((currentQuestionIndex + 1) / quiz.questions.length) * 100}%`,
                    }}
                ></div>
            </div>

            <div className="mb-8">
                <h3 className="text-lg font-bold mb-4">{currentQuestion.question_text}</h3>

                {currentQuestion.question_type === 'multiple_choice' && (
                    <div className="space-y-3">
                        {['A', 'B', 'C', 'D'].map((option) => {
                            const value = currentQuestion[`option_${option.toLowerCase()}`];
                            if (!value) return null;

                            const isSelected = answers[currentQuestion.id] === option;

                            return (
                                <label key={option} style={{
                                    display: 'flex',
                                    alignItems: 'flex-start',
                                    padding: '1rem',
                                    border: isSelected ? '2px solid var(--accent-primary)' : '2px solid var(--border-light)',
                                    borderRadius: '8px',
                                    cursor: 'pointer',
                                    backgroundColor: isSelected ? 'rgba(249, 115, 22, 0.05)' : 'transparent',
                                    transition: 'all 0.2s',
                                    marginBottom: '0.75rem'
                                }}
                                    onMouseEnter={(e) => {
                                        if (!isSelected) {
                                            e.currentTarget.style.borderColor = 'var(--text-muted)';
                                            e.currentTarget.style.backgroundColor = 'var(--bg-primary)';
                                        }
                                    }}
                                    onMouseLeave={(e) => {
                                        if (!isSelected) {
                                            e.currentTarget.style.borderColor = 'var(--border-light)';
                                            e.currentTarget.style.backgroundColor = 'transparent';
                                        }
                                    }}>
                                    <input
                                        type="radio"
                                        name={`question-${currentQuestion.id}`}
                                        value={option}
                                        checked={isSelected}
                                        onChange={(e) =>
                                            handleAnswerChange(currentQuestion.id, e.target.value)
                                        }
                                        style={{
                                            marginRight: '1rem',
                                            marginTop: '0.2rem',
                                            cursor: 'pointer'
                                        }}
                                    />
                                    <div style={{ flex: 1 }}>
                                        <strong style={{ color: 'var(--accent-primary)', fontSize: '1.1rem' }}>
                                            {option}:
                                        </strong>
                                        <p style={{ marginTop: '0.25rem', color: 'var(--text-main)' }}>
                                            {value}
                                        </p>
                                    </div>
                                </label>
                            );
                        })}
                    </div>
                )}

                {currentQuestion.question_type === 'true_false' && (
                    <div className="space-y-3">
                        {['True', 'False'].map((option) => (
                            <label key={option} className="flex items-center p-3 border rounded cursor-pointer hover:bg-gray-50">
                                <input
                                    type="radio"
                                    name={`question-${currentQuestion.id}`}
                                    value={option}
                                    checked={answers[currentQuestion.id] === option}
                                    onChange={(e) =>
                                        handleAnswerChange(currentQuestion.id, e.target.value)
                                    }
                                    className="mr-3"
                                />
                                <span>{option}</span>
                            </label>
                        ))}
                    </div>
                )}

                {(currentQuestion.question_type === 'short_answer' ||
                    currentQuestion.question_type === 'essay') && (
                        <textarea
                            value={answers[currentQuestion.id] || ''}
                            onChange={(e) =>
                                handleAnswerChange(currentQuestion.id, e.target.value)
                            }
                            className="w-full p-3 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
                            rows={currentQuestion.question_type === 'essay' ? 6 : 3}
                            placeholder="Enter your answer..."
                        />
                    )}
            </div>

            <div className="flex justify-between items-center">
                <button
                    onClick={handlePreviousQuestion}
                    disabled={currentQuestionIndex === 0}
                    className="px-6 py-2 border rounded hover:bg-gray-100 disabled:bg-gray-100 disabled:cursor-not-allowed"
                >
                    Previous
                </button>

                <span className="text-sm text-gray-600">
                    {currentQuestionIndex + 1} / {quiz.questions.length}
                </span>

                {currentQuestionIndex === quiz.questions.length - 1 ? (
                    <button
                        onClick={handleSubmitQuiz}
                        disabled={loading}
                        className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 disabled:bg-gray-400"
                    >
                        {loading ? 'Submitting...' : 'Submit Quiz'}
                    </button>
                ) : (
                    <button
                        onClick={handleNextQuestion}
                        disabled={!answers[currentQuestion.id]}
                        className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
                    >
                        Next
                    </button>
                )}
            </div>
        </div>
    );
}
