'use client';

import { useEffect, useRef, useState } from 'react';
import Map, { Marker, Popup } from 'react-map-gl';
import { motion } from 'framer-motion';
import { MapPin, Briefcase } from 'lucide-react';

interface Job {
  id: string;
  title: string;
  company: string;
  location: string;
  match_score: number;
  latitude?: number;
  longitude?: number;
}

export default function JobMap3D({ jobs }: { jobs: Job[] }) {
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [viewState, setViewState] = useState({
    longitude: 10.4515,
    latitude: 51.1657,
    zoom: 5.5
  });

  const getMarkerColor = (score: number) => {
    if (score >= 90) return '#22c55e'; // Green
    if (score >= 70) return '#eab308'; // Yellow
    return '#ef4444'; // Red
  };

  return (
    <div className="w-full h-[400px] rounded-lg overflow-hidden relative">
      <Map
        {...viewState}
        onMove={evt => setViewState(evt.viewState)}
        mapStyle="mapbox://styles/mapbox/dark-v11"
        mapboxAccessToken={process.env.NEXT_PUBLIC_MAPBOX_TOKEN}
        style={{ width: '100%', height: '100%' }}
      >
        {jobs.map((job, index) => {
          const lat = job.latitude || 52.52 + (Math.random() - 0.5) * 2;
          const lng = job.longitude || 13.405 + (Math.random() - 0.5) * 2;
          
          return (
            <Marker
              key={job.id || index}
              longitude={lng}
              latitude={lat}
              onClick={(e) => {
                e.originalEvent.stopPropagation();
                setSelectedJob(job);
              }}
            >
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: index * 0.1 }}
                className="cursor-pointer"
              >
                <div
                  className="w-4 h-4 rounded-full animate-ping-slow"
                  style={{
                    backgroundColor: getMarkerColor(job.match_score || 50),
                    opacity: 0.6
                  }}
                />
                <MapPin
                  className="w-6 h-6 -mt-6 -ml-1"
                  style={{ color: getMarkerColor(job.match_score || 50) }}
                />
              </motion.div>
            </Marker>
          );
        })}

        {selectedJob && (
          <Popup
            longitude={selectedJob.longitude || 13.405}
            latitude={selectedJob.latitude || 52.52}
            onClose={() => setSelectedJob(null)}
            closeButton={true}
            closeOnClick={false}
          >
            <div className="p-2 bg-dark-800 text-white rounded">
              <h3 className="font-semibold">{selectedJob.title}</h3>
              <p className="text-sm text-gray-300">{selectedJob.company}</p>
              <p className="text-sm text-gray-400">{selectedJob.location}</p>
              <div className="mt-2 text-xs">
                Match: <span className="font-bold" style={{ 
                  color: getMarkerColor(selectedJob.match_score || 50) 
                }}>
                  {selectedJob.match_score || 50}%
                </span>
              </div>
            </div>
          </Popup>
        )}
      </Map>

      {/* Legend */}
      <div className="absolute bottom-4 right-4 glass-effect p-3 rounded-lg text-sm">
        <div className="flex items-center gap-2 mb-1">
          <div className="w-3 h-3 rounded-full bg-green-500" />
          <span>90%+ Match</span>
        </div>
        <div className="flex items-center gap-2 mb-1">
          <div className="w-3 h-3 rounded-full bg-yellow-500" />
          <span>70-89% Match</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded-full bg-red-500" />
          <span>50-69% Match</span>
        </div>
      </div>
    </div>
  );
}