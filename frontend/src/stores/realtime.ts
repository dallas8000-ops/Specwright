import { create } from "zustand";
import type { DomainEventEnvelope } from "@/realtime/types";

interface RealtimeState {
  status: "connecting" | "connected" | "disconnected" | "error";
  lastEvent: DomainEventEnvelope | null;
  feed: DomainEventEnvelope[];
  setStatus: (status: RealtimeState["status"]) => void;
  pushEvent: (event: DomainEventEnvelope) => void;
  clearFeed: () => void;
}

const MAX_FEED = 50;

export const useRealtimeStore = create<RealtimeState>((set) => ({
  status: "disconnected",
  lastEvent: null,
  feed: [],
  setStatus: (status) => set({ status }),
  pushEvent: (event) =>
    set((s) => ({
      lastEvent: event,
      feed: [event, ...s.feed].slice(0, MAX_FEED),
    })),
  clearFeed: () => set({ feed: [], lastEvent: null }),
}));
