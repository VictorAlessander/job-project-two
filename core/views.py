from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from .models import Category, Product, MCart, Order
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from .forms import FilterForm
from django import forms
from django.http import JsonResponse


class Index(TemplateView):
	template_name = 'index.html'


@login_required
def category_list(request):

	categories = Category.objects.all()

	return render(request, 'categories.html', {'categories': categories})


@login_required
def product_list(request, category):

	products = Product.objects.filter(category__name=category)

	return render(request, 'products.html', {'products': products})


@login_required
def add_to_cart(request):

	user = request.user
	item_cod = request.GET['cod']

	item = get_object_or_404(Product, cod=item_cod)

	if MCart.objects.filter(name=item.name, owner=user).exists():
		increase_item = MCart.objects.get(cod=item_cod, name=item.name, owner=user)
		increase_item.quantity = increase_item.quantity + 1
		increase_item.save()

	else:
		add = MCart.objects.create(
			cod=item.cod,
			name=item.name,
			price=item.price,
			owner=user,
			)

	return JsonResponse({'data': 'Added to cart.'})


@login_required
def remove_of_cart(request, item_cod):

	user = request.user
	item = get_object_or_404(MCart, cod=item_cod, owner=user)

	if MCart.objects.filter(name=item.name, owner=user).exists():
		item.delete()

	return redirect('core:cart')


@login_required
def increase_product(request, item_cod):

	user = request.user

	item = get_object_or_404(MCart, cod=item_cod, owner=user)

	if MCart.objects.filter(name=item.name, owner=user).exists():
		increase_item = MCart.objects.get(cod=item_cod, name=item.name, owner=user)
		increase_item.quantity = increase_item.quantity + 1
		increase_item.save()

	else:
		MCart.objects.create(
			cod=item.cod,
			name=item.name,
			price=item.price,
			owner=user,
			)

	return redirect('core:cart')


@login_required
def decrease_product(request, item_cod):

	user = request.user
	item = get_object_or_404(MCart, cod=item_cod, owner=user)

	if MCart.objects.filter(name=item.name, owner=user).exists():
		decrease_item = MCart.objects.get(id=item.id, cod=item_cod, name=item.name, owner=user)
		if decrease_item.quantity > 1:
			decrease_item.quantity = decrease_item.quantity - 1
			decrease_item.save()

	return redirect('core:cart')


@login_required
def cart(request):

	user = request.user
	session = request.COOKIES['sessionid']

	item_list = MCart.objects.all().filter(owner=user)
	total_price = MCart()
	total_price = total_price.total(user)

	return render(request, 'cart.html', {'item_list': item_list, 'total_price': total_price, 'session': session})


@login_required
def checkout(request):

	user = request.user
	order = MCart.objects.all().filter(owner=user)
	total_price = MCart()
	total_price = total_price.total(user)

	return render(request, 'checkout.html', {'order': order, 'order_price': total_price})


@login_required
def submit_order(request):

	user = request.user # Get the logged user
	session = request.COOKIES['sessionid']
	cart = MCart.objects.all().filter(owner=user)

	for item in cart:
		if Order.objects.filter(id=item.id, name=item.name, owner=user).exists():
			increase_item = Order.objects.get(name=item.name, owner=user)
			increase_item.quantity = increase_item.quantity + 1
			increase_item.save()

		else:
			submit = Order.objects.create(
				cod=item.cod,
				name=item.name,
				price=item.price,
				quantity=item.quantity,
				owner=user,
				order_id=session,
				)

			submit.save_order()

	# Django will logout the user and give him a new session cookie
	request.session.modified = True
	request.session.flush()

	# Will clear the cart
	cart.delete()

	# Then, automatically redirects user to reauthentication
	return redirect('social:begin', backend='facebook')


@login_required
def order_list(request):

	user = request.user
	total_price = None
	orders = None

	if request.method == 'POST':
		form = FilterForm(user, request.POST or None)

		if form.is_valid():
			field_content = {
				'order_id': request.POST['order_id']
			}
			
			if field_content['order_id']:
				orders = Order.objects.filter(
					order_id=form.cleaned_data.get('order_id'),
					owner=user
				)
				total_price = Order()
				total_price = total_price.total(form.cleaned_data.get('order_id'), user)

	else:
		form = FilterForm(user)

	return render(request, 'order_list.html', {'orders': orders, 'form': form, 'total_price': total_price})