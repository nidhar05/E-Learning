'use client';

import { useEffect, useState } from 'react';
import api from '@/api/client';
const OPTION_KEYS = ['A', 'B', 'C', 'D'];

const getErrorMessage = (err, fallback) => {
    const data = err?.response?.data;
    if (!data) {
        return fallback;
    }

    if (typeof data === 'string') {
        return data;
    }

    if (typeof data.detail === 'string') {
        return data.detail;
    }

    const firstEntry = Object.entries(data)[0];
    if (firstEntry && Array.isArray(firstEntry[1]) && firstEntry[1].length > 0) {
        return String(firstEntry[1][0]);
    }

    if (firstEntry && typeof firstEntry[1] === 'string') {
        return String(firstEntry[1]);
    }

    return fallback;
};

const logUnexpectedError = (err) => {
    // Avoid noisy Next.js dev overlay for expected 4xx API validation errors.
    if (!err?.response) {
        console.error(err);
    }
};

const getQuestionOptionText = (question, optionKey) => {
    if (!question || !optionKey) {
        return '';
    }
    return question[`option_${optionKey.toLowerCase()}`] || '';
};

const getResolvedAnswerLabel = (question, optionKey) => {
    if (!optionKey) {
        return 'Not answered';
    }
    const optionText = getQuestionOptionText(question, optionKey);
    return optionText ? `${optionKey}. ${optionText}` : optionKey;
};

