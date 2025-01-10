# App/Subscribe to Shutdown Events
import carb.events
import omni.kit.app

# Stream where app sends shutdown events
shutdown_stream = omni.kit.app.get_app().get_shutdown_event_stream()

def on_event(e: carb.events.IEvent):
    if e.type == omni.kit.app.POST_QUIT_EVENT_TYPE:
        print("We are about to shutdown")

sub = shutdown_stream.create_subscription_to_pop(on_event, name="name of the subscriber for debugging", order=0)

