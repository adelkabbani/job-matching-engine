'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import SkillTree from '@/components/SkillTree';
import LiveAgentView from '@/components/LiveAgentView';
import ProfileUpload from '@/components/ProfileUpload';
import ResumePreview from '@/components/ResumePreview';
import CertificateInsights from '@/components/CertificateInsights';
import LinkedInAssistant from '@/components/LinkedInAssistant';
import JobMatches from '@/components/JobMatches';
import { motion } from 'framer-motion';
import { Briefcase, Target, Zap, Settings } from 'lucide-react';

const JobMap3D = dynamic(() => import('@/components/JobMap3D'), { ssr: false });

export default function Dashboard() {
  const [jobs, setJobs] = useState([]);
  const [cvData, setCvData] = useState(null);
  const [stats, setStats] = useState({
    totalJobs: 0,
    applied: 0,
    interviews: 0,
  });

  const fetchCV = async () => {
    try {
      const { createClient } = await import('@/utils/supabase/client');
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();

      if (!session) return;

      const res = await fetch('http://localhost:8000/api/me/cv', {
        headers: { 'Authorization': `Bearer ${session.access_token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCvData(data);
      }
    } catch (error) {
      console.error("Error fetching CV:", error);
    }
  };

  useEffect(() => {
    // Load jobs from backend
    fetch('http://localhost:8000/api/jobs')
      .then(res => res.json())
      .then(data => {
        setJobs(data);
        setStats({
          totalJobs: data.length,
          applied: data.filter((j: any) => j.status === 'applied').length,
          interviews: data.filter((j: any) => j.status === 'interview').length,
        });
      })
      .catch(err => console.log('Backend not running:', err));

    // Load CV
    fetchCV();
  }, []);

  return (
    <div className="min-h-screen p-6">
      {/* Header */}
      <div className="mb-8 flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold mb-2">Mission Control</h1>
          <p className="text-gray-400">Your AI-powered job search dashboard</p>
        </div>
        <a href="/settings" className="p-3 bg-slate-800 rounded-full hover:bg-slate-700 transition-colors border border-slate-700" title="API Settings">
          <Settings className="w-6 h-6 text-gray-300" />
        </a>
      </div>

      {/* Profile Upload Section */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4 text-blue-400">Step 1: Upload Your Profile</h2>
        <ProfileUpload onProfileUpdate={fetchCV} />
      </div>

      {/* CV Analysis Preview */}
      <div className="mb-8">
        <ResumePreview initialData={cvData || undefined} onRefresh={fetchCV} />
      </div>

      {/* Certificate Insights */}
      <div className="mb-8">
        <CertificateInsights />
      </div>

      {/* Job Matching Section */}
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4 text-green-400">Step 2: Find Your Matches</h2>
        <LinkedInAssistant />
        <JobMatches />
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <StatCard
          icon={<Briefcase className="w-6 h-6" />}
          label="Jobs Found"
          value={stats.totalJobs}
          color="blue"
        />
        <StatCard
          icon={<Zap className="w-6 h-6" />}
          label="Applied"
          value={stats.applied}
          color="green"
        />
        <StatCard
          icon={<Target className="w-6 h-6" />}
          label="Interviews"
          value={stats.interviews}
          color="yellow"
        />
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 3D Job Map */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          className="glass-effect rounded-xl p-6"
        >
          <h2 className="text-2xl font-semibold mb-4">Job Map</h2>
          <JobMap3D jobs={jobs} />
        </motion.div>

        {/* Skill Tree */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          className="glass-effect rounded-xl p-6"
        >
          <h2 className="text-2xl font-semibold mb-4">Skill Tree</h2>
          <SkillTree />
        </motion.div>
      </div>

      {/* Live Agent View */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
        className="glass-effect rounded-xl p-6 mt-6"
      >
        <h2 className="text-2xl font-semibold mb-4">Live Agent View</h2>
        <LiveAgentView />
      </motion.div>
    </div>
  );
}

function StatCard({
  icon,
  label,
  value,
  color
}: {
  icon: React.ReactNode;
  label: string;
  value: number;
  color: string;
}) {
  const colorClasses = {
    blue: 'text-blue-400',
    green: 'text-green-400',
    yellow: 'text-yellow-400',
  };

  return (
    <div className="glass-effect rounded-xl p-6">
      <div className="flex items-center justify-between mb-2">
        <span className={colorClasses[color as keyof typeof colorClasses]}>
          {icon}
        </span>
        <span className="text-3xl font-bold">{value}</span>
      </div>
      <p className="text-gray-400">{label}</p>
    </div>
  );
}