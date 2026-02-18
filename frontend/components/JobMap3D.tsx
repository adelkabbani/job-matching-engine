'use client';

import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix Leaflet's default icon path issue in Next.js
const iconUrl = 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-icon.png';
const iconRetinaUrl = 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-icon-2x.png';
const shadowUrl = 'https://unpkg.com/leaflet@1.9.3/dist/images/marker-shadow.png';

const customIcon = new L.Icon({
    iconUrl: iconUrl,
    iconRetinaUrl: iconRetinaUrl,
    shadowUrl: shadowUrl,
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
});

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
    const mapContainerRef = useRef<HTMLDivElement>(null);
    const mapInstanceRef = useRef<L.Map | null>(null);
    const [isClient, setIsClient] = useState(false);

    // Ensure we're on the client
    useEffect(() => {
        setIsClient(true);
    }, []);

    // Initialize map after client mount
    useEffect(() => {
        if (!isClient || !mapContainerRef.current) return;

        // CRITICAL: Check if container already has a map
        const container = mapContainerRef.current;
        if ((container as any)._leaflet_id) {
            // Container already initialized, skip
            return;
        }

        // Create map instance
        const map = L.map(container, {
            center: [51.1657, 10.4515],
            zoom: 6,
            scrollWheelZoom: true,
        });

        // Add tile layer
        L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);

        // Add markers for jobs
        jobs.forEach((job) => {
            if (job.latitude && job.longitude) {
                L.marker([job.latitude, job.longitude], { icon: customIcon })
                    .addTo(map)
                    .bindPopup(`
                        <div class="p-1">
                            <h3 class="font-bold text-gray-900">${job.title}</h3>
                            <p class="text-gray-600">${job.company}</p>
                            <p class="text-xs text-gray-500 mt-1">Match: ${job.match_score}%</p>
                        </div>
                    `);
            }
        });

        mapInstanceRef.current = map;

        // Cleanup function
        return () => {
            if (mapInstanceRef.current) {
                mapInstanceRef.current.remove();
                mapInstanceRef.current = null;
            }
        };
    }, [isClient, jobs]);

    if (!isClient) {
        return <div className="w-full h-[400px] bg-dark-800 animate-pulse rounded-lg" />;
    }

    return (
        <div className="w-full h-[400px] rounded-lg overflow-hidden relative z-0">
            <div
                ref={mapContainerRef}
                style={{ height: "100%", width: "100%" }}
            />

            {/* Legend Overlay */}
            <div className="absolute bottom-4 right-4 bg-black/70 p-3 rounded-lg text-sm text-white z-[1000] backdrop-blur-sm border border-white/10">
                <div className="font-semibold mb-1">Open Street Map</div>
                <div className="text-xs text-gray-400">German Job Market</div>
            </div>
        </div>
    );
}
