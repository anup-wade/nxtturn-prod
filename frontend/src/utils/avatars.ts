// src/utils/avatars.ts

import defaultAvatar from '@/assets/images/default-avatar.svg';

// This safely gets the base URL from the environment variables.
const API_URL_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace('/api/', '');

/**
 * Creates an SVG data URL for a simple avatar with initials.
 * @param initials The user's initials (e.g., "JD").
 * @returns A base64 encoded SVG data URL.
 */
function createInitialsAvatar(initials: string): string {
  // Simple hashing function to get a consistent color from the initials
  let hash = 0;
  for (let i = 0; i < initials.length; i++) {
    hash = initials.charCodeAt(i) + ((hash << 5) - hash);
  }
  const h = hash % 360;
  const color = `hsl(${h}, 50%, 60%)`; // Generate a pleasant color

  const svg = `
    <svg width="100" height="100" viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <rect width="100%" height="100%" fill="${color}" />
      <text
        x="50%"
        y="50%"
        dominant-baseline="central"
        text-anchor="middle"
        font-family="sans-serif"
        font-size="40"
        fill="white"
        font-weight="bold"
      >
        ${initials.toUpperCase()}
      </text>
    </svg>
  `;

  // Return a "data URL" which can be used directly in an <img> src
  return `data:image/svg+xml;base64,${btoa(svg)}`;
}


/**
 * A robust function to get a user's avatar.
 * It prioritizes: 1. Custom Picture, 2. Initials-based SVG, 3. Static Fallback.
 */
export function getAvatarUrl(
  pictureUrl: string | null | undefined, 
  firstName: string | null | undefined, 
  lastName: string | null | undefined
): string {
  
  // 1. If a custom picture URL exists, use it.
  if (pictureUrl) {
    if (pictureUrl.startsWith('http')) {
      return pictureUrl; // Already a full URL (from Cloudinary, etc.)
    }
    return `${API_URL_BASE}${pictureUrl}`; // Local relative path
  }

  // 2. If no picture, try to generate initials.
  const firstInitial = firstName?.[0] || '';
  const lastInitial = lastName?.[0] || '';
  const initials = `${firstInitial}${lastInitial}`;

  if (initials) {
    return createInitialsAvatar(initials);
  }

  // 3. If all else fails, return the static default avatar.
  return defaultAvatar;
}


/**
 * A utility for general media files that don't have a fallback.
 */
export function buildMediaUrl(url: string | null | undefined): string {
  if (!url) {
    return ''; 
  }
  
  if (url.startsWith('http')) {
    return url;
  }
  
  return `${API_URL_BASE}${url}`;
}