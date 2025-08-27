from typing import List

from rest_framework import serializers


class ProjectMembersAssignmentSerializer(serializers.Serializer):
    add = serializers.ListField(
        child=serializers.IntegerField(min_value=1), required=False, allow_empty=True, default=list
    )
    remove = serializers.ListField(
        child=serializers.IntegerField(min_value=1), required=False, allow_empty=True, default=list
    )


class ProjectMembersEnableSerializer(serializers.Serializer):
    enable = serializers.ListField(
        child=serializers.IntegerField(min_value=1), required=False, allow_empty=True, default=list
    )
    disable = serializers.ListField(
        child=serializers.IntegerField(min_value=1), required=False, allow_empty=True, default=list
    )


class TaskAssignLocksSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(min_value=1)
    task_ids: List[int] = serializers.ListField(
        child=serializers.IntegerField(min_value=1), allow_empty=False
    )


class TaskAssignSingleSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(min_value=1)
