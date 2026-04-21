'use client';

import { useState, useEffect } from 'react';
import api from '@/api/client';

export default function NotesComponent({ videoId }) {
    const [notes, setNotes] = useState(null);
    const [userProgress, setUserProgress] = useState(null);
    const [activeSection, setActiveSection] = useState(null);
    const [bookmarks, setBookmarks] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchNotes();
        fetchUserProgress();
    }, [videoId]);

    const fetchNotes = async () => {
        try {
            setLoading(true);
            const response = await api.get(`notes/video/${videoId}/`);
            setNotes(response.data);
            if (response.data.sections.length > 0) {
                setActiveSection(response.data.sections[0]);
            }
        } catch (err) {
            setError('Failed to load notes');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const fetchUserProgress = async () => {
        try {
            const response = await api.get('notes/progress/my_progress/');
            setUserProgress(response.data);
        } catch (err) {
            console.error('Failed to load progress:', err);
        }
    };

    const handleSectionClick = async (section) => {
        setActiveSection(section);
        await markSectionRead(section);
    };

    const markSectionRead = async (section) => {
        try {
            await api.post('notes/progress/mark_section_read/', {
                notes_id: notes.id,
                section_id: section.id,
            });
            fetchUserProgress();
        } catch (err) {
            console.error('Failed to mark section as read:', err);
        }
    };

    const addBookmark = async (section, title) => {
        try {
            await api.post('notes/bookmarks/add_bookmark/', {
                notes_id: notes.id,
                section_id: section.id,
                title: title || section.title,
            });
            // Refresh bookmarks
            const response = await api.get('notes/bookmarks/my_bookmarks/');
            setBookmarks(response.data);
        } catch (err) {
            console.error('Failed to add bookmark:', err);
        }
    };

    if (loading) {
        return <div className="flex items-center justify-center p-8">Loading notes...</div>;
    }

    if (error) {
        return <div className="text-red-500 p-4">{error}</div>;
    }

    if (!notes) {
        return <div className="p-4">No notes available for this video.</div>;
    }

    const notesProgress =
        userProgress?.find((p) => p.notes === notes.id) || null;

    return (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Sidebar - Sections List */}
            <div className="lg:col-span-1">
                <div className="sticky top-4">
                    <h3 className="text-lg font-bold mb-4">Sections</h3>

                    {notesProgress && (
                        <div className="bg-blue-50 p-3 rounded mb-4 text-sm">
                            <p className="font-bold">Progress</p>
                            <div className="w-full bg-gray-200 rounded-full h-2 mt-2 mb-1">
                                <div
                                    className="bg-blue-600 h-2 rounded-full transition-all"
                                    style={{ width: `${notesProgress.progress_percentage}%` }}
                                ></div>
                            </div>
                            <p className="text-xs text-gray-600 mt-1">
                                {notesProgress.progress_percentage.toFixed(0)}% complete
                            </p>
                        </div>
                    )}

                    <div className="space-y-2 max-h-96 overflow-y-auto">
                        {notes.sections.map((section) => (
                            <button
                                key={section.id}
                                onClick={() => handleSectionClick(section)}
                                className={`w-full text-left p-3 rounded transition-colors ${activeSection?.id === section.id
                                        ? 'bg-blue-600 text-white'
                                        : 'bg-gray-100 hover:bg-gray-200'
                                    }`}
                            >
                                <div className="flex items-start gap-2">
                                    {section.icon && <span className="text-lg">{section.icon}</span>}
                                    <span className="text-sm font-medium flex-1 break-words">
                                        {section.title}
                                    </span>
                                </div>
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Main Content - Section Details */}
            <div className="lg:col-span-3">
                <div className="bg-white p-6 rounded-lg shadow">
                    {/* Header */}
                    <div className="mb-6 border-b pb-4">
                        <h1 className="text-3xl font-bold mb-2">{notes.title}</h1>
                        <div className="flex items-center gap-4 text-sm text-gray-600">
                            <span>
                                {notes.is_ai_generated ? '🤖 AI-Generated' : '👤 Instructor-Created'}
                            </span>
                            <span>Created: {new Date(notes.created_at).toLocaleDateString()}</span>
                        </div>
                    </div>

                    {/* Overview Section */}
                    {activeSection === null && (
                        <div>
                            <h2 className="text-2xl font-bold mb-4">Notes Overview</h2>

                            {notes.key_takeaways && (
                                <div className="mb-6 p-4 bg-yellow-50 rounded border-l-4 border-yellow-400">
                                    <h3 className="font-bold mb-2 text-lg">Key Takeaways</h3>
                                    <div className="prose prose-sm max-w-none">
                                        {notes.key_takeaways}
                                    </div>
                                </div>
                            )}

                            {notes.important_terms && (
                                <div className="mb-6 p-4 bg-purple-50 rounded border-l-4 border-purple-400">
                                    <h3 className="font-bold mb-2 text-lg">Important Terms</h3>
                                    <div className="prose prose-sm max-w-none">
                                        {notes.important_terms}
                                    </div>
                                </div>
                            )}

                            {notes.content && (
                                <div className="p-4 bg-gray-50 rounded">
                                    <h3 className="font-bold mb-2 text-lg">Main Content</h3>
                                    <div className="prose prose-sm max-w-none">
                                        {notes.content}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Active Section Content */}
                    {activeSection && (
                        <div>
                            <div className="flex items-center justify-between mb-4">
                                <h2 className="text-2xl font-bold">{activeSection.title}</h2>
                                <button
                                    onClick={() => addBookmark(activeSection, activeSection.title)}
                                    className="px-4 py-2 text-sm bg-yellow-100 hover:bg-yellow-200 rounded flex items-center gap-2"
                                >
                                    ⭐ Bookmark
                                </button>
                            </div>

                            <div className="prose prose-sm mt-4 mb-6 max-w-none">
                                {activeSection.content}
                            </div>

                            {/* Navigation Buttons */}
                            <div className="flex justify-between gap-4 pt-6 border-t">
                                <button
                                    onClick={() => {
                                        const currentIndex = notes.sections.findIndex(
                                            (s) => s.id === activeSection.id
                                        );
                                        if (currentIndex > 0) {
                                            handleSectionClick(notes.sections[currentIndex - 1]);
                                        }
                                    }}
                                    disabled={notes.sections[0].id === activeSection.id}
                                    className="px-6 py-2 border rounded hover:bg-gray-100 disabled:bg-gray-100 disabled:cursor-not-allowed"
                                >
                                    ← Previous Section
                                </button>

                                <span className="text-sm text-gray-600 self-center">
                                    Section {notes.sections.findIndex((s) => s.id === activeSection.id) + 1} of{' '}
                                    {notes.sections.length}
                                </span>

                                <button
                                    onClick={() => {
                                        const currentIndex = notes.sections.findIndex(
                                            (s) => s.id === activeSection.id
                                        );
                                        if (currentIndex < notes.sections.length - 1) {
                                            handleSectionClick(notes.sections[currentIndex + 1]);
                                        }
                                    }}
                                    disabled={
                                        notes.sections[notes.sections.length - 1].id === activeSection.id
                                    }
                                    className="px-6 py-2 border rounded hover:bg-gray-100 disabled:bg-gray-100 disabled:cursor-not-allowed"
                                >
                                    Next Section →
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
