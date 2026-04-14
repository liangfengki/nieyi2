export interface Persona {
  id: string;
  name: string;
  name_en: string;
  description: string;
  suitable_markets: string[];
}

export interface ShotType {
  id: string;
  name: string;
  name_en: string;
  description: string;
  icon: string;
  category: string;
  needs_persona: boolean;
  aspect_ratio: string;
}

export interface TextLevel {
  id: string;
  name: string;
  name_en: string;
  description: string;
}

export interface BustType {
  id: string;
  name: string;
  name_en: string;
  description: string;
}

export interface SkinTone {
  id: string;
  name: string;
  name_en: string;
  description: string;
}

export interface StrategiesResponse {
  shot_types: Record<string, ShotType>;
  personas: Record<string, Persona>;
  text_levels: Record<string, TextLevel>;
  bust_types: Record<string, BustType>;
  skin_tones: Record<string, SkinTone>;
}

export interface ShotSelection {
  shot_type: string;
}

export interface PlanResult {
  shot_type: string;
  shot_name: string;
  image_url: string;
}

export interface LicenseCode {
  id: string;
  code: string;
  max_images: number | null;
  images_used: number;
  is_active: boolean;
  expires_at: string | null;
  note: string | null;
  created_at: string;
  owner_user_id?: string | null;
}

export interface ProviderPreset {
  id: string;
  name: string;
  base_url: string;
  api_protocol: string;
  default_model: string;
  description: string;
}

export interface UserAPIConfig {
  id: string;
  provider_preset_id: string;
  display_name: string;
  model_name: string;
  api_key: string;
  base_url: string;
  api_protocol: string;
  is_active: boolean;
  purpose: string;
}

export interface SessionUser {
  id: string;
  email: string;
  registered_ip: string | null;
  free_generations_limit: number;
  free_generations_used: number;
  free_remaining: number;
  has_active_license: boolean;
  license_bound: boolean;
}

export interface SessionLicense {
  code: string;
  max_images: number | null;
  images_used: number;
  remaining: number | null;
  expires_at: string | null;
  note: string | null;
  status: string;
}

export interface SessionResponse {
  session_token: string;
  user: SessionUser;
  license: SessionLicense | null;
}

export interface EmailCodeRequestResponse {
  success: boolean;
  message: string;
  expires_in_seconds: number;
  resend_in_seconds: number;
  debug_code?: string | null;
}

export interface AdminDashboardStats {
  total_codes: number;
  active_codes: number;
  total_tasks: number;
  success_rate: string;
  total_images: number;
  total_users: number;
  free_users: number;
}

export interface PlatformApiConfig {
  display_name: string;
  base_url: string;
  api_key: string;
  model_name: string;
  api_protocol: string;
  configured: boolean;
  source: string | null;
  message?: string;
}
