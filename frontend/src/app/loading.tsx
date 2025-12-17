'use client';

import { CampingLoader } from '@/components/CampingLoader';
import { useEffect, useState } from 'react';

export default function Loading() {
    const [showLoader, setShowLoader] = useState(true);

    useEffect(() => {
        // 3.5 second delay for page transitions
        const timer = setTimeout(() => {
            setShowLoader(false);
        }, 3500);

        return () => clearTimeout(timer);
    }, []);

    if (!showLoader) return null;

    return <CampingLoader />;
}
