'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function AssignmentsPage() {
  const router = useRouter();
  
  useEffect(() => {
    // Redirect to employees page since assignments are now integrated there
    router.replace('/employees');
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="text-lg text-gray-600 mb-4">
          Redirecting to Employee & Assignment Management...
        </div>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
      </div>
    </div>
  );
}