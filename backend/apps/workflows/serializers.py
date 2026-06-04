from rest_framework import serializers

from .models import Workflow, WorkflowEdge, WorkflowNode, WorkflowTemplate, WorkflowVersion


class WorkflowNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowNode
        fields = (
            "id",
            "key",
            "node_type",
            "label",
            "config",
            "position_x",
            "position_y",
            "retry_policy",
            "timeout_seconds",
        )


class WorkflowEdgeSerializer(serializers.ModelSerializer):
    source_key = serializers.CharField(source="source.key", read_only=True)
    target_key = serializers.CharField(source="target.key", read_only=True)

    class Meta:
        model = WorkflowEdge
        fields = ("id", "source", "target", "source_key", "target_key", "condition", "label")


class WorkflowSerializer(serializers.ModelSerializer):
    nodes = WorkflowNodeSerializer(many=True, read_only=True)
    edges = WorkflowEdgeSerializer(many=True, read_only=True)
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = Workflow
        fields = (
            "id",
            "organization",
            "department",
            "department_name",
            "name",
            "slug",
            "description",
            "status",
            "trigger_type",
            "trigger_config",
            "variables_schema",
            "sla_hours",
            "version",
            "template",
            "nodes",
            "edges",
            "created_by",
            "updated_at",
            "created_at",
        )
        read_only_fields = ("id", "version", "created_by", "updated_at", "created_at")


class WorkflowWriteSerializer(serializers.ModelSerializer):
    graph = serializers.JSONField(write_only=True, required=False)

    class Meta:
        model = Workflow
        fields = (
            "organization",
            "department",
            "name",
            "slug",
            "description",
            "status",
            "trigger_type",
            "trigger_config",
            "variables_schema",
            "sla_hours",
            "template",
            "graph",
        )

    def _sync_graph(self, workflow, graph: dict):
        if not graph:
            return
        workflow.nodes.all().delete()
        key_to_node = {}
        for node_data in graph.get("nodes", []):
            node = WorkflowNode.objects.create(
                workflow=workflow,
                key=node_data["key"],
                node_type=node_data["type"],
                label=node_data.get("label", node_data["key"]),
                config=node_data.get("config", {}),
                position_x=node_data.get("x", 0),
                position_y=node_data.get("y", 0),
                retry_policy=node_data.get("retry_policy", {}),
                timeout_seconds=node_data.get("timeout_seconds"),
            )
            key_to_node[node.key] = node
        for edge_data in graph.get("edges", []):
            source = key_to_node.get(edge_data["source"])
            target = key_to_node.get(edge_data["target"])
            if source and target:
                WorkflowEdge.objects.create(
                    workflow=workflow,
                    source=source,
                    target=target,
                    label=edge_data.get("label", ""),
                    condition=edge_data.get("condition", {}),
                )

    def create(self, validated_data):
        graph = validated_data.pop("graph", None)
        validated_data["created_by"] = self.context["request"].user
        workflow = super().create(validated_data)
        self._sync_graph(workflow, graph)
        return workflow

    def update(self, instance, validated_data):
        graph = validated_data.pop("graph", None)
        workflow = super().update(instance, validated_data)
        if graph is not None:
            instance.version += 1
            instance.save(update_fields=["version"])
            WorkflowVersion.objects.create(
                workflow=workflow,
                version_number=workflow.version,
                snapshot=graph,
                published_by=self.context["request"].user,
            )
            self._sync_graph(workflow, graph)
        return workflow


class WorkflowTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowTemplate
        fields = (
            "id",
            "name",
            "slug",
            "category",
            "description",
            "definition",
            "variables_schema",
            "is_public",
            "created_at",
        )
