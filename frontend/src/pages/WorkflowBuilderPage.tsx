import { useCallback, useMemo } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  type Connection,
  type Node,
  type Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { api } from "@/api/client";
import type { Workflow } from "@/types";
import styles from "./WorkflowBuilderPage.module.css";

const NODE_COLORS: Record<string, string> = {
  trigger: "#3b82f6",
  approval: "#f59e0b",
  integration: "#22c55e",
  condition: "#a78bfa",
  notification: "#f472b6",
  action: "#64748b",
};

function workflowToFlow(workflow: Workflow): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = workflow.nodes.map((n) => ({
    id: n.key,
    type: "default",
    position: { x: n.position_x, y: n.position_y },
    data: { label: `${n.label}\n(${n.node_type})` },
    style: {
      background: NODE_COLORS[n.node_type] ?? "#334155",
      color: "#fff",
      border: "none",
      borderRadius: 8,
      fontSize: 12,
      padding: 8,
      minWidth: 140,
    },
  }));
  const edges: Edge[] = workflow.edges.map((e, i) => ({
    id: `e-${i}`,
    source: e.source_key,
    target: e.target_key,
    label: e.label || undefined,
  }));
  return { nodes, edges };
}

export default function WorkflowBuilderPage() {
  const { slug } = useParams<{ slug: string }>();
  const { data: workflow } = useQuery({
    queryKey: ["workflow", slug],
    queryFn: async () => (await api.get<Workflow>(`/workflows/${slug}/`)).data,
    enabled: !!slug,
  });

  const initial = useMemo(
    () => (workflow ? workflowToFlow(workflow) : { nodes: [], edges: [] }),
    [workflow]
  );

  const [nodes, setNodes, onNodesChange] = useNodesState(initial.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initial.edges);

  const onConnect = useCallback(
    (connection: Connection) => setEdges((eds) => addEdge(connection, eds)),
    [setEdges]
  );

  if (!workflow) return <p>Loading workflow…</p>;

  return (
    <div className={styles.page}>
      <header>
        <h2>{workflow.name}</h2>
        <p>Visual builder — drag nodes, connect steps, publish when ready.</p>
      </header>
      <div className={styles.canvas}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          fitView
        >
          <Background gap={16} color="#2a3548" />
          <Controls />
          <MiniMap />
        </ReactFlow>
      </div>
    </div>
  );
}
