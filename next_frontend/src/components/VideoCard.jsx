'use client';

export default function VideoCard({ video, onViewDetails }) {
    const handleViewLesson = () => {
        onViewDetails?.('lesson', video.id);
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

                <div className="grid grid-cols-1 gap-2">
                    <button
                        onClick={handleViewLesson}
                        className="py-2 px-3 rounded-lg font-medium text-sm transition-colors bg-blue-100 text-blue-700 hover:bg-blue-200"
                    >
                        View Lesson
                    </button>
                </div>
            </div>
        </div>
    );
}
