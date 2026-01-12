from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has a 'user' attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        return obj == request.user or (hasattr(obj, 'user') and obj.user == request.user)


class IsProfileOwner(permissions.BasePermission):
    """
    Permission to only allow users to edit their own profile
    """

    def has_object_permission(self, request, view, obj):
        # Allow read permissions to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the profile owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return obj == request.user


class IsStaffOrReadOnly(permissions.BasePermission):
    """
    Permission to only allow staff members to edit.
    """

    def has_permission(self, request, view):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to staff
        return request.user and request.user.is_staff