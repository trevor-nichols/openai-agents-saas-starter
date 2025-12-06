export interface ActivityEvent {
  id: string;
  tenant_id: string;
  action: string;
  created_at: string;
  actor_id?: string | null;
  actor_type?: string | null;
  actor_role?: string | null;
  object_type?: string | null;
  object_id?: string | null;
  object_name?: string | null;
  status: 'success' | 'failure' | 'pending';
  source?: string | null;
  request_id?: string | null;
  ip_hash?: string | null;
  user_agent?: string | null;
  metadata?: Record<string, unknown> | null;
  read_state?: ActivityReceiptStatus;
}

export interface ActivityListPage {
  items: ActivityEvent[];
  next_cursor: string | null;
  unread_count?: number;
}

export type ActivityReceiptStatus = 'unread' | 'read' | 'dismissed';
