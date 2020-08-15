import stripe

from django.shortcuts import render, redirect
from django.views.decorators.http import require_GET, require_POST

from crossbox.models.card import Card
from crossbox.models.fee import Fee


@require_GET
def profile(request):
    subscriber = request.user.subscriber
    user_cards = Card.objects.filter(subscriber=subscriber)
    empty_fee_option = {None: {'selected': False, 'label': 'Sin cuota'}}
    fees = [empty_fee_option]
    for fee in Fee.objects.all():
        selected = (
            bool(subscriber.fee.pk == fee.pk)
            if subscriber.fee
            else False
        )
        select_option = {'selected': selected, 'label': fee.label}
        fees.append({fee.pk: select_option})
    return render(
        request,
        'profile.html',
        {'user_cards': user_cards, 'fees': fees},
    )


@require_POST
def change_cuota(request):
    fee_pk = request.POST['fee']
    fee = Fee.objects.get(pk=fee_pk)
    subscriber = request.user.subscriber
    subscriber.fee = fee
    subscriber.save()
    return redirect('profile')


@require_POST
def add_payment_method(request):
    card_token = request.POST['stripeToken']
    subscriber = request.user.subscriber
    stripe_card = stripe.Customer.create_source(
        subscriber.stripe_customer_id,
        source=card_token,
    )
    default_card = not bool(Card.objects.filter(subscriber=subscriber).count())
    Card.objects.create(
        last_digits=stripe_card['last4'],
        subscriber=subscriber,
        default=default_card,  # True if is the first card, False for next ones
        stripe_card_id=stripe_card['id'],
    )
    return redirect('profile')


@require_POST
def set_default_payment_method(request):
    subscriber = request.user.subscriber
    stripe_card_id = request.POST['stripe_card_id']
    stripe.Customer.modify(
        subscriber.stripe_customer_id,
        default_source=stripe_card_id,
    )
    user_cards = Card.objects.filter(subscriber=subscriber)
    for user_card in user_cards:
        if user_card.stripe_card_id == stripe_card_id:
            new_default_card = user_card
        if user_card.default:
            user_card.default = False
            user_card.save()
    new_default_card.default = True
    new_default_card.save()
    return redirect('profile')


@require_POST
def delete_card(request):
    subscriber = request.user.subscriber
    stripe_card_id = request.POST['stripe_card_id']
    stripe.Customer.delete_source(
        subscriber.stripe_customer_id,
        stripe_card_id,
    )
    card_to_delete = Card.objects.filter(stripe_card_id=stripe_card_id).first()
    card_to_delete.delete()
    if card_to_delete.default:
        card_to_be_default = Card.objects.filter(subscriber=subscriber).first()
        if card_to_be_default:
            card_to_be_default.default = True
            card_to_be_default.save()
    return redirect('profile')