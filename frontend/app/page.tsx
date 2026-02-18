'use client';

import { motion } from 'framer-motion';
import { ArrowRight, MapPin, Sparkles, Zap } from 'lucide-react';
import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8">
      {/* Hero Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="text-center max-w-4xl"
      >
        <h1 className="text-6xl font-bold mb-6 bg-gradient-to-r from-primary-400 to-primary-600 bg-clip-text text-transparent">
          HyperApply
        </h1>
        
        <p className="text-2xl text-gray-300 mb-4">
          AI-Powered Job Application Platform
        </p>
        
        <p className="text-lg text-gray-400 mb-12 max-w-2xl mx-auto">
          Transform your job search into an intelligent, automated pipeline. 
          Find opportunities, tailor applications, and maximize your interview success rate.
        </p>

        {/* CTA Button */}
        <Link href="/dashboard">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="glass-effect px-8 py-4 rounded-xl text-lg font-semibold 
                     bg-primary-600 hover:bg-primary-500 transition-colors
                     flex items-center gap-2 mx-auto"
          >
            Launch Dashboard
            <ArrowRight className="w-5 h-5" />
          </motion.button>
        </Link>
      </motion.div>

      {/* Feature Cards */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4, duration: 0.8 }}
        className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-20 max-w-6xl"
      >
        <FeatureCard
          icon={<MapPin className="w-8 h-8 text-primary-400" />}
          title="3D Job Map"
          description="Visualize opportunities across Germany with an interactive 3D map"
        />
        <FeatureCard
          icon={<Sparkles className="w-8 h-8 text-primary-400" />}
          title="AI Matching"
          description="Smart algorithms find jobs that match your skills and goals"
        />
        <FeatureCard
          icon={<Zap className="w-8 h-8 text-primary-400" />}
          title="Auto-Apply"
          description="Automated applications with personalized CVs and cover letters"
        />
      </motion.div>
    </div>
  );
}

function FeatureCard({ icon, title, description }: { 
  icon: React.ReactNode; 
  title: string; 
  description: string;
}) {
  return (
    <motion.div
      whileHover={{ y: -5 }}
      className="glass-effect p-6 rounded-xl"
    >
      <div className="mb-4">{icon}</div>
      <h3 className="text-xl font-semibold mb-2">{title}</h3>
      <p className="text-gray-400">{description}</p>
    </motion.div>
  );
}