'use client';

import { useState, useEffect } from 'react';
import { createClient } from '@/utils/supabase/client';
import { useRouter } from 'next/navigation';
import { Key, Check, AlertCircle, ArrowLeft, ShieldCheck, Lock } from 'lucide-react';
import Link from 'next/link';

export default function SettingsPage() {
    const [key, setKey] = useState('');
    const [status, setStatus] = useState<{ has_key: boolean, masked?: string } | null>(null);
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);
    const router = useRouter();
    const supabase = createClient();

    useEffect(() => {
        checkStatus();
    }, []);

    const checkStatus = async () => {
        const { data: { session } } = await supabase.auth.getSession();
        if (!session) {
            router.push('/login');
            return;
        }

        try {
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/settings/get-key-status`, {
                headers: {
                    Authorization: `Bearer ${session.access_token}`
                }
            });
            const data = await res.json();
            setStatus(data);
        } catch (err) {
            console.error("Failed to check status", err);
        }
    };

    const handleSave = async () => {
        setLoading(true);
        setMessage(null);

        try {
            const { data: { session } } = await supabase.auth.getSession();
            if (!session) throw new Error('Not authenticated');

            // Save to Backend (which encrypts it)
            const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/settings/save-key`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    Authorization: `Bearer ${session.access_token}`
                },
                body: JSON.stringify({ key })
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.detail || 'Failed to save key');
            }

            setMessage({ type: 'success', text: 'API Key encrypted and saved successfully!' });
            setKey(''); // Clear input for security
            await checkStatus(); // Refresh status

        } catch (err: any) {
            setMessage({ type: 'error', text: err.message || 'Failed to save key' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen p-6 bg-slate-900 text-white flex justify-center items-center">
            <div className="max-w-md w-full glass-effect p-8 rounded-xl border border-slate-700">

                <div className="mb-6 flex items-center">
                    <Link href="/dashboard" className="mr-4 p-2 hover:bg-slate-800 rounded-full transition-colors">
                        <ArrowLeft className="w-5 h-5" />
                    </Link>
                    <h1 className="text-2xl font-bold flex items-center">
                        <ShieldCheck className="w-6 h-6 mr-2 text-blue-400" />
                        Secure API Settings
                    </h1>
                </div>

                <div className="mb-8 p-4 bg-slate-800/50 rounded-lg border border-slate-700">
                    <h3 className="text-sm font-semibold text-gray-300 mb-2 flex items-center">
                        <Lock className="w-4 h-4 mr-2" /> Security Status
                    </h3>
                    <div className="flex items-center">
                        <div className={`w-3 h-3 rounded-full mr-2 ${status?.has_key ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]' : 'bg-red-500'}`}></div>
                        <span className="text-white font-medium">
                            {status?.has_key ? 'Connected & Encrypted' : 'Not Configured'}
                        </span>
                    </div>
                    {status?.has_key && (
                        <p className="text-xs text-gray-500 mt-1 pl-5">
                            Key is stored securely. To rotate, enter a new key below.
                        </p>
                    )}
                </div>

                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium mb-2 text-gray-300">Update OpenRouter API Key</label>
                        <input
                            type="password"
                            value={key}
                            onChange={(e) => setKey(e.target.value)}
                            placeholder="sk-or-..."
                            className="w-full bg-slate-800 border border-slate-600 rounded-lg p-3 text-white focus:ring-2 focus:ring-blue-500 outline-none transition-all"
                        />
                    </div>

                    {message && (
                        <div className={`p-3 rounded-lg flex items-center text-sm ${message.type === 'success' ? 'bg-green-900/50 text-green-300 border border-green-700' : 'bg-red-900/50 text-red-300 border border-red-700'
                            }`}>
                            {message.type === 'success' ? <Check className="w-4 h-4 mr-2" /> : <AlertCircle className="w-4 h-4 mr-2" />}
                            {message.text}
                        </div>
                    )}

                    <button
                        onClick={handleSave}
                        disabled={loading || !key}
                        className={`w-full py-3 rounded-lg font-semibold flex justify-center items-center transition-all ${loading || !key
                            ? 'bg-blue-900/50 cursor-not-allowed text-blue-300'
                            : 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg hover:shadow-blue-500/20'
                            }`}
                    >
                        {loading ? 'Encrypting & Saving...' : 'Save Configuration'}
                    </button>
                </div>

                <div className="mt-6 text-center">
                    <a
                        href="https://openrouter.ai/keys"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-400 hover:text-blue-300 underline"
                    >
                        Get an OpenRouter Key ↗
                    </a>
                </div>
            </div>
        </div>
    );
}

