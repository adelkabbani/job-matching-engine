
'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FileText, Cpu, CheckCircle, AlertTriangle, Briefcase, GraduationCap, Code } from 'lucide-react';

interface ResumeData {
  contact_info: {
    name?: string;
    email?: string;
    phone?: string;
    location?: string;
    linkedin?: string;
  };
  summary?: string;
  skills: string[];
  experience: Array<{
    company: string;
    role: string;
    start_date?: string;
    end_date?: string;
    description?: string;
    technologies?: string[];
  }>;
  education: Array<{
    institution: string;
    degree: string;
    start_date?: string;
    end_date?: string;
  }>;
}

interface ResumePreviewProps {
  initialData?: {
    found: boolean;
    document_id?: string;
    filename?: string;
    has_text?: boolean;
    parsed_data?: ResumeData;
  };
  onRefresh: () => void;
}

export default function ResumePreview({ initialData, onRefresh }: ResumePreviewProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editData, setEditData] = useState<ResumeData | null>(null);

  if (!initialData || !initialData.found) {
    return null;
  }

  const { document_id, filename, parsed_data, has_text } = initialData;

  // Initialize editData when entering edit mode or when data loads
  const startEditing = () => {
    if (parsed_data) {
      setEditData(JSON.parse(JSON.stringify(parsed_data))); // Deep copy
      setIsEditing(true);
    }
  };

  const cancelEditing = () => {
    setIsEditing(false);
    setEditData(null);
  };

  const handleSave = async () => {
    if (!document_id || !editData) return;
    setIsSaving(true);
    setError(null);

    try {
      const { createClient } = await import('@/utils/supabase/client');
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) throw new Error('Not authenticated');

      const res = await fetch(`http://localhost:8000/api/cv/update/${document_id}`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${session.access_token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(editData)
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Save failed');
      }

      // Success
      setIsEditing(false);
      onRefresh(); // Reload data from parent

    } catch (err: any) {
      console.error(err);
      setError(err.message);
    } finally {
      setIsSaving(false);
    }
  };

  const handleAnalyze = async () => {
    if (!document_id) return;

    setIsAnalyzing(true);
    setError(null);

    try {
      const { createClient } = await import('@/utils/supabase/client');
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) throw new Error('Not authenticated');

      const res = await fetch(`http://localhost:8000/api/cv/extract/${document_id}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session.access_token}`
        }
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Analysis failed');
      }

      onRefresh();

    } catch (err: any) {
      console.error(err);
      setError(err.message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Helper to update nested state
  const updateContact = (field: string, value: string) => {
    if (!editData) return;
    setEditData({
      ...editData,
      contact_info: { ...editData.contact_info, [field]: value }
    });
  };

  return (
    <div className="glass-effect rounded-xl p-6 border border-white/10">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <FileText className="w-6 h-6 text-blue-400" />
            Resume Analysis
          </h2>
          <p className="text-gray-400 text-sm mt-1">
            File: <span className="text-white">{filename}</span>
          </p>
        </div>

        <div className="flex gap-2">
          {!parsed_data && has_text && !isAnalyzing && (
            <button
              onClick={handleAnalyze}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg font-medium transition-colors"
            >
              <Cpu className="w-4 h-4" /> Analyze CV
            </button>
          )}

          {isAnalyzing && (
            <button disabled className="flex items-center gap-2 px-4 py-2 bg-blue-600/50 rounded-lg font-medium cursor-not-allowed">
              <Cpu className="w-4 h-4 animate-spin" /> Analyzing...
            </button>
          )}

          {parsed_data && !isEditing && (
            <button
              onClick={startEditing}
              className="flex items-center gap-2 px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg font-medium transition-colors border border-white/10"
            >
              Edit
            </button>
          )}

          {isEditing && (
            <>
              <button
                onClick={cancelEditing}
                disabled={isSaving}
                className="px-4 py-2 hover:bg-white/10 rounded-lg font-medium transition-colors text-gray-300"
              >
                Cancel
              </button>
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 rounded-lg font-medium transition-colors"
              >
                {isSaving ? 'Saving...' : 'Save Changes'}
              </button>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex items-center gap-2 text-red-400">
          <AlertTriangle className="w-5 h-5" />
          {error}
        </div>
      )}

      {/* VIEW MODE */}
      {!isEditing && parsed_data ? (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* Header Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-white/5 p-4 rounded-lg">
            <div>
              <h3 className="text-xl font-semibold text-white">{parsed_data.contact_info.name || "Unknown Name"}</h3>
              <p className="text-blue-300">{parsed_data.contact_info.role || "Candidate"}</p>
            </div>
            <div className="text-sm text-gray-300 space-y-1">
              <p>📧 {parsed_data.contact_info.email}</p>
              {parsed_data.contact_info.phone && <p>📱 {parsed_data.contact_info.phone}</p>}
              {parsed_data.contact_info.location && <p>📍 {parsed_data.contact_info.location}</p>}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Experience */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold flex items-center gap-2 text-green-400">
                <Briefcase className="w-5 h-5" /> Experience
              </h3>
              {parsed_data.experience.length > 0 ? (
                parsed_data.experience.map((exp, idx) => (
                  <div key={idx} className="bg-white/5 p-4 rounded-lg border border-white/5">
                    <div className="flex justify-between items-start mb-1">
                      <h4 className="font-medium text-white">{exp.role}</h4>
                      <span className="text-xs text-gray-400 bg-black/20 px-2 py-1 rounded">
                        {exp.start_date} - {exp.end_date}
                      </span>
                    </div>
                    <p className="text-sm text-blue-300 mb-2">{exp.company}</p>
                    <p className="text-sm text-gray-400 line-clamp-3">{exp.description}</p>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 italic">No experience found.</p>
              )}
            </div>

            {/* Skills & Education */}
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold flex items-center gap-2 text-purple-400 mb-3">
                  <Code className="w-5 h-5" /> Key Skills
                </h3>
                <div className="flex flex-wrap gap-2">
                  {parsed_data.skills.map((skill, idx) => (
                    <span key={idx} className="px-3 py-1 bg-purple-500/10 text-purple-300 rounded-full text-sm border border-purple-500/20">
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold flex items-center gap-2 text-yellow-400 mb-3">
                  <GraduationCap className="w-5 h-5" /> Education
                </h3>
                {parsed_data.education.map((edu, idx) => (
                  <div key={idx} className="mb-3 bg-white/5 p-3 rounded-lg">
                    <h4 className="font-medium text-white">{edu.institution}</h4>
                    <p className="text-sm text-gray-300">{edu.degree}</p>
                    <p className="text-xs text-gray-500 mt-1">{edu.start_date} - {edu.end_date}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      ) : isEditing && editData ? (

        /* EDIT MODE FORM */
        <div className="space-y-6 animate-in fade-in duration-300">
          {/* Contact Info Edit */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-white/5 p-4 rounded-lg border border-blue-500/30">
            <div className="space-y-2">
              <label className="text-xs text-gray-400">Full Name</label>
              <input
                className="w-full bg-black/20 border border-white/10 rounded p-2 text-white focus:outline-none focus:border-blue-500"
                value={editData.contact_info.name || ''}
                onChange={(e) => updateContact('name', e.target.value)}
              />
              <label className="text-xs text-gray-400">Current Role</label>
              <input
                className="w-full bg-black/20 border border-white/10 rounded p-2 text-white focus:outline-none focus:border-blue-500"
                value={editData.contact_info.role || ''} // Note: This field might not be in schema, careful
                onChange={(e) => updateContact('role', e.target.value)}
              />
            </div>
            <div className="space-y-2">
              <label className="text-xs text-gray-400">Email</label>
              <input
                className="w-full bg-black/20 border border-white/10 rounded p-2 text-white focus:outline-none focus:border-blue-500"
                value={editData.contact_info.email || ''}
                onChange={(e) => updateContact('email', e.target.value)}
              />
              <label className="text-xs text-gray-400">Phone</label>
              <input
                className="w-full bg-black/20 border border-white/10 rounded p-2 text-white focus:outline-none focus:border-blue-500"
                value={editData.contact_info.phone || ''}
                onChange={(e) => updateContact('phone', e.target.value)}
              />
            </div>
          </div>

          {/* Simple Textarea for JSON fallback editing for now, or build full UI */}
          {/* For Step 3 simplicity, let's offer a JSON editor for complex arrays, OR simple fields if user asked for "form UI" */}
          {/* User asked for: Skills (add/remove), Experience (title/company/dates/bullets) */}

          {/* SKILLS EDITOR */}
          <div className="bg-white/5 p-4 rounded-lg">
            <h3 className="text-lg font-semibold text-purple-400 mb-2">Skills (Comma Separated)</h3>
            <textarea
              className="w-full h-24 bg-black/20 border border-white/10 rounded p-2 text-white font-mono text-sm"
              value={editData.skills.join(', ')}
              onChange={(e) => setEditData({ ...editData, skills: e.target.value.split(',').map(s => s.trim()).filter(Boolean) })}
            />
          </div>

          {/* EXPERIENCE - Just render first 3 for MVP editing or map them */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-green-400">Experience</h3>
            {editData.experience.map((exp, idx) => (
              <div key={idx} className="bg-white/5 p-4 rounded-lg border border-white/10 space-y-2">
                <div className="grid grid-cols-2 gap-2">
                  <input
                    className="bg-black/20 border border-white/10 rounded p-2 text-white"
                    placeholder="Role"
                    value={exp.role}
                    onChange={(e) => {
                      const newExp = [...editData.experience];
                      newExp[idx].role = e.target.value;
                      setEditData({ ...editData, experience: newExp });
                    }}
                  />
                  <input
                    className="bg-black/20 border border-white/10 rounded p-2 text-white"
                    placeholder="Company"
                    value={exp.company}
                    onChange={(e) => {
                      const newExp = [...editData.experience];
                      newExp[idx].company = e.target.value;
                      setEditData({ ...editData, experience: newExp });
                    }}
                  />
                </div>
                <textarea
                  className="w-full bg-black/20 border border-white/10 rounded p-2 text-white text-sm h-20"
                  placeholder="Description"
                  value={exp.description || ''}
                  onChange={(e) => {
                    const newExp = [...editData.experience];
                    newExp[idx].description = e.target.value;
                    setEditData({ ...editData, experience: newExp });
                  }}
                />
              </div>
            ))}
          </div>

        </div>

      ) : (
        <div className="flex flex-col items-center justify-center py-12 text-gray-400">
          <div className="p-4 bg-white/5 rounded-full mb-4">
            <FileText className="w-8 h-8 opacity-50" />
          </div>
          <p>Resume uploaded. Ready for AI analysis.</p>
        </div>
      )}
    </div>
  );
}