export default function QuizComponent({ videoId, hasCaptions = true }) {
    const [quiz, setQuiz] = useState(null);
    const [currentAttempt, setCurrentAttempt] = useState(null);
    const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
    const [answers, setAnswers] = useState({});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [submitted, setSubmitted] = useState(false);
    const [result, setResult] = useState(null);

    useEffect(() => {
        if (!hasCaptions) {
            setQuiz(null);
            setCurrentAttempt(null);
            setAnswers({});
            setCurrentQuestionIndex(0);
            setSubmitted(false);
            setResult(null);
            setError(null);
            return;
        }
        fetchQuiz();
    }, [videoId, hasCaptions]);

    useEffect(() => {
        if (!hasCaptions) {
            return undefined;
        }
        if (!quiz?.id || (quiz.questions && quiz.questions.length > 0)) {
            return undefined;
        }

        const retryTimer = setTimeout(() => {
            fetchQuiz();
        }, 5000);

        return () => clearTimeout(retryTimer);
    }, [quiz, videoId, hasCaptions]);

    const fetchQuiz = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await api.get(`quiz/video/${videoId}/`);
            setQuiz(response.data);
        } catch (err) {
            setError(getErrorMessage(err, 'Failed to load quiz.'));
            logUnexpectedError(err);
        } finally {
            setLoading(false);
        }
    };

    const startQuiz = async () => {
        if (!quiz?.id) {
            return;
        }

        try {
            setLoading(true);
            setError(null);
            const response = await api.post('quiz/attempts/start_quiz/', {
                quiz_id: quiz.id,
            });
            setCurrentAttempt(response.data);
            setAnswers({});
            setCurrentQuestionIndex(0);
            setSubmitted(false);
        } catch (err) {
            setError(getErrorMessage(err, 'Failed to start quiz.'));
            logUnexpectedError(err);
        } finally {
            setLoading(false);
        }
    };

    const handleAnswerChange = (questionId, answer) => {
        setAnswers((prev) => ({
            ...prev,
            [questionId]: answer,
        }));
    };

    const submitSingleAnswer = async (questionId, answer) => {
        if (!currentAttempt?.id || !questionId || !answer) {
            return;
        }

        await api.post(`quiz/attempts/${currentAttempt.id}/submit_answer/`, {
            question_id: questionId,
            answer,
        });
    };

    const handleNextQuestion = async () => {
        const currentQuestion = quiz.questions[currentQuestionIndex];
        if (!currentQuestion) {
            return;
        }

        try {
            if (answers[currentQuestion.id]) {
                await submitSingleAnswer(currentQuestion.id, answers[currentQuestion.id]);
            }
            if (currentQuestionIndex < quiz.questions.length - 1) {
                setCurrentQuestionIndex((idx) => idx + 1);
            }
        } catch (err) {
            const message = getErrorMessage(err, 'Failed to save your answer.');
            if (message.includes('Please restart the quiz')) {
                await fetchQuiz();
                setCurrentAttempt(null);
                setAnswers({});
                setCurrentQuestionIndex(0);
                setSubmitted(false);
            }
            setError(message);
            logUnexpectedError(err);
        }
    };

    const handlePreviousQuestion = () => {
        if (currentQuestionIndex > 0) {
            setCurrentQuestionIndex((idx) => idx - 1);
        }
    };

    const handleSubmitQuiz = async () => {
        if (!currentAttempt?.id) {
            return;
        }

        try {
            setLoading(true);
            setError(null);

            // Ensure the current question answer is sent before final submission.
            const currentQuestion = quiz.questions[currentQuestionIndex];
            if (currentQuestion && answers[currentQuestion.id]) {
                await submitSingleAnswer(currentQuestion.id, answers[currentQuestion.id]);
            }

            // Ensure every selected local answer has been posted.
            for (const question of quiz.questions) {
                const selected = answers[question.id];
                if (selected) {
                    await submitSingleAnswer(question.id, selected);
                }
            }

            const response = await api.post(`quiz/attempts/${currentAttempt.id}/submit_quiz/`, {});
            setResult(response.data);
            setSubmitted(true);
        } catch (err) {
            const message = getErrorMessage(err, 'Failed to submit quiz.');
            if (message.includes('Please restart the quiz')) {
                await fetchQuiz();
                setCurrentAttempt(null);
                setAnswers({});
                setCurrentQuestionIndex(0);
                setSubmitted(false);
                setResult(null);
            }
            setError(message);
            logUnexpectedError(err);
        } finally {
            setLoading(false);
        }
    };

    if (loading && !quiz) {
        return <div className="flex items-center justify-center p-8">Loading quiz...</div>;
    }

    if (!hasCaptions) {
        return (
            <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4 text-amber-800">
                quiz is not added
            </div>
        );
    }

    if (error) {
        return (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-rose-700">
                {error}
            </div>
        );
    }

    if (!quiz) {
        return <div className="p-4">quiz is not added</div>;
    }

    if (!quiz.questions || quiz.questions.length === 0) {
        return (
            <div className="p-6 bg-white rounded-lg shadow">
                <h2 className="text-2xl font-bold mb-4">{quiz.title}</h2>
                <p className="mb-4 text-gray-600">
                    quiz is not added
                </p>
            </div>
        );
    }

    if (!currentAttempt) {
        return (
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
                <h2 className="text-2xl font-bold text-slate-900 mb-2">{quiz.title}</h2>
                <div className="mb-6 space-y-1 text-slate-700">
                    <p className="text-base">
                        <span className="font-semibold text-slate-900">Questions:</span> {quiz.question_count ?? quiz.questions.length}
                    </p>
                    <p className="text-base">
                        <span className="font-semibold text-slate-900">Passing Score:</span> {quiz.passing_score}%
                    </p>
                </div>
                <button
                    onClick={startQuiz}
                    disabled={loading}
                    className="rounded-xl bg-orange-600 text-white px-6 py-2.5 font-semibold hover:bg-orange-700 disabled:bg-gray-400"
                >
                    Start Quiz
                </button>
            </div>
        );
    }

    if (submitted && result) {
        const questionLookup = Object.fromEntries(
            (quiz.questions || []).map((question) => [question.id, question])
        );

        return (
            <div className="p-6 bg-white rounded-lg shadow">
                <h2 className="text-2xl font-bold mb-4">Quiz Completed</h2>
                <div className={`p-4 rounded mb-6 ${result.is_passed ? 'bg-green-100' : 'bg-red-100'}`}>
                    <p className="text-lg font-bold mb-2">
                        {result.is_passed ? 'PASSED' : 'NOT PASSED'}
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
                            {(() => {
                                const question = questionLookup[answer.question];
                                const userLabel = getResolvedAnswerLabel(question, answer.user_answer);
                                const correctLabel = getResolvedAnswerLabel(question, answer.correct_answer);

                                return (
                                    <>
                            <p className="font-bold mb-2">Q{idx + 1}: {answer.question_text}</p>
                            <p className="mb-2">
                                <span className={answer.is_correct ? 'text-green-600' : 'text-red-600'}>
                                    Your Answer: {userLabel}
                                </span>
                            </p>
                            {!answer.is_correct && (
                                <p className="text-green-600">Correct Answer: {correctLabel}</p>
                            )}
                            <p className="text-sm text-gray-600 mt-2">
                                Points: {answer.points_earned}
                            </p>
                                    </>
                                );
                            })()}
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
                />
            </div>

            <div className="mb-8">
                <h3 className="text-lg font-bold mb-4">{currentQuestion.question_text}</h3>

                {currentQuestion.question_type === 'multiple_choice' && (
                    <div
                        style={{
                            display: 'flex',
                            flexDirection: 'column',
                            gap: '0.5rem',
                            width: '100%',
                        }}
                    >
                        {OPTION_KEYS.map((option) => {
                            const value = getQuestionOptionText(currentQuestion, option);
                            if (!value) return null;

                            const isSelected = answers[currentQuestion.id] === option;

                            return (
                                <label
                                    key={option}
                                    style={{
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '0.35rem',
                                        width: '100%',
                                        padding: '0.45rem 0.6rem',
                                        borderRadius: '0.75rem',
                                        border: isSelected ? '1px solid #f97316' : '1px solid #e2e8f0',
                                        backgroundColor: isSelected ? '#fff7ed' : '#ffffff',
                                        cursor: 'pointer',
                                        textAlign: 'left',
                                    }}
                                >
                                    <input
                                        type="radio"
                                        name={`question-${currentQuestion.id}`}
                                        value={option}
                                        checked={isSelected}
                                        onChange={(e) =>
                                            handleAnswerChange(currentQuestion.id, e.target.value)
                                        }
                                        style={{
                                            width: 'auto',
                                            margin: 0,
                                            flexShrink: 0,
                                            accentColor: '#ea580c',
                                        }}
                                    />
                                    <span
                                        style={{
                                            flex: 1,
                                            fontSize: '0.95rem',
                                            color: '#1e293b',
                                            lineHeight: 1.35,
                                        }}
                                    >
                                        <span style={{ fontWeight: 700, color: '#0f172a' }}>{option}.</span>{' '}
                                        {value}
                                    </span>
                                </label>
                            );
                        })}
                    </div>
                )}
            </div>

            <div
                style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginTop: '0.5rem',
                }}
            >
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
                        disabled={loading || !answers[currentQuestion.id]}
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
