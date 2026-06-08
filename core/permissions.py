from rest_framework import permissions

class IsAdmin(permissions.BasePermission):
    """
    Permite el acceso solo a usuarios con el rol ADMIN.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and 
                    (request.user.is_superuser or (request.user.role and request.user.role.name == 'ADMIN')))

class IsAdminOrOwner(permissions.BasePermission):
    """
    Control de Acceso a Nivel de Objeto (Prevención BOLA).
    Permite a los médicos acceder solo a sus propios datos,
    mientras que el administrador tiene acceso a todos.
    """
    def has_permission(self, request, view):
        # Primero debe estar autenticado
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        # Si es Administrador o Superuser, tiene acceso total
        if request.user.is_superuser or (request.user.role and request.user.role.name == 'ADMIN'):
            return True
        
        # Si no es administrador, validamos que sea el dueño del objeto
        # Asumiendo que el objeto tiene un campo `usuario` relacionado al User model
        if hasattr(obj, 'usuario'):
            return obj.usuario == request.user
        
        return False
