// C:\Users\Vinay\Project\frontend\src\types\index.ts
// --- THIS IS THE COMPLETE, REPLACEMENT CONTENT ---

// --- Core User Types (Unchanged) ---
export interface User {
  id: number
  pk: number
  username: string
  email: string
  first_name: string
  last_name: string
}

export interface CurrentUser extends User {
  profile_picture: string | null
}

// --- Profile Section Types ---
export interface EducationEntry {
  id: number
  institution: string
  degree: string
  field_of_study: string
  university: string
  board: string
  start_date: string | null
  end_date: string | null
  description: string
  location: string
  achievements: string
}

export interface Experience {
  id: number
  title: string
  company: string
  location: string | null
  start_date: string
  end_date: string | null // null implies "Present"
  description: string | null
}

export interface Skill {
  id: number
  name: string
}

// --- NEW: SocialLink Type ---
export interface SocialLink {
  id: number
  link_type: 'linkedin' | 'github' | 'twitter' | 'portfolio'
  url: string
}

// --- UPDATED: The Main UserProfile Type ---
export interface UserProfile {
  user: PostAuthor // Using PostAuthor as it seems to be the public user representation
  display_name: string | null
  headline: string | null
  bio: string | null

  // --- NEW STRUCTURED LOCATION FIELDS ---
  location_city: string | null
  location_administrative_area: string | null
  location_country: string | null
  current_work_style: 'on_site' | 'hybrid' | 'remote' | '' | null
  is_open_to_relocation: boolean
  // --- END NEW FIELDS ---

  resume: string | null
  picture: string | null
  updated_at: string
  relationship_status: {
    connection_status: 'not_connected' | 'request_sent' | 'request_received' | 'connected' | 'self'
    is_followed_by_request_user: boolean
  } | null
  skills: Skill[]
  education: EducationEntry[]
  experience: Experience[]
  interests: string[]

  // --- NEW SOCIAL LINKS FIELD ---
  social_links: SocialLink[]
}

// --- UPDATED: The Payload for Profile Updates ---
export type ProfileUpdatePayload = {
  display_name?: string | null
  headline?: string | null
  bio?: string | null

  // --- NEW PAYLOAD FIELDS ---
  location_city?: string | null
  location_administrative_area?: string | null
  location_country?: string | null
  current_work_style?: 'on_site' | 'hybrid' | 'remote' | '' | null
  is_open_to_relocation?: boolean
  // Use Omit to create a version of SocialLink without the 'id' for creation/updates
  social_links?: Omit<SocialLink, 'id'>[]
  // --- END NEW PAYLOAD FIELDS ---

  interests?: string[]
}

// --- Post-Related Types (Unchanged) ---
export interface PostAuthor {
  id: number
  username: string
  first_name: string
  last_name: string
  picture: string | null
}

export interface PostMedia {
  id: number
  media_type: 'image' | 'video'
  file_url: string
}

export interface PollOption {
  id: number
  text: string
  vote_count: number
}

export interface Poll {
  id: number
  question: string
  options: PollOption[]
  total_votes: number
  user_vote: number | null
}

export interface Post {
  id: number
  post_type: string
  author: PostAuthor
  created_at: string
  updated_at: string
  title: string | null
  content: string | null
  media: PostMedia[]
  poll: Poll | null
  like_count: number
  comment_count?: number
  is_liked_by_user: boolean
  content_type_id: number
  object_id: number
  isLiking?: boolean
  isDeleting?: boolean
  isUpdating?: boolean
  group: { id: number; name: string; slug: string } | null
  is_saved: boolean
}
