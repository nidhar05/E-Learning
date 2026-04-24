'use client';

import { useEffect, useMemo, useState } from 'react';
import { BookOpen, Bookmark, CheckCircle2, GraduationCap, Lightbulb, Sparkles } from 'lucide-react';
import api from '@/api/client';

const splitLines = (value) =>
    (value || '')
        .split('\n')
        .map((item) => item.trim())
        .filter(Boolean);

const stripBullet = (value) => value.replace(/^[-*]\s*/, '').trim();

const SECTION_ACCENTS = {
    'Lesson Summary': 'from-sky-50 to-cyan-50 border-sky-100',
    'Learning Objectives': 'from-indigo-50 to-blue-50 border-indigo-100',
    'Core Concepts Explained': 'from-amber-50 to-orange-50 border-amber-100',
    'Important Terms': 'from-violet-50 to-purple-50 border-violet-100',
    'Practical Rules': 'from-emerald-50 to-teal-50 border-emerald-100',
    'Practical Examples From Lesson': 'from-rose-50 to-pink-50 border-rose-100',
    'Interview Preparation Points': 'from-lime-50 to-emerald-50 border-lime-100',
    'Interview Questions To Practice': 'from-yellow-50 to-amber-50 border-yellow-100',
    'Revision Checklist': 'from-slate-50 to-zinc-50 border-slate-200',
};

const parseGlossary = (value) =>
    splitLines(value)
        .map((line) => stripBullet(line))
        .map((line) => {
            const separatorIndex = line.indexOf(':');
            if (separatorIndex === -1) {
                return null;
            }

            return {
                term: line.slice(0, separatorIndex).trim(),
                definition: line.slice(separatorIndex + 1).trim(),
            };
        })
        .filter(Boolean);

