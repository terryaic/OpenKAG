# App/Subscribe to Update Events
import carb.events
import omni.kit.app


update_stream = omni.kit.app.get_app().get_update_event_stream()

def on_update(e: carb.events.IEvent):
	print(f"Update: {e.payload['dt']}")

sub = update_stream.create_subscription_to_pop(on_update, name="My Subscription Name")
