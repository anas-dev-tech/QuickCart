import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from orders.models import Order
from .tasks import payment_completed
from shop.recommender import Recommender
from icecream import ic
from shop.models import Product

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None
    
    try:
        event = stripe.Webhook.construct_event(
            payload,
            sig_header,
            settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e: 
        # Invalid payload   
        return HttpResponse(status=400) 
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)
    if event.type == 'checkout.session.completed':
        session = event.data.object
        if session.mode == 'payment' and session.payment_status == 'paid':
            try:
                order = Order.objects.get(id=session.client_reference_id)
            except Order.DoesNotExist:
                return HttpResponse(status=404)
            
            # mark order as paid
            order.paid = True
            
            ordered_product_ids = order.items.values_list('product', flat=True)
            if len(ordered_product_ids) > 1:
                ordered_products = Product.objects.filter(id__in=ordered_product_ids)
                ic(ordered_products)
                r = Recommender()
                r.products_bought(ordered_products)
            
            
            
            order.stripe_id = session.payment_intent
            order.save()
            
            payment_completed.delay(order.id)
                
    return HttpResponse(status=200)