'use client';

import { useState, useEffect, useRef } from 'react';
import { Award, Tag, Calendar, Building2, TrendingUp, Loader2, AlertCircle, RefreshCw, Sparkles } from 'lucide-react';

interface CertificateInsight {
    document_id: string;
    status: 'pending' | 'processing' | 'done' | 'failed';
    error?: string;
    analyzed_at?: string;
    title?: string;
    issuer?: string;
    completion_date?: string;
    skills?: string[];
    confidence?: string;
}

interface InsightsData {
    certificates: CertificateInsight[];
    unique_skills: string[];
    total_count: number;
}

export default function CertificateInsights() {
    const [data, setData] = useState<InsightsData | null>(null);
    const [loading, setLoading] = useState(true);
    const [previousSkills, setPreviousSkills] = useState<string[]>([]);
    const [newSkills, setNewSkills] = useState<Set<string>>(new Set());
    const [retrying, setRetrying] = useState<Set<string>>(new Set());

    const newSkillsTimeoutRef = useRef<NodeJS.Timeout | null>(null);

    const fetchInsights = async () => {
        try {
            const { createClient } = await import('@/utils/supabase/client');
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();

            if (!session) {
                setLoading(false);
                return;
            }

            const res = await fetch('http://localhost:8000/api/me/certificate-insights', {
                headers: { 'Authorization': `Bearer ${session.access_token}` }
            });

            if (res.ok) {
                const insights = await res.json();

                // Detect new skills
                if (previousSkills.length > 0) {
                    const currentSkills = new Set(insights.unique_skills);
                    const added = insights.unique_skills.filter((s: string) => !previousSkills.includes(s));

                    if (added.length > 0) {
                        setNewSkills(new Set(added));

                        // Clear "new" indicator after 30 seconds
                        if (newSkillsTimeoutRef.current) {
                            clearTimeout(newSkillsTimeoutRef.current);
                        }
                        newSkillsTimeoutRef.current = setTimeout(() => {
                            setNewSkills(new Set());
                        }, 30000);
                    }
                }

                setPreviousSkills(insights.unique_skills);
                setData(insights);
            }
        } catch (error) {
            console.error("Error fetching insights:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleRetry = async (documentId: string) => {
        try {
            setRetrying(prev => new Set(prev).add(documentId));

            const { createClient } = await import('@/utils/supabase/client');
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();

            if (!session) return;

            const res = await fetch(`http://localhost:8000/api/certificate/retry/${documentId}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${session.access_token}` }
            });

            if (res.ok) {
                // Refresh insights immediately
                await fetchInsights();
            }
        } catch (error) {
            console.error("Error retrying certificate:", error);
        } finally {
            setRetrying(prev => {
                const next = new Set(prev);
                next.delete(documentId);
                return next;
            });
        }
    };

    useEffect(() => {
        fetchInsights();

        // Auto-refresh every 5 seconds to pick up new certificates
        const interval = setInterval(fetchInsights, 5000);
        return () => {
            clearInterval(interval);
            if (newSkillsTimeoutRef.current) {
                clearTimeout(newSkillsTimeoutRef.current);
            }
        };
    }, []);

    if (loading) {
        return (
            <div className="flex items-center justify-center p-8">
                <Loader2 className="w-6 h-6 animate-spin text-purple-600" />
                <span className="ml-2 text-gray-500">Loading certificates...</span>
            </div>
        );
    }

    if (!data || data.total_count === 0) return null;

    const newSkillsCount = newSkills.size;

    return (
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-100 rounded-lg">
                        <Award className="w-6 h-6 text-purple-600" />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-gray-900">Certificate Insights</h2>
                        <p className="text-sm text-gray-500">
                            {data.total_count} {data.total_count === 1 ? 'certificate' : 'certificates'}
                        </p>
                    </div>
                </div>

                {newSkillsCount > 0 && (
                    <div className="flex items-center gap-2 px-3 py-1 bg-green-50 border border-green-200 rounded-full">
                        <Sparkles className="w-4 h-4 text-green-600" />
                        <span className="text-sm font-medium text-green-700">+{newSkillsCount} new skill{newSkillsCount > 1 ? 's' : ''}</span>
                    </div>
                )}
            </div>

            {/* Unique Skills Summary */}
            {data.unique_skills.length > 0 && (
                <div className="mb-6 p-4 bg-purple-50 rounded-lg">
                    <div className="flex items-center gap-2 mb-3">
                        <TrendingUp className="w-5 h-5 text-purple-600" />
                        <h3 className="font-semibold text-gray-900">Your Skills ({data.unique_skills.length})</h3>
                    </div>
                    <div className="flex flex-wrap gap-2">
                        {data.unique_skills.map((skill, idx) => {
                            const isNew = newSkills.has(skill);
                            return (
                                <span
                                    key={idx}
                                    className={`px-3 py-1 border rounded-full text-sm font-medium transition-all ${isNew
                                            ? 'bg-green-50 border-green-300 text-green-700 animate-pulse'
                                            : 'bg-white border-purple-200 text-purple-700'
                                        }`}
                                >
                                    {skill}
                                    {isNew && <span className="ml-1 text-xs">✨</span>}
                                </span>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Certificate Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {data.certificates.map((cert) => (
                    <div
                        key={cert.document_id}
                        className="border border-gray-200 rounded-lg p-4 hover:border-purple-300 transition-colors bg-gradient-to-br from-white to-purple-50/30"
                    >
                        {/* Status Badge */}
                        <div className="flex items-center justify-between mb-2">
                            {cert.status === 'processing' && (
                                <span className="flex items-center gap-1 text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded font-medium">
                                    <Loader2 className="w-3 h-3 animate-spin" />
                                    Processing...
                                </span>
                            )}
                            {cert.status === 'done' && (
                                <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded font-medium">
                                    ✓ Analyzed
                                </span>
                            )}
                            {cert.status === 'failed' && (
                                <div className="flex items-center gap-2">
                                    <span className="flex items-center gap-1 text-xs px-2 py-1 bg-red-100 text-red-700 rounded font-medium">
                                        <AlertCircle className="w-3 h-3" />
                                        Failed
                                    </span>
                                    <button
                                        onClick={() => handleRetry(cert.document_id)}
                                        disabled={retrying.has(cert.document_id)}
                                        className="flex items-center gap-1 text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded font-medium hover:bg-purple-200 disabled:opacity-50"
                                    >
                                        {retrying.has(cert.document_id) ? (
                                            <Loader2 className="w-3 h-3 animate-spin" />
                                        ) : (
                                            <RefreshCw className="w-3 h-3" />
                                        )}
                                        Retry
                                    </button>
                                </div>
                            )}
                            {cert.status === 'pending' && (
                                <span className="text-xs px-2 py-1 bg-gray-100 text-gray-700 rounded font-medium">
                                    Pending...
                                </span>
                            )}
                        </div>

                        {/* Certificate Content */}
                        {cert.status === 'done' && cert.title ? (
                            <>
                                <h3 className="font-bold text-gray-900 mb-2 line-clamp-2">{cert.title}</h3>

                                <div className="space-y-2 text-sm">
                                    <div className="flex items-center gap-2 text-gray-600">
                                        <Building2 className="w-4 h-4 flex-shrink-0" />
                                        <span className="line-clamp-1">{cert.issuer}</span>
                                    </div>

                                    {cert.completion_date && (
                                        <div className="flex items-center gap-2 text-gray-600">
                                            <Calendar className="w-4 h-4 flex-shrink-0" />
                                            <span>{cert.completion_date}</span>
                                        </div>
                                    )}

                                    {cert.skills && cert.skills.length > 0 && (
                                        <div className="flex items-start gap-2">
                                            <Tag className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                                            <div className="flex flex-wrap gap-1">
                                                {cert.skills.map((skill, sidx) => (
                                                    <span
                                                        key={sidx}
                                                        className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs"
                                                    >
                                                        {skill}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </div>

                                {cert.confidence && (
                                    <div className="mt-3 pt-3 border-t border-gray-100">
                                        <span
                                            className={`text-xs px-2 py-1 rounded font-medium ${cert.confidence === 'high'
                                                    ? 'bg-green-100 text-green-700'
                                                    : cert.confidence === 'medium'
                                                        ? 'bg-yellow-100 text-yellow-700'
                                                        : 'bg-gray-100 text-gray-700'
                                                }`}
                                        >
                                            {cert.confidence} confidence
                                        </span>
                                    </div>
                                )}
                            </>
                        ) : cert.status === 'failed' && cert.error ? (
                            <div className="text-sm text-red-600">
                                <p className="font-medium">Error:</p>
                                <p className="text-xs mt-1">{cert.error}</p>
                            </div>
                        ) : (
                            <div className="text-sm text-gray-500">
                                <p>Waiting for analysis...</p>
                            </div>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}
