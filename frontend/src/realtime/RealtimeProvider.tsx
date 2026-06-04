import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useAuthStore } from "@/stores/auth";
import { useRealtimeStore } from "@/stores/realtime";
import { OpsWebSocket } from "./OpsWebSocket";
import type { DomainEventEnvelope } from "./types";

let socket: OpsWebSocket | null = null;

export function getOpsSocket() {
  if (!socket) {
    socket = new OpsWebSocket(() => useAuthStore.getState().accessToken);
  }
  return socket;
}

export default function RealtimeProvider({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.accessToken);
  const queryClient = useQueryClient();
  const setStatus = useRealtimeStore((s) => s.setStatus);
  const pushEvent = useRealtimeStore((s) => s.pushEvent);
  const connectedRef = useRef(false);

  useEffect(() => {
    const ops = getOpsSocket();

    const unsubStatus = ops.onStatus((status) => setStatus(status));

    const unsubEvent = ops.onEvent((event: DomainEventEnvelope) => {
      pushEvent(event);
      const keys = event.invalidate_queries ?? [];
      keys.forEach((key) => {
        queryClient.invalidateQueries({ queryKey: [key] });
      });
      if (!keys.length) {
        queryClient.invalidateQueries();
      }
    });

    if (token) {
      ops.connect();
      connectedRef.current = true;
    } else {
      ops.disconnect();
      connectedRef.current = false;
    }

    return () => {
      unsubStatus();
      unsubEvent();
      if (connectedRef.current) ops.disconnect();
    };
  }, [token, queryClient, setStatus, pushEvent]);

  return <>{children}</>;
}
