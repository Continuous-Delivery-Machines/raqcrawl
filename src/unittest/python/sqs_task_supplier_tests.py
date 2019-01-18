"""Unit tests concerning the SqsTaskSupplier"""
import json
import os
import unittest
from time import sleep

import boto3
from botocore import exceptions
from hamcrest import assert_that, calling, raises, is_not, is_, has_key, not_

from sqs_queue_capsuling import SqsMessageQueue, NoMessagesAfterLongPollingAvailableException


class SqsTaskSupplierTests(unittest.TestCase):
    """TestCase covering the pop of single messages from the
    SQS Msg Queue in TEST stage provided by the environment.

    Purges the content of the provided Queue."""
    aws_id = None
    aws_secret = None
    queue_address = None

    @classmethod
    def setUpClass(cls):
        """Receives the configuration of the AWS account and SQS Msg
        Queue associated with the TEST stage. Tries for one minute to
        purge the queue to ensure reproducibility.

        Every Message created ba a test MUST be deleted afterwards, regardless
        of whether the test was successful or not. Any asserts are supposed to
        happen AFTER the queue has been cleaned for the next tests."""

        cls.aws_id = os.environ.get('RAQ_CRAWLER_TEST_AWS_ID')
        cls.aws_secret = os.environ.get('RAQ_CRAWLER_TEST_AWS_SECRET')
        cls.queue_address = os.environ.get("RAQ_CRAWLER_TEST_QUEUE")
        cls.boto_session = boto3.session.Session(aws_access_key_id=cls.aws_id,
                                                 aws_secret_access_key=cls.aws_secret,
                                                 region_name='us-east-1')
        cls.msg_queue = cls.boto_session.resource('sqs').Queue(cls.queue_address)
        cls.msg_queue.load()
        for i in range(1, 10):
            try:
                print('Purge attempt {}'.format(i))
                cls.msg_queue.purge()
                print('Done... hopefully')
                break
            except exceptions.ClientError as exception:
                print('Waiting 6sec because of likely PurgeInProgress')
                print(exception)
                sleep(6)
            if i == 10:
                raise Exception('Unsuccessful purge of MsgQueue')

    @classmethod
    def tearDownClass(cls):
        """If a way is found to close the Socket associated with one of them,
        put it here."""
        print("tearDownClass")
        del cls.msg_queue
        del cls.boto_session
        print("tearDownClass end")

    def tearDown(self):
        """Delete all contents of the queue for the next test."""
        print("tearDown")
        msgs = self.get_up_to_ten_messages()
        while msgs:
            del_entries = map(lambda msg: {'Id': msg.message_id, 'ReceiptHandle': msg.receipt_handle}, msgs)
            del_dict = self.msg_queue.delete_messages(Entries=del_entries)
            if "Failed" in del_dict:
                raise Exception('Failed to clean messages during tearDown {}'.format(del_entries))
            msgs = self.get_up_to_ten_messages()
        print("tearDown end")

    def get_up_to_ten_messages(self):
        """Returns as many messages as possible with all their data available"""
        return self.msg_queue.receive_messages(
            AttributeNames=['All'],
            MessageAttributeNames=['All'],
            MaxNumberOfMessages=10,
            VisibilityTimeout=600,
            WaitTimeSeconds=1,
        )

    def test_pop_on_empty_queue(self):
        """Tests behaviour of supplier on an empty Msg Queue"""
        queue = SqsMessageQueue(botosession=self.boto_session,
                                queue_address=self.queue_address,
                                wait_time=1)

        assert_that(calling(queue.pop_next_message), raises(NoMessagesAfterLongPollingAvailableException))

    def test_pop_single_message(self):
        """Tests behaviour on Msg Queue with one msg in it."""
        queue = SqsMessageQueue(botosession=self.boto_session,
                                queue_address=self.queue_address,
                                wait_time=1)

        orig_data_dict = {'task': 'test', 'values': {'a': 1, 'c': "what"}}
        msg = json.dumps(orig_data_dict)
        self.msg_queue.send_message(
            MessageBody=msg,
            DelaySeconds=0,
        )
        pop = queue.pop_next_message()
        received_body_dict = json.loads(pop.body)

        assert_that(pop, is_not(None))
        assert_that(received_body_dict, is_(orig_data_dict))

    def test_write_single_message_no_attributes(self):
        """Sends a message with body into the queue and receives it"""
        queue = SqsMessageQueue(botosession=self.boto_session,
                                queue_address=self.queue_address,
                                wait_time=1)

        data = {'a': 'A', 'langs': {'C': 1234, 'python': 8765}}
        response = queue.write_message(message=data)
        assert_that(response, has_key('MD5OfMessageBody'))
        assert_that(response, not_(has_key('MD5OfMessageAttributes')))
        assert_that(response, has_key('MessageId'))

        received_msg = queue.pop_next_message()
        received_dict = json.loads(received_msg.body)
        assert_that(received_dict, is_(data))

    def test_write_single_message_with_attributes(self):
        """Sends a message with body into the queue and receives it"""
        queue = SqsMessageQueue(botosession=self.boto_session,
                                queue_address=self.queue_address,
                                wait_time=1)

        data = {'a': 'A', 'langs': {'C': 1234, 'python': 8765}}
        attrs = {'key_name': {'StringValue': 'ma_val', 'DataType': 'String'}}
        response = queue.write_message(message=data, message_attributes=attrs)
        assert_that(response, has_key('MD5OfMessageBody'))
        assert_that(response, has_key('MD5OfMessageAttributes'))
        assert_that(response, has_key('MessageId'))

        received_msg = queue.pop_next_message()
        received_dict = json.loads(received_msg.body)
        assert_that(received_dict, is_(data))
        assert_that(received_msg.message_attributes, is_(attrs))
