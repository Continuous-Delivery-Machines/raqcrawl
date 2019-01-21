"""Encapsulate SQS.Queue calls."""

import json

import boto3


def dict_for_message(message):
    body_d = json.loads(message.body)
    message.body_dict = body_d
    message.body_raw = message.body
    return message


class SqsMessageQueue:
    """Encapsulates reading boto3.SQS.Queue calls. """

    def __init__(self, botosession: boto3.session.Session, queue_address: str,
                 msg_visibility_timeout: int = 600, wait_time: int = 20):
        self._session = botosession
        self._queue_address = queue_address
        self._msq_queue = self._session.resource('sqs').Queue(self._queue_address)
        self._vis_timeout = msg_visibility_timeout
        self._wait_time = wait_time

    def pop_next_message(self):
        """Receives one message with all attributes available. Uses Long Polling
        as there might be worker refilling the queue. Raises an exception if nothing is received
        as the refilling should take less than 20 seconds. It """
        messages = self._msq_queue.receive_messages(
            AttributeNames=['All'],
            MessageAttributeNames=['All'],
            MaxNumberOfMessages=1,
            VisibilityTimeout=self._vis_timeout,
            WaitTimeSeconds=self._wait_time,
        )
        if not messages:
            raise NoMessagesAfterLongPollingAvailableException("No Messages receivable from Queue")
        elif len(messages) == 1:
            return dict_for_message(messages[0])
        else:
            raise Exception("Received more Messages than intended")

    def write_message(self, message_dict: dict, message_attributes_dict: dict = {}):
        """Writes the provided dict JSON-encoded into the Msg Queue."""
        msg_body = json.dumps(message_dict)
        response = self._msq_queue.send_message(
            MessageBody=msg_body,
            DelaySeconds=0,
            MessageAttributes=message_attributes_dict
        )
        if "MessageId" not in response or "MD5OfMessageBody" not in response:
            raise Exception("")
        return response


class NoMessagesAfterLongPollingAvailableException(Exception):
    """Exception throws when no Messages are received after a Long Polling."""
    pass
