'use client';

import { useState, useEffect } from 'react';
import { Linkedin, Globe, Zap, MousePointer2, StopCircle, RefreshCw, CheckCircle2, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function LinkedInAssistant() {
    const [status, setStatus] = useState<'idle' | 'running' | 'error'>('idle');
    const [message, setMessage] = useState('Connect LinkedIn to start your assisted job search.');
    const [capturing, setCapturing] = useState(false);
    const [lastCaptureCount, setLastCaptureCount] = useState<number | null>(null);
    const [appliesToday, setAppliesToday] = useState(0);
    const [maxApplies, setMaxApplies] = useState(50);

    const fetchStatus = async () => {
        try {
            const { createClient } = await import('@/utils/supabase/client');
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) return;
            const res = await fetch('http://localhost:8000/api/linkedin/status', {
                headers: { 'Authorization': `Bearer ${session.access_token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setStatus(data.status);
                setAppliesToday(data.applies_today);
                setMaxApplies(data.max_applies);
            }
        } catch (e) { console.error(e); }
    };

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 15000);
        return () => clearInterval(interval);
    }, []);

    const handleLaunch = async () => {
        setStatus('running');
        setMessage('Launching your browser window...');
        try {
            const { createClient } = await import('@/utils/supabase/client');
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) throw new Error('Not authenticated');

            const res = await fetch('http://localhost:8000/api/linkedin/launch', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${session.access_token}` }
            });

            if (res.ok) {
                setMessage('LinkedIn Browser is open. Please navigate to a job search or "Easy Apply" job.');
                fetchStatus();
            } else {
                throw new Error('Failed to launch browser');
            }
        } catch (error: any) {
            setStatus('error');
            setMessage(error.message || 'Error launching assistant');
        }
    };

    const handleStop = async () => {
        try {
            const { createClient } = await import('@/utils/supabase/client');
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) return;

            await fetch('http://localhost:8000/api/linkedin/stop', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${session.access_token}` }
            });
            setStatus('idle');
            setMessage('Assistant stopped. You can reconnect anytime.');
            fetchStatus();
        } catch (error) {
            console.error('Error stopping:', error);
        }
    };

    const handleCapture = async () => {
        setCapturing(true);
        setMessage('Capturing jobs from your active tab...');
        try {
            const { createClient } = await import('@/utils/supabase/client');
            const supabase = createClient();
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) return;

            const res = await fetch('http://localhost:8000/api/linkedin/capture', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${session.access_token}` }
            });

            const result = await res.json();
            if (res.ok) {
                setLastCaptureCount(result.count);
                setMessage(`Successfully captured ${result.count} new jobs! Check your matches below.`);
                // Trigger a global refresh if possible, or just let JobMatches poll
            } else {
                throw new Error(result.message || 'Capture failed');
            }
        } catch (error: any) {
            setMessage(`Capture error: ${error.message}`);
        } finally {
            setCapturing(false);
        }
    };

    return (
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100 mb-8">
            <div className="bg-gradient-to-r from-[#0077B5] to-[#00A0DC] p-6 text-white">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-white/20 rounded-lg backdrop-blur-sm">
                            <Linkedin className="w-8 h-8" />
                        </div>
                        <div>
                            <h2 className="text-2xl font-bold">LinkedIn Assistant</h2>
                            <p className="text-blue-100 text-sm opacity-90">Hardware-Assisted Job Discovery (Track B)</p>
                        </div>
                    </div>

                    {status === 'running' && (
                        <div className="flex items-center gap-2 px-3 py-1 bg-green-400/20 border border-green-400/30 rounded-full text-xs font-medium animate-pulse">
                            <div className="w-2 h-2 bg-green-400 rounded-full" />
                            ASSISTANT ACTIVE
                        </div>
                    )}
                </div>
            </div>

            <div className="p-6">
                <div className="flex flex-col md:flex-row gap-6 items-start">
                    <div className="flex-1 space-y-4">
                        <div className={`p-4 rounded-xl border flex items-start gap-3 ${status === 'error' ? 'bg-red-50 border-red-100 text-red-800' :
                            status === 'running' ? 'bg-blue-50 border-blue-100 text-blue-800' :
                                'bg-gray-50 border-gray-100 text-gray-700'
                            }`}>
                            {status === 'error' ? <AlertCircle className="w-5 h-5 mt-0.5" /> :
                                status === 'running' ? <Globe className="w-5 h-5 mt-0.5 text-blue-600 animate-spin-slow" /> :
                                    <Zap className="w-5 h-5 mt-0.5 text-yellow-600" />}
                            <p className="text-sm font-medium">{message}</p>
                        </div>

                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-4">
                            <div className="p-3 bg-gray-50 rounded-lg border border-gray-100">
                                <h4 className="text-xs font-bold text-gray-500 uppercase mb-1">Privacy First</h4>
                                <p className="text-xs text-gray-600">No passwords stored. Uses your local browser session.</p>
                            </div>
                            <div className="p-3 bg-gray-50 rounded-lg border border-gray-100">
                                <h4 className="text-xs font-bold text-gray-500 uppercase mb-1">Safety Beta</h4>
                                <p className="text-xs text-gray-600">Randomized delays and human-in-the-loop validation.</p>
                            </div>
                            <div className="p-3 bg-blue-50 rounded-lg border border-blue-100">
                                <h4 className="text-xs font-bold text-blue-600 uppercase mb-1">Daily Safety Filter</h4>
                                <div className="flex justify-between items-end">
                                    <p className="text-2xl font-black text-blue-900 leading-none">{appliesToday}<span className="text-lg text-blue-500 font-medium">/{maxApplies}</span></p>
                                    <p className="text-[10px] text-blue-600 font-semibold bg-blue-100 px-2 py-0.5 rounded-full">Automated</p>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="flex flex-col gap-3 w-full md:w-auto min-w-[200px]">
                        {status !== 'running' ? (
                            <button
                                onClick={handleLaunch}
                                className="flex items-center justify-center gap-2 px-6 py-3 bg-[#0077B5] text-white rounded-xl font-bold shadow-lg hover:bg-[#006396] transition-all active:scale-95"
                            >
                                <Zap className="w-5 h-5 fill-current" />
                                Connect LinkedIn
                            </button>
                        ) : (
                            <>
                                <button
                                    onClick={handleCapture}
                                    disabled={capturing}
                                    className="flex items-center justify-center gap-2 px-6 py-3 bg-green-600 text-white rounded-xl font-bold shadow-lg hover:bg-green-700 transition-all active:scale-95 disabled:opacity-50"
                                >
                                    {capturing ? (
                                        <RefreshCw className="w-5 h-5 animate-spin" />
                                    ) : (
                                        <MousePointer2 className="w-5 h-5" />
                                    )}
                                    Capture Job List
                                </button>
                                <button
                                    onClick={handleStop}
                                    className="flex items-center justify-center gap-2 px-6 py-2 border-2 border-red-200 text-red-600 rounded-xl font-bold hover:bg-red-50 transition-all"
                                >
                                    <StopCircle className="w-5 h-5" />
                                    Stop Assistant
                                </button>
                            </>
                        )}
                    </div>
                </div>

                <AnimatePresence>
                    {lastCaptureCount !== null && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            className="mt-6 pt-6 border-t border-gray-100"
                        >
                            <div className="flex items-center gap-2 text-green-700 bg-green-50 p-3 rounded-lg border border-green-100">
                                <CheckCircle2 className="w-5 h-5" />
                                <span className="font-semibold text-sm">Batch sync complete: {lastCaptureCount} new jobs queued for scoring.</span>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
}