const parseStructuredContent = (content) => {
    const lines = splitLines(content);
    const blocks = [];
    let currentSection = null;

    lines.forEach((line) => {
        if (line.startsWith('## ')) {
            if (currentSection) {
                blocks.push(currentSection);
            }
            currentSection = {
                heading: line.replace(/^##\s+/, '').trim(),
                items: [],
                paragraphs: [],
            };
            return;
        }

        if (!currentSection) {
            currentSection = {
                heading: 'Overview',
                items: [],
                paragraphs: [],
            };
        }

        if (line.startsWith('- ')) {
            currentSection.items.push(stripBullet(line));
        } else {
            currentSection.paragraphs.push(line);
        }
    });

    if (currentSection) {
        blocks.push(currentSection);
    }

    return blocks;
};

export default function NotesComponent({ videoId }) {
    const [notes, setNotes] = useState(null);
    const [bookmarks, setBookmarks] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchNotes();
        fetchBookmarks();
    }, [videoId]);

    const fetchNotes = async () => {
        try {
            setLoading(true);
            setError(null);
            const response = await api.get(`notes/video/${videoId}/`);
            setNotes(response.data);
        } catch (err) {
            setError('Failed to load notes');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const fetchBookmarks = async () => {
        try {
            const response = await api.get('notes/bookmarks/my_bookmarks/');
            setBookmarks(response.data);
        } catch (err) {
            console.error('Failed to load bookmarks:', err);
        }
    };

    const addBookmark = async () => {
        if (!notes) {
            return;
        }

        try {
            await api.post('notes/bookmarks/add_bookmark/', {
                notes_id: notes.id,
                section_id: null,
                title: `${notes.title} overview`,
            });
            fetchBookmarks();
        } catch (err) {
            console.error('Failed to add bookmark:', err);
        }
    };

    const contentBlocks = useMemo(
        () => parseStructuredContent(notes?.content),
        [notes?.content],
    );

    const takeawayItems = useMemo(
        () => splitLines(notes?.key_takeaways).map((item) => stripBullet(item)),
        [notes?.key_takeaways],
    );

    const glossaryItems = useMemo(
        () => parseGlossary(notes?.important_terms),
        [notes?.important_terms],
    );

    if (loading) {
        return (
            <div className="rounded-[28px] border border-slate-200 bg-white/90 p-10 text-center shadow-sm">
                <div className="mx-auto mb-3 h-10 w-10 animate-spin rounded-full border-4 border-orange-100 border-t-orange-500" />
                <p className="text-sm font-medium text-slate-500">Preparing your study notes...</p>
            </div>
        );
    }

    if (error) {
        return <div className="rounded-3xl border border-rose-200 bg-rose-50 p-5 text-rose-700">{error}</div>;
    }

    if (!notes) {
        return <div className="rounded-3xl border border-slate-200 bg-white p-5 text-slate-600">No notes available for this video.</div>;
    }

    return (
        <div className="space-y-6">
            <div className="overflow-hidden rounded-[28px] border border-slate-200 bg-gradient-to-br from-slate-950 via-slate-900 to-orange-950 p-6 text-white shadow-xl shadow-slate-900/10">
                <div className="mb-4 flex items-center justify-between gap-4">
                    <span className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-orange-100">
                        <Sparkles size={14} />
                        Smart Notes
                    </span>
                    <GraduationCap size={20} className="text-orange-200" />
                </div>

                <h2 className="text-3xl font-semibold tracking-tight">{notes.title}</h2>
                <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-300">
                    Structured notes generated from lesson coverage for study and interview preparation.
                </p>

                <div className="mt-6 flex flex-wrap items-center gap-3 text-sm text-slate-200">
                    <span className="rounded-full bg-white/10 px-3 py-1">
                        {notes.is_ai_generated ? 'AI-assisted notes' : 'Instructor notes'}
                    </span>
                    <span className="rounded-full bg-white/10 px-3 py-1">
                        {new Date(notes.created_at).toLocaleDateString()}
                    </span>
                    <span className="rounded-full bg-white/10 px-3 py-1">
                        {bookmarks.length} bookmarks
                    </span>
                </div>
            </div>

            <div className="overflow-hidden rounded-[32px] border border-slate-200 bg-white shadow-sm">
                <div className="border-b border-slate-100 bg-[radial-gradient(circle_at_top_left,_rgba(251,146,60,0.18),_transparent_35%),linear-gradient(135deg,#fff7ed,#ffffff_55%,#f8fafc)] px-8 py-8">
                    <div className="flex flex-wrap items-start justify-between gap-4">
                        <div>
                            <p className="text-xs font-semibold uppercase tracking-[0.2em] text-orange-500">Video Coverage Notes</p>
                            <h1 className="mt-3 text-3xl font-semibold tracking-tight text-slate-950">{notes.video_title}</h1>
                        </div>

                        <button
                            onClick={addBookmark}
                            className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:border-orange-200 hover:text-orange-600"
                        >
                            <Bookmark size={16} />
                            Save Notes
                        </button>
                    </div>
                </div>

                <div className="space-y-6 px-8 py-8">
                    {contentBlocks.map((block, index) => (
                        <section
                            key={`${block.heading}-${index}`}
                            className={`rounded-[28px] border bg-gradient-to-br p-6 ${
                                SECTION_ACCENTS[block.heading] || 'from-slate-50 to-slate-100 border-slate-200'
                            }`}
                        >
                            <div className="mb-4 flex items-center gap-3">
                                <div className="rounded-2xl bg-white p-2 shadow-sm">
                                    {index === 0 ? (
                                        <BookOpen size={18} className="text-orange-500" />
                                    ) : index % 2 === 0 ? (
                                        <CheckCircle2 size={18} className="text-emerald-500" />
                                    ) : (
                                        <Lightbulb size={18} className="text-amber-500" />
                                    )}
                                </div>
                                <h2 className="text-2xl font-semibold text-slate-950">{block.heading}</h2>
                            </div>

                            {block.paragraphs.length > 0 && (
                                <div className="space-y-3">
                                    {block.paragraphs.map((paragraph, paragraphIndex) => (
                                        <p key={`${paragraph}-${paragraphIndex}`} className="text-base leading-8 text-slate-700">
                                            {paragraph}
                                        </p>
                                    ))}
                                </div>
                            )}

                            {block.items.length > 0 && (
                                <ul className="mt-4 space-y-3">
                                    {block.items.map((item, itemIndex) => (
                                        <li key={`${item}-${itemIndex}`} className="flex items-start gap-3 rounded-2xl bg-white/90 px-4 py-3 shadow-sm">
                                            <CheckCircle2 size={18} className="mt-0.5 shrink-0 text-orange-500" />
                                            <span className="text-sm leading-7 text-slate-700">{item}</span>
                                        </li>
                                    ))}
                                </ul>
                            )}
                        </section>
                    ))}

                    {(takeawayItems.length > 0 || glossaryItems.length > 0) && (
                        <div className="grid gap-6 lg:grid-cols-[1.1fr_0.9fr]">
                            {takeawayItems.length > 0 && (
                                <div className="rounded-[28px] border border-amber-100 bg-amber-50/70 p-6">
                                    <h2 className="text-xl font-semibold text-slate-950">Quick Revision</h2>
                                    <ul className="mt-4 space-y-3">
                                        {takeawayItems.map((item, index) => (
                                            <li key={`${item}-${index}`} className="flex items-start gap-3 rounded-2xl bg-white/80 px-4 py-3 shadow-sm">
                                                <CheckCircle2 size={18} className="mt-0.5 shrink-0 text-amber-500" />
                                                <span className="text-sm leading-7 text-slate-700">{item}</span>
                                            </li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {glossaryItems.length > 0 && (
                                <div className="rounded-[28px] border border-slate-200 bg-slate-50 p-6">
                                    <h2 className="text-xl font-semibold text-slate-950">Key Terms</h2>
                                    <div className="mt-4 space-y-3">
                                        {glossaryItems.map((item, index) => (
                                            <div key={`${item.term}-${index}`} className="rounded-2xl bg-white p-4 shadow-sm">
                                                <p className="text-sm font-semibold text-slate-900">{item.term}</p>
                                                <p className="mt-1 text-sm leading-6 text-slate-600">{item.definition}</p>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
