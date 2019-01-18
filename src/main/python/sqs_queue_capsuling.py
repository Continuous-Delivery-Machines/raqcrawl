"""Encapsulate SQS.Queue calls."""

import boto3


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
            return messages[0]
        else:
            raise Exception("Received more Messages than intended")

    def write_message(self, message: dict):
        """Writes the provided dict JSON-encoded into the Msg Queue."""
        pass


class NoMessagesAfterLongPollingAvailableException(Exception):
    """Exception throws when no Messages are received after a Long Polling."""
    pass
