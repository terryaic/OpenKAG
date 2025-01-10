# App/Create Custom Event
import carb.events
import omni.kit.app

# Event is unique integer id. Create it from string by hashing, using helper function.
# [ext name].[event name] is a recommended naming convention:
MY_CUSTOM_EVENT = carb.events.type_from_string("omni.my.extension.MY_CUSTOM_EVENT")

# App provides common event bus. It is event queue which is popped every update (frame).
bus = omni.kit.app.get_app().get_message_bus_event_stream()

def on_event(e):
    print(e.type, e.type == MY_CUSTOM_EVENT, e.payload)

# Subscribe to the bus. Keep subscription objects (sub1, sub2) alive for subscription to work.
# Push to queue is called immediately when pushed
sub1 = bus.create_subscription_to_push_by_type(MY_CUSTOM_EVENT, on_event)
# Pop is called on next update
sub2 = bus.create_subscription_to_pop_by_type(MY_CUSTOM_EVENT, on_event)

# Push event the bus with custom payload
bus.push(MY_CUSTOM_EVENT, payload={"data": 2, "x": "y"})
