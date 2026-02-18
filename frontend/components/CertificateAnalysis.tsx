'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Award, Cpu, CheckCircle, AlertTriangle, Calendar, Building2, Tag } from 'lucide-react';

interface CertificateData {
    title: string;
    issuer: string;
    completion_date?: string | null;
    skills: string[];
    confidence?: string | null;
}

interface Certificate {
    document_id: string;
    filename: string;
    created_at: string;
    has_text: boolean;
    parsed_data?: CertificateData | null;
    storage_path: string;
}

interface CertificateAnalysisProps {
    initialData?: {
        certificates: Certificate[];
    };
    onRefresh: () => void;
}

export default function CertificateAnalysis({ initialData, onRefresh }: CertificateAnalysisProps) {
    const [analyzingId, setAnalyzingId] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [expandedId, setExpandedId] = useState<string | null>(null);

    if (!initialData || !initialData.certificates || initialData.certificates.length === 0) {
        return null;
    }

    const { certificates } = initialData;

    const handleAnalyze = async (documentId: string) => {
        setAnalyzingId(documentId);
        setError(null);

        try {
            const { createClient } = await import('@/utils/supabase/client');
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();

            if (!session) throw new Error('Not authenticated');

            const res = await fetch(`http://localhost:8000/api/certificate/extract/${documentId}`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${session.access_token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Analysis failed');
            }

            // Success - refresh data
            onRefresh();

        } catch (err: any) {
            setError(err.message || 'Failed to analyze certificate');
        } finally {
            setAnalyzingId(null);
        }
    };

    const toggleExpand = (id: string) => {
        setExpandedId(expandedId === id ? null : id);
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-white rounded-xl shadow-lg p-6 border border-gray-200"
        >
            <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-purple-100 rounded-lg">
                    <Award className="w-6 h-6 text-purple-600" />
                </div>
                <div>
                    <h2 className="text-xl font-bold text-gray-900">Certificate Analysis</h2>
                    <p className="text-sm text-gray-500">
                        {certificates.length} certificate{certificates.length !== 1 ? 's' : ''} uploaded
                    </p>
                </div>
            </div>

            {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
                    <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
                    <p className="text-sm text-red-800">{error}</p>
                </div>
            )}

            <div className="space-y-3">
                {certificates.map((cert) => (
                    <motion.div
                        key={cert.document_id}
                        layout
                        className="border border-gray-200 rounded-lg overflow-hidden hover:border-purple-300 transition-colors"
                    >
                        {/* Certificate Header */}
                        <div
                            className="p-4 bg-gray-50 cursor-pointer flex items-center justify-between"
                            onClick={() => toggleExpand(cert.document_id)}
                        >
                            <div className="flex items-center gap-3 flex-1">
                                <Award className="w-5 h-5 text-purple-600" />
                                <div className="flex-1 min-w-0">
                                    <p className="font-medium text-gray-900 truncate">{cert.filename}</p>
                                    <p className="text-xs text-gray-500">
                                        Uploaded {new Date(cert.created_at).toLocaleDateString()}
                                    </p>
                                </div>
                            </div>

                            {cert.parsed_data ? (
                                <div className="flex items-center gap-2 text-green-600">
                                    <CheckCircle className="w-5 h-5" />
                                    <span className="text-sm font-medium">Analyzed</span>
                                </div>
                            ) : (
                                <button
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleAnalyze(cert.document_id);
                                    }}
                                    disabled={analyzingId === cert.document_id || !cert.has_text}
                                    className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-sm font-medium flex items-center gap-2"
                                >
                                    {analyzingId === cert.document_id ? (
                                        <>
                                            <Cpu className="w-4 h-4 animate-spin" />
                                            Analyzing...
                                        </>
                                    ) : !cert.has_text ? (
                                        'No Text'
                                    ) : (
                                        <>
                                            <Cpu className="w-4 h-4" />
                                            Analyze
                                        </>
                                    )}
                                </button>
                            )}
                        </div>

                        {/* Expanded Details */}
                        <AnimatePresence>
                            {expandedId === cert.document_id && cert.parsed_data && (
                                <motion.div
                                    initial={{ height: 0, opacity: 0 }}
                                    animate={{ height: 'auto', opacity: 1 }}
                                    exit={{ height: 0, opacity: 0 }}
                                    transition={{ duration: 0.2 }}
                                    className="border-t border-gray-200"
                                >
                                    <div className="p-4 space-y-4">
                                        {/* Title */}
                                        <div>
                                            <h3 className="text-lg font-bold text-gray-900">
                                                {cert.parsed_data.title}
                                            </h3>
                                        </div>

                                        {/* Issuer */}
                                        <div className="flex items-start gap-2">
                                            <Building2 className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
                                            <div>
                                                <p className="text-xs text-gray-500 uppercase tracking-wide">Issuer</p>
                                                <p className="text-sm text-gray-900 font-medium">{cert.parsed_data.issuer}</p>
                                            </div>
                                        </div>

                                        {/* Completion Date */}
                                        {cert.parsed_data.completion_date && (
                                            <div className="flex items-start gap-2">
                                                <Calendar className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
                                                <div>
                                                    <p className="text-xs text-gray-500 uppercase tracking-wide">Completed</p>
                                                    <p className="text-sm text-gray-900 font-medium">
                                                        {cert.parsed_data.completion_date}
                                                    </p>
                                                </div>
                                            </div>
                                        )}

                                        {/* Skills */}
                                        {cert.parsed_data.skills && cert.parsed_data.skills.length > 0 && (
                                            <div>
                                                <div className="flex items-center gap-2 mb-2">
                                                    <Tag className="w-5 h-5 text-gray-400" />
                                                    <p className="text-xs text-gray-500 uppercase tracking-wide">Skills</p>
                                                </div>
                                                <div className="flex flex-wrap gap-2">
                                                    {cert.parsed_data.skills.map((skill, idx) => (
                                                        <span
                                                            key={idx}
                                                            className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-medium"
                                                        >
                                                            {skill}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Confidence Badge */}
                                        {cert.parsed_data.confidence && (
                                            <div className="pt-2 border-t border-gray-100">
                                                <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${cert.parsed_data.confidence === 'high' ? 'bg-green-100 text-green-700' :
                                                        cert.parsed_data.confidence === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                                                            'bg-gray-100 text-gray-700'
                                                    }`}>
                                                    Confidence: {cert.parsed_data.confidence}
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </motion.div>
                ))}
            </div>
        </motion.div>
    );
}
