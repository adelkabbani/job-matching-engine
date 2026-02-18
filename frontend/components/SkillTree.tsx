'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Circle, AlertCircle } from 'lucide-react';

interface Skill {
    name: string;
    level: number;
    category: string;
    required_for?: number; // Number of jobs requiring this skill
}

export default function SkillTree() {
    const [skills, setSkills] = useState<Skill[]>([]);

    useEffect(() => {
        // Load user profile skills
        fetch('http://localhost:8000/api/profile/skills')
            .then(res => res.json())
            .then(data => setSkills(data))
            .catch(() => {
                // Mock data for demo
                setSkills([
                    { name: 'Python', level: 90, category: 'Languages', required_for: 12 },
                    { name: 'JavaScript', level: 85, category: 'Languages', required_for: 8 },
                    { name: 'React', level: 80, category: 'Frontend', required_for: 10 },
                    { name: 'Node.js', level: 75, category: 'Backend', required_for: 6 },
                    { name: 'Docker', level: 0, category: 'DevOps', required_for: 15 },
                    { name: 'Kubernetes', level: 0, category: 'DevOps', required_for: 8 },
                    { name: 'AWS', level: 60, category: 'Cloud', required_for: 11 },
                    { name: 'PostgreSQL', level: 70, category: 'Database', required_for: 9 },
                ]);
            });
    }, []);

    const categories = Array.from(new Set(skills.map(s => s.category)));

    const getSkillStatus = (level: number) => {
        if (level >= 70) return { icon: CheckCircle2, color: 'text-green-400', label: 'Strong' };
        if (level >= 40) return { icon: Circle, color: 'text-yellow-400', label: 'Moderate' };
        return { icon: AlertCircle, color: 'text-red-400', label: 'Missing' };
    };

    return (
        <div className="w-full h-[400px] overflow-y-auto space-y-6">
            {categories.map((category, idx) => (
                <motion.div
                    key={category}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.1 }}
                >
                    <h3 className="text-lg font-semibold mb-3 text-primary-400">{category}</h3>
                    <div className="space-y-2">
                        {skills
                            .filter(s => s.category === category)
                            .map((skill, skillIdx) => {
                                const status = getSkillStatus(skill.level);
                                const StatusIcon = status.icon;

                                return (
                                    <motion.div
                                        key={skill.name}
                                        initial={{ opacity: 0, scale: 0.9 }}
                                        animate={{ opacity: 1, scale: 1 }}
                                        transition={{ delay: idx * 0.1 + skillIdx * 0.05 }}
                                        className={`flex items-center justify-between p-3 rounded-lg 
                              ${skill.level === 0 ? 'bg-red-500/10 border border-red-500/30 animate-pulse-glow' : 'bg-white/5'}
                              hover:bg-white/10 transition-colors cursor-pointer`}
                                    >
                                        <div className="flex items-center gap-3">
                                            <StatusIcon className={`w-5 h-5 ${status.color}`} />
                                            <div>
                                                <p className="font-medium">{skill.name}</p>
                                                <p className="text-xs text-gray-400">
                                                    {skill.required_for} jobs require this
                                                </p>
                                            </div>
                                        </div>

                                        <div className="flex items-center gap-2">
                                            {skill.level === 0 ? (
                                                <span className="text-xs text-red-400 font-semibold">LEARN THIS!</span>
                                            ) : (
                                                <>
                                                    <div className="w-24 h-2 bg-gray-700 rounded-full overflow-hidden">
                                                        <motion.div
                                                            initial={{ width: 0 }}
                                                            animate={{ width: `${skill.level}%` }}
                                                            transition={{ duration: 1, delay: idx * 0.1 + skillIdx * 0.05 }}
                                                            className={`h-full ${skill.level >= 70 ? 'bg-green-500' :
                                                                    skill.level >= 40 ? 'bg-yellow-500' : 'bg-red-500'
                                                                }`}
                                                        />
                                                    </div>
                                                    <span className="text-sm font-semibold w-10 text-right">
                                                        {skill.level}%
                                                    </span>
                                                </>
                                            )}
                                        </div>
                                    </motion.div>
                                );
                            })}
                    </div>
                </motion.div>
            ))}
        </div>
    );
}
