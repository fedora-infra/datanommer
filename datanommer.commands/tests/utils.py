from bodhi.messages.schemas.update import UpdateCommentV1
from fedora_messaging import message as fedora_message


def generate_message(
    topic="org.fedoraproject.test.a.nice.message",
    body=None,
    headers=None,
):
    body = body or {"encouragement": "You're doing great!"}
    return fedora_message.Message(topic=topic, body=body, headers=headers)


def generate_bodhi_update_complete_message():
    msg = UpdateCommentV1(
        body={
            "comment": {
                "karma": -1,
                "text": "text",
                "timestamp": "2019-03-18 16:54:48",
                "update": {
                    "alias": "FEDORA-EPEL-2021-f2d195dada",
                    "builds": [
                        {"nvr": "abrt-addon-python3-2.1.11-50.el7"},
                        {"nvr": "kernel-10.4.0-2.el7"},
                    ],
                    "status": "pending",
                    "release": {"name": "F35"},
                    "request": "testing",
                    "user": {"name": "ryanlerch"},
                },
                "user": {"name": "dudemcpants"},
            }
        }
    )
    msg.topic = f"org.fedoraproject.stg.{msg.topic}"
    return msg
