export type TripType = 'leisure' | 'business' | 'adventure' | 'family'
export type BagType = 'carry_on' | 'checked' | 'personal'
export type AddedBy = 'activity' | 'adhoc' | 'ai' | 'user'
export type GenderFilter = 'all' | 'male' | 'female'

export interface PackingItem {
  id: number
  list_id: number
  name: string
  quantity: number
  unit: string | null
  is_packed: boolean
  is_essential: boolean
  added_by: AddedBy
  source_activities: string[]
  template_item_id: number | null
  is_customised: boolean
  weight_grams: number | null
  bag_type: BagType | null
  created_at: string
  updated_at: string
}

export interface PackingList {
  id: number
  trip_id: number
  name: string
  description: string | null
  is_default: boolean
  created_at: string
  items: PackingItem[]
}

export interface Trip {
  id: number
  ha_user_id: string | null
  destination: string
  country: string | null
  start_date: string
  end_date: string
  duration_days: number | null
  trip_type: TripType | null
  activities: string[]
  climate_type: string | null
  notes: string | null
  traveller_count: number
  created_at: string
  updated_at: string
  packing_lists: PackingList[]
}

export interface ActivityTemplateItem {
  id: number
  activity_template_id: number
  name: string
  quantity: number
  unit: string | null
  is_essential: boolean
  priority: number
  notes: string | null
  gender_filter: GenderFilter
}

export interface ActivityTemplate {
  id: number
  slug: string
  name: string
  icon_emoji: string
  description: string | null
  is_builtin: boolean
  climate_types: string[]
  items: ActivityTemplateItem[]
}

export interface MergedItem {
  name: string
  quantity: number
  unit: string | null
  is_essential: boolean
  source_activities: string[]
  priority: number
}

export interface PropagationSummary {
  trips_updated: number
  items_added: number
  items_updated: number
  items_removed: number
  items_skipped_customised: number
}

// Form types
export interface TripFormValues {
  destination: string
  country?: string
  start_date: string
  end_date: string
  trip_type?: TripType
  activities: string[]
  notes?: string
  traveller_count: number
}

export interface PackingItemFormValues {
  name: string
  quantity: number
  unit?: string
  is_essential: boolean
  source_activity?: string
  weight_grams?: number
  bag_type?: BagType
}
