import React from 'react';

export default function KurinjiLogo({ size = 28 }) {
  return (
    <div style={{ display: 'inline-flex', alignItems: 'center' }}>
      <svg
        width={size}
        height={size}
        viewBox="0 0 32 32"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ flexShrink: 0 }}
      >
        <rect width="32" height="32" rx="8" fill="#1f1b18" />
        {/* Minimal geometric flower motif in crisp white and botanical green */}
        <circle cx="16" cy="16" r="4" fill="#10b981" />
        <path
          d="M16 6C16 11 11 16 6 16C11 16 16 21 16 26C16 21 21 16 26 16C21 16 16 11 16 6Z"
          stroke="#ffffff"
          strokeWidth="1.75"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
}
