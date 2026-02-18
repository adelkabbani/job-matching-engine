'use client';

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Terminal, Loader2, CheckCircle, XCircle, Clock } from 'lucide-react';

interface LogEntry {
  timestamp: string;
  type: 'info' | 'success' | 'error' | 'warning';
  message: string;
}

export default function LiveAgentView() {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isActive, setIsActive] = useState(false);

  useEffect(() => {
    // Simulate live logs (replace with WebSocket in production)
    const interval = setInterval(() => {
      if (isActive) {
        const mockLogs: LogEntry[] = [
          { timestamp: new Date().toISOString(), type: 'info', message: '🔍 Navigating to job page...' },
          { timestamp: new Date().toISOString(), type: 'success', message: '✅ Found "Easy Apply" button' },
          { timestamp: new Date().toISOString(), type: 'info', message: '📝 Filling form field: Years of Experience = 5' },
          { timestamp: new Date().toISOString(), type: 'info', message: '📎 Uploading CV...' },
          { timestamp: new Date().toISOString(), type: 'success', message: '✅ Application submitted!' },
        ];

        const randomLog = mockLogs[Math.floor(Math.random() * mockLogs.length)];
        setLogs(prev => [...prev.slice(-9), randomLog]);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [isActive]);

  const getIcon = (type: string) => {
    switch (type) {
      case 'success': return <CheckCircle className="w-4 h-4 text-green-400" />;
      case 'error': return <XCircle className="w-4 h-4 text-red-400" />;
      case 'warning': return <Clock className="w-4 h-4 text-yellow-400" />;
      default: return <Terminal className="w-4 h-4 text-blue-400" />;
    }
  };

  return (
    <div className="w-full">
      {/* Control Panel */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Terminal className="w-5 h-5 text-primary-400" />
          <span className="font-semibold">Agent Status:</span>
          {isActive ? (
            <span className="flex items-center gap-2 text-green-400">
              <Loader2 className="w-4 h-4 animate-spin" />
              Active
            </span>
          ) : (
            <span className="text-gray-400">Idle</span>
          )}
        </div>

        <button
          onClick={() => setIsActive(!isActive)}
          className={`px-4 py-2 rounded-lg font-semibold transition-colors ${
            isActive
              ? 'bg-red-600 hover:bg-red-500'
              : 'bg-primary-600 hover:bg-primary-500'
          }`}
        >
          {isActive ? 'Stop Agent' : 'Start Agent'}
        </button>
      </div>

      {/* Terminal Window */}
      <div className="bg-black/40 rounded-lg p-4 h-[300px] overflow-y-auto font-mono text-sm border border-gray-700">
        <AnimatePresence>
          {logs.length === 0 ? (
            <p className="text-gray-500">Waiting for agent to start...</p>
          ) : (
            logs.map((log, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0 }}
                className="flex items-start gap-2 mb-2"
              >
                {getIcon(log.type)}
                <span className="text-gray-400 text-xs">
                  {new Date(log.timestamp).toLocaleTimeString()}
                </span>
                <span className={`flex-1 ${
                  log.type === 'success' ? 'text-green-400' :
                  log.type === 'error' ? 'text-red-400' :
                  log.type === 'warning' ? 'text-yellow-400' :
                  'text-gray-300'
                }`}>
                  {log.message}
                </span>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mt-4">
        <div className="bg-white/5 rounded-lg p-3 text-center">
          <p className="text-2xl font-bold text-green-400">0</p>
          <p className="text-xs text-gray-400">Applications Today</p>
        </div>
        <div className="bg-white/5 rounded-lg p-3 text-center">
          <p className="text-2xl font-bold text-yellow-400">0</p>
          <p className="text-xs text-gray-400">In Progress</p>
        </div>
        <div className="bg-white/5 rounded-lg p-3 text-center">
          <p className="text-2xl font-bold text-red-400">0</p>
          <p className="text-xs text-gray-400">Failed</p>
        </div>
      </div>
    </div>
  );
}