# USD/Subscribe to USD Stage Events
import carb.events
import omni.usd


def on_stage_event(e: carb.events.IEvent):
	print(f"Stage Event: {e.type} {e.payload}")


stage_event_sub = (
	omni.usd.get_context()
	.get_stage_event_stream()
	.create_subscription_to_pop(on_stage_event, name="My Subscription Name")
)
