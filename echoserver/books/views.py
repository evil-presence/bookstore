from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import CustomUser, Book, CartItem, Order, OrderItem
from .forms import CustomUserCreationForm, CustomAuthenticationForm, BookForm, ProfileForm, CustomPasswordChangeForm
from django.db import transaction
from decimal import Decimal
from django.http import JsonResponse

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

def book_list(request):
    books = Book.objects.all()
    author_filter = request.GET.get('author', '')
    if author_filter:
        books = books.filter(author__icontains=author_filter)
    paginator = Paginator(books, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'books/book_list.html', {'page_obj': page_obj, 'author_filter': author_filter})

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            transfer_session_cart_to_db(request, user)  # Перенос корзины из сессии
            return redirect('book_list')
    else:
        form = CustomUserCreationForm()
    return render(request, 'books/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            transfer_session_cart_to_db(request, user)  # Перенос корзины из сессии
            return redirect('book_list')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'books/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('book_list')

@login_required
def book_create(request):
    if request.method == 'POST':
        form = BookForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('book_list')
    else:
        form = BookForm()
    return render(request, 'books/book_form.html', {'form': form, 'title': 'Добавить книгу'})

@login_required
@user_passes_test(is_admin)
def book_update(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        form = BookForm(request.POST, instance=book)
        if form.is_valid():
            form.save()
            return redirect('book_list')
    else:
        form = BookForm(instance=book)
    return render(request, 'books/book_form.html', {'form': form, 'title': 'Изменить книгу'})

@login_required
@user_passes_test(is_admin)
def book_delete(request, pk):
    book = get_object_or_404(Book, pk=pk)
    if request.method == 'POST':
        book.delete()
        return redirect('book_list')
    return render(request, 'books/book_confirm_delete.html', {'book': book})

@login_required
def profile(request):
    if request.method == 'POST':
        profile_form = ProfileForm(request.POST, instance=request.user)
        password_form = CustomPasswordChangeForm(user=request.user, data=request.POST)
        if 'update_profile' in request.POST and profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Профиль успешно обновлён.')
            return redirect('profile')
        elif 'change_password' in request.POST and password_form.is_valid():
            password_form.save()
            login(request, request.user)
            messages.success(request, 'Пароль успешно изменён.')
            return redirect('profile')
    else:
        profile_form = ProfileForm(instance=request.user)
        password_form = CustomPasswordChangeForm(user=request.user)
    return render(request, 'books/profile.html', {
        'profile_form': profile_form,
        'password_form': password_form
    })

def add_to_cart(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    if request.user.is_authenticated:
        cart_item, created = CartItem.objects.get_or_create(user=request.user, book=book)
        if not created:
            cart_item.quantity += 1
            cart_item.save()
    else:
        cart = request.session.get('cart', {})
        book_id_str = str(book_id)
        if book_id_str in cart:
            cart[book_id_str]['quantity'] += 1
        else:
            cart[book_id_str] = {
                'quantity': 1,
                'title': book.title,
                'price': str(book.price)
            }
        request.session['cart'] = cart
    return redirect('book_list')

def cart(request):
    if request.user.is_authenticated:
        transfer_session_cart_to_db(request, request.user)
        cart_items = CartItem.objects.filter(user=request.user)
        total_price = sum(item.total_price for item in cart_items)
        if request.method == 'POST' and 'clear_cart' in request.POST:
            cart_items.delete()
            messages.success(request, 'Корзина очищена.')
            return redirect('cart')
    else:
        cart = request.session.get('cart', {})
        cart_items = [
            {
                'book': {'title': item['title'], 'price': Decimal(item['price'])},
                'quantity': item['quantity'],
                'total_price': item['quantity'] * Decimal(item['price'])
            }
            for item in cart.values()
        ]
        total_price = sum(item['total_price'] for item in cart_items)
        if request.method == 'POST' and 'clear_cart' in request.POST:
            if 'cart' in request.session:
                del request.session['cart']
            messages.success(request, 'Корзина очищена.')
            return redirect('cart')
    return render(request, 'books/cart.html', {'cart_items': cart_items, 'total_price': total_price})

@login_required
def checkout(request):
    if request.method == 'POST':
        cart_items = CartItem.objects.filter(user=request.user)
        if not cart_items:
            return redirect('cart')
        with transaction.atomic():
            total_price = sum(item.total_price for item in cart_items)
            order = Order.objects.create(user=request.user, total_price=total_price)
            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    book=item.book,
                    book_title=item.book.title,
                    book_author=item.book.author,
                    book_price=item.book.price,
                    quantity=item.quantity
                )
            cart_items.delete()
        messages.success(request, 'Заказ успешно оформлен.')
        return redirect('orders')
    return render(request, 'books/checkout.html')

@login_required
def orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'books/orders.html', {'orders': orders})

def transfer_session_cart_to_db(request, user):
    if 'cart' in request.session:
        for book_id, item in request.session['cart'].items():
            book = get_object_or_404(Book, id=book_id)
            cart_item, created = CartItem.objects.get_or_create(user=user, book=book)
            if not created:
                cart_item.quantity += item['quantity']
            else:
                cart_item.quantity = item['quantity']
            cart_item.save()
        del request.session['cart']

def check_email(request):
    email = request.GET.get('email', '')
    exists = CustomUser.objects.filter(email=email).exists()
    return JsonResponse({'exists': exists})