'use client';

import { useState } from 'react';
import { Upload, FileText, Award, Briefcase, CheckCircle, AlertCircle, X, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface UploadedFile {
    id: string;
    name: string;
    status: 'uploading' | 'success' | 'error';
    error?: string;
}

export default function ProfileUpload({ onProfileUpdate }: { onProfileUpdate?: () => void }) {
    const [uploadedFiles, setUploadedFiles] = useState<{ [key: string]: UploadedFile[] }>({
        cv: [],
        certificate: [],
        experience: []
    });

    const handleFileUpload = async (type: 'cv' | 'certificate' | 'experience', files: FileList | null) => {
        if (!files || files.length === 0) return;

        // Convert FileList to Array
        const filesArray = Array.from(files);

        // Add files to state with 'uploading' status
        const newFiles = filesArray.map(file => ({
            id: Math.random().toString(36).substr(2, 9),
            name: file.name,
            status: 'uploading' as const
        }));

        setUploadedFiles(prev => ({
            ...prev,
            [type]: [...prev[type], ...newFiles]
        }));

        // Upload each file
        for (let i = 0; i < filesArray.length; i++) {
            const file = filesArray[i];
            const fileId = newFiles[i].id;

            const formData = new FormData();
            formData.append('file', file);

            try {
                // Get current session for token
                const { createClient } = await import('@/utils/supabase/client');
                const supabase = createClient();
                const { data: { session } } = await supabase.auth.getSession();

                if (!session) throw new Error('You must be logged in to upload files');

                // Use relative path for proxy
                const res = await fetch(`/api/upload/${type}`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${session.access_token}`
                    },
                    body: formData,
                });

                if (res.ok) {
                    updateFileStatus(type, fileId, 'success');
                    if (type === 'cv' && onProfileUpdate) {
                        setTimeout(onProfileUpdate, 2000);
                    }
                } else {
                    updateFileStatus(type, fileId, 'error', `Failed: ${res.statusText}`);
                }
            } catch (error: any) {
                console.error('Upload failed:', error);
                updateFileStatus(type, fileId, 'error', error.message || 'Network Error');
            }
        }
    };

    const updateFileStatus = (type: string, fileId: string, status: 'success' | 'error', error?: string) => {
        setUploadedFiles(prev => ({
            ...prev,
            [type]: prev[type].map(f => f.id === fileId ? { ...f, status, error } : f)
        }));
    };

    const removeFile = (type: string, fileId: string) => {
        setUploadedFiles(prev => ({
            ...prev,
            [type]: prev[type].filter(f => f.id !== fileId)
        }));
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {/* CV Upload */}
            <UploadCard
                type="cv"
                title="Upload CV"
                description="PDF or DOCX (Single File)"
                icon={<FileText className="w-8 h-8 text-blue-400" />}
                files={uploadedFiles.cv}
                onUpload={(files) => handleFileUpload('cv', files)}
                onRemove={(id) => removeFile('cv', id)}
                accept=".pdf,.doc,.docx"
                multiple={false}
            />

            {/* Certificate Upload */}
            <UploadCard
                type="certificate"
                title="Certificates"
                description="Images or PDF (Multiple)"
                icon={<Award className="w-8 h-8 text-yellow-400" />}
                files={uploadedFiles.certificate}
                onUpload={(files) => handleFileUpload('certificate', files)}
                onRemove={(id) => removeFile('certificate', id)}
                accept="image/*,.pdf"
                multiple={true}
            />

            {/* Experience Upload */}
            <UploadCard
                type="experience"
                title="Work Experience"
                description="Documents (Multiple)"
                icon={<Briefcase className="w-8 h-8 text-green-400" />}
                files={uploadedFiles.experience}
                onUpload={(files) => handleFileUpload('experience', files)}
                onRemove={(id) => removeFile('experience', id)}
                accept=".pdf,.doc,.docx,image/*"
                multiple={true}
            />
        </div>
    );
}

function UploadCard({
    type,
    title,
    description,
    icon,
    files,
    onUpload,
    onRemove,
    accept,
    multiple
}: {
    type: string;
    title: string;
    description: string;
    icon: React.ReactNode;
    files: UploadedFile[];
    onUpload: (files: FileList | null) => void;
    onRemove: (id: string) => void;
    accept: string;
    multiple: boolean;
}) {
    return (
        <motion.div
            whileHover={{ y: -5 }}
            className="glass-effect rounded-xl p-6 relative overflow-hidden group border border-white/10 hover:border-white/20 h-full flex flex-col"
        >
            <div className="flex flex-col items-center text-center space-y-4 mb-4">
                <div className="p-4 bg-white/5 rounded-full group-hover:bg-white/10 transition-colors">
                    {icon}
                </div>

                <div>
                    <h3 className="text-lg font-semibold">{title}</h3>
                    <p className="text-sm text-gray-400">{description}</p>
                </div>

                <div className="w-full">
                    <label className="flex flex-col items-center justify-center w-full h-24 border-2 border-dashed border-gray-600 rounded-lg cursor-pointer hover:border-gray-400 transition-colors bg-black/20 hover:bg-black/30">
                        <div className="flex flex-col items-center pt-5 pb-6">
                            <Upload className="w-6 h-6 text-gray-400 mb-2" />
                            <p className="text-xs text-gray-400">Click to upload {multiple ? 'files' : 'file'}</p>
                        </div>
                        <input
                            type="file"
                            className="hidden"
                            accept={accept}
                            multiple={multiple}
                            onChange={(e) => onUpload(e.target.files)}
                        />
                    </label>
                </div>
            </div>

            {/* File List */}
            <div className="flex-1 space-y-2 max-h-40 overflow-y-auto custom-scrollbar">
                <AnimatePresence>
                    {files.map((file) => (
                        <motion.div
                            key={file.id}
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className="flex items-center justify-between p-2 rounded bg-white/5 text-sm"
                        >
                            <div className="flex items-center gap-2 truncate">
                                {file.status === 'uploading' && <Loader2 className="w-3 h-3 animate-spin text-blue-400" />}
                                {file.status === 'success' && <CheckCircle className="w-3 h-3 text-green-400" />}
                                {file.status === 'error' && <AlertCircle className="w-3 h-3 text-red-400" />}
                                <span className="truncate max-w-[150px]" title={file.name}>{file.name}</span>
                            </div>

                            {file.status === 'error' ? (
                                <span className="text-xs text-red-400 ml-2">{file.error}</span>
                            ) : (
                                <button
                                    onClick={(e) => { e.stopPropagation(); onRemove(file.id); }}
                                    className="p-1 hover:bg-white/10 rounded"
                                >
                                    <X className="w-3 h-3 text-gray-400 hover:text-white" />
                                </button>
                            )}
                        </motion.div>
                    ))}
                </AnimatePresence>
            </div>
        </motion.div>
    );
}
