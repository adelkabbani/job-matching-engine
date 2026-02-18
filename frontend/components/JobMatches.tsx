'use client';

import { useState, useEffect } from 'react';
import { Briefcase, TrendingUp, AlertCircle, MapPin, Building2, ExternalLink, CheckCircle, XCircle, Sparkles, RefreshCw, FileText, Download, Edit, Save, ListChecks } from 'lucide-react';

interface Job {
    id: string;
    title: string;
    company: string;
    location: string;
    remote_ok: boolean;
    url?: string;
    raw_data?: any;
    match_score: number;
    matched_skills: string[];
    missing_skills: string[];
    strengths_summary: string;
    filtered_out: boolean;
    filter_reason?: string;
    created_at: string;
    description: string;
    status: 'interested' | 'shortlisted' | 'rejected';
    is_easy_apply: boolean;
}

interface JobMatchesData {
    jobs: Job[];
    total: number;
    filtered_count: number;
}

export default function JobMatches() {
    const [data, setData] = useState<JobMatchesData | null>(null);
    const [loading, setLoading] = useState(true);
    const [showFiltered, setShowFiltered] = useState(false);
    const [minScore, setMinScore] = useState(50);
    const [newJobUrl, setNewJobUrl] = useState('');
    const [ingesting, setIngesting] = useState(false);
    const [discovering, setDiscovering] = useState(false);
    const [filterStatus, setFilterStatus] = useState<'all' | 'shortlisted'>('all');
    const [capturingDetails, setCapturingDetails] = useState<string | null>(null);
    const [dryRun, setDryRun] = useState(false);
    const [stopping, setStopping] = useState(false);
    const [tailoring, setTailoring] = useState<string | null>(null);
    const [selectedJobForMaterials, setSelectedJobForMaterials] = useState<Job | null>(null);
    const [materials, setMaterials] = useState<any>(null);
    const [finalizing, setFinalizing] = useState(false);
    const [debugSession, setDebugSession] = useState<any>(null);

    useEffect(() => {
        const checkSession = async () => {
            try {
                const { createClient } = await import('@/utils/supabase/client');
                const supabase = createClient();
                const { data: { session }, error } = await supabase.auth.getSession();
                setDebugSession(session);
                if (error) console.error("Session check error:", error);
            } catch (e) {
                console.error("Failed to check session:", e);
            }
        };
        checkSession();
    }, []);

    const fetchJobs = async () => {
        try {
            const { createClient } = await import('@/utils/supabase/client');
            const supabase = createClient();
            const { data: { session }, error: sessionError } = await supabase.auth.getSession();

            console.log("🔍 [fetchJobs] Checking session...");
            if (sessionError) console.error("❌ Session Error:", sessionError);

            if (!session) {
                console.warn("⚠️ No active session found. Aborting fetch.");
                setLoading(false);
                return;
            }

            console.log("✅ Session found for user:", session.user.id);
            console.log("🔑 Token prefix:", session.access_token.substring(0, 10) + "...");

            const res = await fetch(`http://localhost:8000/api/jobs/matches?min_score=${showFiltered ? 0 : minScore}`, {
                headers: {
                    'Authorization': `Bearer ${session.access_token}`,
                    'Content-Type': 'application/json'
                }
            });

            if (res.status === 401) {
                console.error("❌ 401 Unauthorized - The token might be invalid/expired even though we have a session.");
                alert("Session expired. Please sign out and sign in again.");
                return;
            }

            if (res.ok) {
                const jobsData = await res.json();
                console.log("📦 Jobs fetched successfully:", jobsData.jobs.length);
                setData(jobsData);
            } else {
                console.error("❌ Fetch failed:", res.status, res.statusText);
            }
        } catch (error) {
            console.error("❌ Error fetching jobs:", error);
        } finally {
            setLoading(false);
        }
    };

    const handleIngestJob = async () => {
        if (!newJobUrl.trim()) return;

        setIngesting(true);
        try {
            const { createClient } = await import('@/utils/supabase/client');
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();

            if (!session) return;

            const res = await fetch('http://localhost:8000/api/jobs/ingest', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${session.access_token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ url: newJobUrl })
            });

            if (res.ok) {
                setNewJobUrl('');
                await fetchJobs();
            } else {
                const error = await res.json();
                alert(`Failed to ingest job: ${error.detail}`);
            }
        } catch (error) {
            console.error("Error ingesting job:", error);
            alert('Failed to ingest job');
        } finally {
            setIngesting(false);
        }
    };

    const handleDiscoverJobs = async () => {
        setDiscovering(true);
        try {
            const { createClient } = await import('@/utils/supabase/client');
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();

            if (!session) return;

            const res = await fetch('http://localhost:8000/api/jobs/discover', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${session.access_token}`
                }
            });

            if (res.ok) {
                // Since it's a background task, we'll wait a bit and refresh
                // In a real app we might use websockets or polling
                setTimeout(fetchJobs, 3000);
                setTimeout(fetchJobs, 8000); // Polling twice for good measure
            } else {
                const error = await res.json();
                alert(`Failed to start discovery: ${error.detail}`);
            }
        } catch (error) {
            console.error("Error starting discovery:", error);
            alert('Failed to start discovery');
        } finally {
            setDiscovering(false);
        }
    };

    const handleShortlist = async (jobId: string) => {
        try {
            const { createClient } = await import('@/utils/supabase/client');
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) return;

            const res = await fetch(`http://localhost:8000/api/jobs/${jobId}/shortlist`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${session.access_token}` }
            });

            if (res.ok) fetchJobs();
        } catch (error) {
            console.error("Error shortlisting:", error);
        }
    };

    const handleReject = async (jobId: string) => {
        try {
            const { createClient } = await import('@/utils/supabase/client');
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) return;

            const res = await fetch(`http://localhost:8000/api/jobs/${jobId}/reject`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${session.access_token}` }
            });

            if (res.ok) fetchJobs();
        } catch (error) {
            console.error("Error rejecting:", error);
        }
    };

    const handleStop = async () => {
        setStopping(true);
        try {
            const { createClient } = await import('@/utils/supabase/client');
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) return;

            await fetch('http://localhost:8000/api/linkedin/stop-actions', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${session.access_token}` }
            });
        } catch (error) {
            console.error("Error stopping actions:", error);
        } finally {
            setStopping(false);
        }
    };

    const handleViewDetails = async (job: Job) => {
        // If it already has a description and score > 0, just open URL
        const jobUrl = job.url || (job.raw_data as any)?.url || (job.raw_data as any)?.redirect_url;

        if (job.match_score > 0 && !job.description.includes('pending')) {
            if (jobUrl) window.open(jobUrl, '_blank');
            else alert("Job URL not found");
            return;
        }

        setCapturingDetails(job.id);
        try {
            const { createClient } = await import('@/utils/supabase/client');
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) return;

            const res = await fetch(`http://localhost:8000/api/jobs/${job.id}/capture-details`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${session.access_token}` }
            });

            if (res.ok) {
                await fetchJobs();
                // After capture, it might be worth opening the URL too
            }
        } catch (error) {
            console.error("Error capturing details:", error);
        } finally {
            setCapturingDetails(null);
        }
    };

    const handleTailorCV = async (jobId: string) => {
        setTailoring(jobId);
        try {
            const { createClient } = await import('@/utils/supabase/client');
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) return;

            const res = await fetch(`http://localhost:8000/api/jobs/${jobId}/tailor-cv`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${session.access_token}` }
            });

            if (res.ok) {
                fetchMaterials(jobId);
            }
        } catch (error) {
            console.error("Error tailoring CV:", error);
        } finally {
            setTailoring(null);
        }
    };

    const handleGenerateCL = async (jobId: string, variant: string = 'professional') => {
        setTailoring(jobId);
        try {
            const { createClient } = await import('@/utils/supabase/client');
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) return;

            const res = await fetch(`http://localhost:8000/api/jobs/${jobId}/generate-cl?variant=${variant}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${session.access_token}` }
            });

            if (res.ok) {
                fetchMaterials(jobId);
            }
        } catch (error) {
            console.error("Error generating CL:", error);
        } finally {
            setTailoring(null);
        }
    };

    const fetchMaterials = async (jobId: string) => {
        try {
            const { createClient } = await import('@/utils/supabase/client');
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) return;

            const res = await fetch(`http://localhost:8000/api/jobs/${jobId}/materials`, {
                headers: { 'Authorization': `Bearer ${session.access_token}` }
            });

            if (res.ok) {
                const data = await res.json();
                setMaterials(data);
            }
        } catch (error) {
            console.error("Error fetching materials:", error);
        }
    };

    const handleFinalizeMaterials = async (jobId: string) => {
        setFinalizing(true);
        try {
            const { createClient } = await import('@/utils/supabase/client');
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) return;

            const res = await fetch(`http://localhost:8000/api/jobs/${jobId}/save-materials`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${session.access_token}` }
            });

            if (res.ok) {
                alert("Materials finalized and saved to storage!");
                fetchMaterials(jobId);
            }
        } catch (error) {
            console.error("Error finalizing:", error);
        } finally {
            setFinalizing(false);
        }
    };

    const handleApply = async (job: Job) => {
        if (!job.is_easy_apply) return;

        setCapturingDetails(job.id); // Re-use loading state
        try {
            const { createClient } = await import('@/utils/supabase/client');
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) return;

            const res = await fetch(`http://localhost:8000/api/linkedin/apply/${job.id}?dry_run=${dryRun}`, {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${session.access_token}` }
            });

            const result = await res.json();
            if (res.ok) {
                if (result.status === 'warning') {
                    alert(`⚠️ ${result.message}`);
                } else {
                    alert(result.message || "Assistant is filling the form!");
                }
            } else {
                alert(`Error: ${result.detail || result.message}`);
            }
        } catch (error) {
            console.error("Error applying:", error);
            alert("Failed to start application assistant.");
        } finally {
            setCapturingDetails(null);
        }
    };

    useEffect(() => {
        fetchJobs();
    }, [showFiltered, minScore, filterStatus]);

    if (loading) {
        return (
            <div className="flex items-center justify-center p-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600"></div>
            </div>
        );
    }

    const eligibleJobs = data?.jobs.filter(j => !j.filtered_out && j.match_score >= 50) || [];
    const filteredJobs = data?.jobs.filter(j => j.filtered_out) || [];

    return (
        <div className="bg-white rounded-xl shadow-lg p-6 border border-gray-200">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-blue-100 rounded-lg">
                        <Briefcase className="w-6 h-6 text-blue-600" />
                    </div>
                    <div>
                        <h2 className="text-xl font-bold text-gray-900">Job Matches</h2>
                        <p className="text-sm text-gray-500">
                            {eligibleJobs.length} eligible / {data?.total || 0} total
                        </p>
                    </div>
                </div>

                {/* Filter and Discovery */}
                <div className="flex items-center gap-4">
                    {/* Status Toggle */}
                    <div className="flex bg-gray-100 p-1 rounded-lg border border-gray-200">
                        <button
                            onClick={() => setFilterStatus('all')}
                            className={`px-3 py-1 rounded-md text-xs font-bold transition-all ${filterStatus === 'all' ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                                }`}
                        >
                            All Matches
                        </button>
                        <button
                            onClick={() => setFilterStatus('shortlisted')}
                            className={`px-3 py-1 rounded-md text-xs font-bold transition-all ${filterStatus === 'shortlisted' ? 'bg-white text-green-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                                }`}
                        >
                            Shortlisted
                        </button>
                    </div>

                    <button
                        onClick={handleDiscoverJobs}
                        disabled={discovering}
                        className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium shadow-md transition-all active:scale-95"
                    >
                        {discovering ? (
                            <>
                                <Sparkles className="w-4 h-4 animate-pulse" />
                                Finding Jobs...
                            </>
                        ) : (
                            <>
                                <Sparkles className="w-4 h-4" />
                                Find Jobs ✨
                            </>
                        )}
                    </button>

                    <label className="flex items-center gap-2 text-sm">
                        <input
                            type="checkbox"
                            checked={showFiltered}
                            onChange={(e) => setShowFiltered(e.target.checked)}
                            className="rounded"
                        />
                        Show filtered
                    </label>

                    <label className="flex items-center gap-2 text-sm font-bold text-orange-600 bg-orange-50 px-2 py-1 rounded border border-orange-100">
                        <input
                            type="checkbox"
                            checked={dryRun}
                            onChange={(e) => setDryRun(e.target.checked)}
                            className="rounded text-orange-600"
                        />
                        Dry Run 🧪
                    </label>
                </div>
            </div>

            {/* Add Job URL */}
            <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Add Job by URL (Manual Fallback)
                </label>
                <div className="flex gap-2">
                    <input
                        type="url"
                        value={newJobUrl}
                        onChange={(e) => setNewJobUrl(e.target.value)}
                        placeholder="https://example.com/job/12345"
                        className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                    />
                    <button
                        onClick={handleIngestJob}
                        disabled={ingesting || !newJobUrl.trim()}
                        className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 disabled:bg-gray-300 disabled:cursor-not-allowed font-medium"
                    >
                        {ingesting ? 'Adding...' : 'Add Job'}
                    </button>
                </div>
            </div>

            {/* Job List */}
            {!data || data.jobs.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                    <Briefcase className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                    <p>No jobs yet. Add a job URL to get started!</p>
                </div>
            ) : (
                <div className="space-y-4">
                    {data.jobs
                        .filter((job: Job) => filterStatus === 'shortlisted' ? job.status === 'shortlisted' : (showFiltered ? true : job.status !== 'rejected'))
                        .map((job: Job) => (
                            <div
                                key={job.id}
                                className={`border rounded-lg p-4 transition-colors relative ${job.filtered_out
                                    ? 'border-gray-200 bg-gray-50'
                                    : job.status === 'shortlisted'
                                        ? 'border-green-400 bg-green-50/50 shadow-md ring-1 ring-green-100'
                                        : job.match_score >= 70
                                            ? 'border-green-200 bg-green-50/30'
                                            : job.match_score >= 50
                                                ? 'border-yellow-200 bg-yellow-50/30'
                                                : 'border-red-200 bg-red-50/30'
                                    }`}
                            >
                                {/* Shortlist/Reject Actions Overlay */}
                                <div className="absolute top-4 right-4 flex items-center gap-2">
                                    <button
                                        onClick={() => handleShortlist(job.id)}
                                        className={`p-1.5 rounded-full border transition-all ${job.status === 'shortlisted'
                                            ? 'bg-yellow-100 border-yellow-300 text-yellow-600'
                                            : 'bg-white border-gray-200 text-gray-400 hover:text-yellow-500 hover:border-yellow-200'
                                            }`}
                                        title="Shortlist"
                                    >
                                        <Sparkles className={`w-4 h-4 ${job.status === 'shortlisted' ? 'fill-current' : ''}`} />
                                    </button>
                                    <button
                                        onClick={() => handleReject(job.id)}
                                        className="p-1.5 rounded-full bg-white border border-gray-200 text-gray-400 hover:text-red-500 hover:border-red-200 transition-all"
                                        title="Reject"
                                    >
                                        <XCircle className="w-4 h-4" />
                                    </button>
                                </div>

                                {/* Job Header */}
                                <div className="flex items-start justify-between mb-3">
                                    <div className="flex-1">
                                        <h3 className="font-bold text-gray-900 text-lg">{job.title}</h3>
                                        <div className="flex items-center gap-3 mt-1 text-sm text-gray-600">
                                            <div className="flex items-center gap-1">
                                                <Building2 className="w-4 h-4" />
                                                <span>{job.company}</span>
                                            </div>
                                            <div className="flex items-center gap-1">
                                                <MapPin className="w-4 h-4" />
                                                <span>{job.location}</span>
                                                {job.remote_ok && <span className="text-green-600">(Remote)</span>}
                                            </div>
                                        </div>
                                    </div>

                                    {job.status === 'shortlisted' && (
                                        <div className="px-3 py-1 bg-yellow-100 text-yellow-700 rounded-full text-xs font-bold border border-yellow-200 mr-2">
                                            Shortlisted
                                        </div>
                                    )}

                                    {/* Match Score Badge */}
                                    {!job.filtered_out && (
                                        <div className={`px-4 py-2 rounded-lg font-bold text-2xl mr-12 ${job.match_score >= 70
                                            ? 'bg-green-100 text-green-700'
                                            : job.match_score >= 50
                                                ? 'bg-yellow-100 text-yellow-700'
                                                : 'bg-red-100 text-red-700'
                                            }`}>
                                            {job.match_score}%
                                        </div>
                                    )}

                                    {job.filtered_out && (
                                        <div className="px-3 py-1 bg-gray-200 text-gray-700 rounded text-sm">
                                            Filtered
                                        </div>
                                    )}
                                </div>

                                {/* Filtered Reason */}
                                {job.filtered_out && job.filter_reason && (
                                    <div className="mb-3 p-2 bg-gray-100 rounded text-sm text-gray-600 flex items-center gap-2">
                                        <AlertCircle className="w-4 h-4" />
                                        <span>{job.filter_reason}</span>
                                    </div>
                                )}

                                {/* Strengths Summary */}
                                {!job.filtered_out && job.strengths_summary && (
                                    <div className="mb-3 p-3 bg-blue-50 border border-blue-200 rounded-lg">
                                        <div className="flex items-start gap-2">
                                            <Sparkles className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                                            <p className="text-sm text-blue-900">{job.strengths_summary}</p>
                                        </div>
                                    </div>
                                )}

                                {/* Skills */}
                                {!job.filtered_out && (
                                    <div className="grid grid-cols-2 gap-4 mb-3">
                                        {/* Matched Skills */}
                                        {job.matched_skills && job.matched_skills.length > 0 && (
                                            <div>
                                                <div className="flex items-center gap-2 mb-2">
                                                    <CheckCircle className="w-4 h-4 text-green-600" />
                                                    <span className="text-xs font-medium text-gray-700 uppercase">Matched</span>
                                                </div>
                                                <div className="flex flex-wrap gap-1">
                                                    {job.matched_skills.map((skill: string, idx: number) => (
                                                        <span
                                                            key={idx}
                                                            className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs"
                                                        >
                                                            {skill}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}

                                        {/* Missing Skills */}
                                        {job.missing_skills && job.missing_skills.length > 0 && (
                                            <div>
                                                <div className="flex items-center gap-2 mb-2">
                                                    <XCircle className="w-4 h-4 text-yellow-600" />
                                                    <span className="text-xs font-medium text-gray-700 uppercase">Missing</span>
                                                </div>
                                                <div className="flex flex-wrap gap-1">
                                                    {job.missing_skills.map((skill: string, idx: number) => (
                                                        <span
                                                            key={idx}
                                                            className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded text-xs"
                                                        >
                                                            {skill}
                                                        </span>
                                                    ))}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Actions */}
                                <div className="flex items-center gap-3 pt-3 border-t border-gray-200">
                                    <button
                                        onClick={() => handleViewDetails(job)}
                                        disabled={capturingDetails === job.id}
                                        className="flex items-center gap-1 text-sm text-purple-600 hover:text-purple-700 font-medium disabled:opacity-50"
                                    >
                                        {capturingDetails === job.id ? (
                                            <RefreshCw className="w-4 h-4 animate-spin" />
                                        ) : (
                                            <ExternalLink className="w-4 h-4" />
                                        )}
                                        {job.match_score > 0 ? 'View Job' : 'Analyze Details'}
                                    </button>

                                    {job.is_easy_apply && !job.filtered_out && (
                                        <div className="flex items-center gap-2">
                                            <button
                                                onClick={() => handleApply(job)}
                                                disabled={capturingDetails === job.id}
                                                className={`flex items-center gap-1 text-sm font-bold ${dryRun ? 'text-orange-600 bg-orange-50 border-orange-100 hover:bg-orange-100' : 'text-blue-600 bg-blue-50 border-blue-100 hover:bg-blue-100'} px-3 py-1 rounded-full border transition-all disabled:opacity-50`}
                                            >
                                                <Sparkles className="w-4 h-4" />
                                                {dryRun ? 'Dry Run Fill' : 'Easy Apply Assistant'}
                                            </button>

                                            {capturingDetails === job.id && (
                                                <button
                                                    onClick={handleStop}
                                                    disabled={stopping}
                                                    className="flex items-center gap-1 text-xs font-bold text-red-600 bg-red-50 border border-red-100 px-2 py-1 rounded-full hover:bg-red-100 animate-pulse disabled:opacity-50"
                                                >
                                                    {stopping ? 'Stopping...' : 'STOP 🛑'}
                                                </button>
                                            )}
                                        </div>
                                    )}

                                    {job.status === 'shortlisted' && (
                                        <button
                                            onClick={() => {
                                                setSelectedJobForMaterials(job);
                                                fetchMaterials(job.id);
                                            }}
                                            className="flex items-center gap-1 text-sm text-green-600 hover:text-green-700 font-bold bg-green-50 px-3 py-1 rounded-full border border-green-100 hover:bg-green-100 transition-all"
                                        >
                                            <FileText className="w-4 h-4" />
                                            CV & Cover Letter
                                        </button>
                                    )}

                                    {!job.filtered_out && job.match_score >= 50 && (
                                        <div className="flex items-center gap-2">
                                            <TrendingUp className="w-4 h-4 text-green-600" />
                                            <span className="text-sm font-medium text-green-600">Generated</span>
                                        </div>
                                    )}
                                </div>
                            </div>
                        ))}
                </div>
            )}

            {/* Materials Modal */}
            {selectedJobForMaterials && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-2xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
                        <div className="p-6 border-b border-gray-100 flex items-center justify-between bg-gray-50">
                            <div>
                                <h2 className="text-xl font-bold text-gray-900">Application Materials</h2>
                                <p className="text-sm text-gray-500">{selectedJobForMaterials.title} @ {selectedJobForMaterials.company}</p>
                            </div>
                            <button
                                onClick={() => setSelectedJobForMaterials(null)}
                                className="p-2 hover:bg-gray-200 rounded-full transition-colors"
                            >
                                <XCircle className="w-6 h-6 text-gray-400" />
                            </button>
                        </div>

                        <div className="flex-1 overflow-y-auto p-6 space-y-8">
                            {/* ATS Score Section */}
                            {materials?.cv && (
                                <div className="p-4 bg-purple-50 rounded-xl border border-purple-100">
                                    <div className="flex items-center justify-between mb-4">
                                        <div className="flex items-center gap-2">
                                            <TrendingUp className="w-5 h-5 text-purple-600" />
                                            <h3 className="font-bold text-purple-900 uppercase text-xs tracking-wider">ATS Optimization</h3>
                                        </div>
                                        <div className="px-3 py-1 bg-purple-600 text-white rounded-full text-sm font-bold">
                                            Score: {materials.cv.ats_score}%
                                        </div>
                                    </div>
                                    <div className="flex flex-wrap gap-2">
                                        {materials.cv.keywords_missing?.map((kw: string, i: number) => (
                                            <span key={i} className="px-2 py-0.5 bg-red-100 text-red-600 rounded-full text-xs font-medium border border-red-200">
                                                Missing: {kw}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <div className="grid grid-cols-2 gap-8">
                                {/* CV Section */}
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between">
                                        <h3 className="font-bold text-gray-900 flex items-center gap-2">
                                            <FileText className="w-5 h-5 text-blue-600" />
                                            Tailored CV
                                        </h3>
                                        {!materials?.cv ? (
                                            <button
                                                onClick={() => handleTailorCV(selectedJobForMaterials.id)}
                                                disabled={tailoring === selectedJobForMaterials.id}
                                                className="px-3 py-1 bg-blue-600 text-white rounded-lg text-xs font-bold hover:bg-blue-700 transition-all active:scale-95 disabled:opacity-50"
                                            >
                                                Tailor Now
                                            </button>
                                        ) : (
                                            <div className="flex items-center gap-2">
                                                <span className="text-xs text-green-600 font-bold bg-green-50 px-2 py-0.5 rounded border border-green-100">Tailored</span>
                                            </div>
                                        )}
                                    </div>
                                    <div className="border border-gray-200 rounded-xl p-4 bg-gray-50 min-h-[300px] text-sm text-gray-600 overflow-y-auto max-h-[400px]">
                                        {materials?.cv ? (
                                            <pre className="whitespace-pre-wrap font-sans">
                                                {JSON.stringify(materials.cv.tailored_content, null, 2)}
                                            </pre>
                                        ) : (
                                            <div className="flex items-center justify-center h-full text-gray-400">
                                                No tailored CV yet
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Cover Letter Section */}
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between">
                                        <h3 className="font-bold text-gray-900 flex items-center gap-2">
                                            <Sparkles className="w-5 h-5 text-purple-600" />
                                            Cover Letter
                                        </h3>
                                        <div className="flex gap-2">
                                            <button
                                                onClick={() => handleGenerateCL(selectedJobForMaterials.id, 'professional')}
                                                disabled={tailoring === selectedJobForMaterials.id}
                                                className="px-3 py-1 bg-purple-600 text-white rounded-lg text-xs font-bold hover:bg-purple-700 transition-all active:scale-95 disabled:opacity-50"
                                            >
                                                Draft Pro
                                            </button>
                                            <button
                                                onClick={() => handleGenerateCL(selectedJobForMaterials.id, 'concise')}
                                                disabled={tailoring === selectedJobForMaterials.id}
                                                className="px-3 py-1 bg-indigo-600 text-white rounded-lg text-xs font-bold hover:bg-indigo-700 transition-all active:scale-95 disabled:opacity-50"
                                            >
                                                Draft Concise
                                            </button>
                                        </div>
                                    </div>
                                    <div className="border border-gray-200 rounded-xl p-4 bg-purple-50/30 min-h-[300px] text-sm text-gray-600 overflow-y-auto max-h-[400px]">
                                        {materials?.cover_letters?.length > 0 ? (
                                            <div className="space-y-4">
                                                {materials.cover_letters.map((cl: any) => (
                                                    <div key={cl.id} className="p-3 bg-white rounded-lg border border-purple-100 shadow-sm">
                                                        <div className="flex items-center justify-between mb-2">
                                                            <span className="text-[10px] font-bold uppercase tracking-widest text-purple-500">{cl.variant}</span>
                                                        </div>
                                                        <p className="whitespace-pre-wrap">{cl.content}</p>
                                                    </div>
                                                ))}
                                            </div>
                                        ) : (
                                            <div className="flex items-center justify-center h-full text-gray-400">
                                                No cover letters yet
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="p-6 border-t border-gray-100 flex items-center justify-between bg-gray-50">
                            <div className="text-xs text-gray-400">
                                Docx generation will use your validated profile data.
                            </div>
                            <div className="flex gap-3">
                                <button
                                    onClick={() => handleFinalizeMaterials(selectedJobForMaterials.id)}
                                    disabled={!materials?.cv || finalizing}
                                    className="px-6 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-xl font-bold hover:shadow-lg transition-all active:scale-95 disabled:opacity-50 disabled:grayscale flex items-center gap-2"
                                >
                                    {finalizing ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                    Finalize & Save Docx
                                </button>
                                {materials?.cv?.storage_path && (
                                    <button className="px-6 py-2 bg-green-600 text-white rounded-xl font-bold hover:bg-green-700 transition-all active:scale-95 flex items-center gap-2">
                                        <Download className="w-4 h-4" />
                                        Download Final
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

