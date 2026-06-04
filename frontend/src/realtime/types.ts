export interface DomainEventEnvelope {
  type?: string;
  id?: number;
  service: string;
  event_type: string;
  organization_id: number | null;
  aggregate_type: string;
  aggregate_id: string;
  payload: Record<string, unknown>;
  correlation_id: string;
  created_at: string;
  invalidate_queries?: string[];
}

export interface ConnectionMessage {
  type: "connection.established";
  user_id: number;
  organizations: number[];
  message: string;
}
