from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from .models import Cliente, Caso, Perfil
from .forms import CasoForm, ClienteForm, UserForm
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test


def is_admin(user):
    return hasattr(user, 'perfil') and user.perfil.rol == 'admin'


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('gestion_cliente')
        else:
            messages.error(request, 'Invalid username or password')
    return render(request, 'login.html')


@login_required
def crear_cliente(request):
    # Handle delete action
    if request.method == 'POST' and 'delete_cliente' in request.POST:
        cliente_id = request.POST.get('delete_cliente')
        cliente = get_object_or_404(Cliente, id=cliente_id)
        # Check permissions
        if request.user.perfil.rol == 'admin' or cliente.creado_por == request.user:
            cliente.delete()
            messages.success(request, 'Cliente eliminado exitosamente')
        else:
            messages.error(request, 'No tiene permisos para eliminar este cliente')
        return redirect('gestion_cliente')

    # Handle create action
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save(commit=False)
            if request.user.is_authenticated:
                cliente.creado_por = request.user
                cliente.save()
                messages.success(request, 'Cliente creado exitosamente')
            else:
                return redirect('login')
        else:
            messages.error(request, 'Error al crear cliente. Verifique los datos ingresados.')
    else:
        form = ClienteForm()

    clientes = Cliente.objects.all()
    return render(request, 'crear_cliente.html', {'form': form, 'clientes': clientes})


@login_required
def crear_caso(request):
    # Handle delete action
    if request.method == 'POST' and 'delete_caso' in request.POST:
        caso_id = request.POST.get('delete_caso')
        caso = get_object_or_404(Caso, id=caso_id)
        # Check permissions
        if request.user.perfil.rol == 'admin' or caso.asignado_a == request.user:
            caso.delete()
            messages.success(request, 'Caso eliminado exitosamente')
        else:
            messages.error(request, 'No tiene permisos para eliminar este caso')
        return redirect('crear_caso')

    # Handle create action
    if request.method == 'POST':
        form = CasoForm(request.POST)
        if form.is_valid():
            caso = form.save(commit=False)
            # Solo asignar el usuario actual si no se seleccionó ninguno
            if not caso.asignado_a:
                caso.asignado_a = request.user
            caso.save()
            messages.success(request, 'Caso creado exitosamente')
        else:
            messages.error(request, 'Error al crear caso. Verifique los datos ingresados.')
    else:
        form = CasoForm()

    casos = Caso.objects.all()
    return render(request, 'crear_caso.html', {'form': form, 'casos': casos})

@login_required
def vista_tablas(request):
    # Handle delete actions
    if request.method == 'POST':
        if 'delete_cliente' in request.POST:
            cliente_id = request.POST.get('delete_cliente')
            cliente = get_object_or_404(Cliente, id=cliente_id)
            # Check permissions
            if request.user.perfil.rol == 'admin' or cliente.creado_por == request.user:
                cliente.delete()
                messages.success(request, 'Cliente eliminado exitosamente')
            else:
                messages.error(request, 'No tiene permisos para eliminar este cliente')
            return redirect('vista_tablas')

        elif 'delete_caso' in request.POST:
            caso_id = request.POST.get('delete_caso')
            caso = get_object_or_404(Caso, id=caso_id)
            # Check permissions
            if request.user.perfil.rol == 'admin' or caso.asignado_a == request.user:
                caso.delete()
                messages.success(request, 'Caso eliminado exitosamente')
            else:
                messages.error(request, 'No tiene permisos para eliminar este caso')
            return redirect('vista_tablas')

    # Check if user has admin role
    is_admin = hasattr(request.user, 'perfil') and request.user.perfil.rol == 'admin'

    if is_admin:
        # Admin sees all data
        clientes = Cliente.objects.all()
        casos = Caso.objects.all()
        casos_abiertos = Caso.objects.filter(estado='Abierto')
        casos_cerrados = Caso.objects.filter(estado='Cerrado')
    else:
        # Abogado only sees data related to them
        clientes = Cliente.objects.filter(creado_por=request.user)
        casos = Caso.objects.filter(asignado_a=request.user)
        casos_abiertos = Caso.objects.filter(estado='Abierto', asignado_a=request.user)
        casos_cerrados = Caso.objects.filter(estado='Cerrado', asignado_a=request.user)

    return render(request, 'vista_tablas.html', {
        'clientes': clientes,
        'casos': casos,
        'casos_abiertos': casos_abiertos,
        'casos_cerrados': casos_cerrados,
    })


@login_required
@user_passes_test(is_admin)
def gestion_usuarios(request):
    # Handle delete action
    if request.method == 'POST' and 'delete_usuario' in request.POST:
        usuario_id = request.POST.get('delete_usuario')
        usuario = get_object_or_404(User, id=usuario_id)

        if usuario.username == 'admin' or usuario.id == request.user.id:
            messages.error(request, 'No se puede eliminar al usuario admin ni a sí mismo')
        else:
            usuario.delete()
            messages.success(request, 'Usuario eliminado exitosamente')
        return redirect('gestion_usuarios')

    # Handle create action
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            # Create or update the Perfil instance
            Perfil.objects.create(usuario=user, rol=form.cleaned_data['rol'])

            messages.success(request, 'Usuario creado exitosamente')
        else:
            messages.error(request, 'Error al crear usuario. Verifique los datos ingresados.')
    else:
        form = UserForm()

    usuarios = User.objects.all()
    return render(request, 'gestion_usuarios.html', {'form': form, 'usuarios': usuarios})