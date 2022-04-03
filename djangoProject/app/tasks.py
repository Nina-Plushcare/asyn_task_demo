import uuid
from dataclasses import dataclass, is_dataclass, asdict
from typing import Dict, List, Optional, Any

from celery import group, shared_task


# from analytics_helper.segment_events_registry import SegmentEventsRegistry


@dataclass
class SegmentEventTrackRequest:
    task_uuid: str
    event_name: str
    custom_properties: Dict
    headers: Optional[Dict] = None


@dataclass
class TaskExecutorRequest:
    task: Any
    task_request: Optional[Any] = None


@dataclass
class TaskResponse:
    task_uuid: str
    response: Any


class AsyncTaskExecutor:

    @classmethod
    # TODO: we can add success and error callbacks + timeouts
    # TODO: need to understand the result and see how to handle different results.
    # TODO: leave a note on race conditions on redis keys and db
    def group_signatures(cls, request_list: List[TaskExecutorRequest]) -> group:
        sigs = []
        for r in request_list:
            if r.task_request is None:
                sigs.append(r.task.s())
            elif is_dataclass(r.task_request):
                sigs.append(r.task.s(**asdict(r.task_request)))
            elif isinstance(r.task_request, Dict):
                sigs.append(r.task.s(**r.task_request))
            else:
                raise ValueError
        return group(sigs)

    @classmethod
    def wait_on_results(cls, request_list: List[TaskExecutorRequest], timeout=120) -> List[TaskResponse]:
        return cls.group_signatures(request_list).apply_async().get(timeout)


class AsyncSegmentEventExecutor:
    """
    a wrapper around AsyncTaskExecutor
    fixing track_event_in_segment_async as task to be run
    """

    # for now, choosing comp over inheritance.
    executor: AsyncTaskExecutor = AsyncTaskExecutor

    # @staticmethod
    # @CeleryApp.register_task(**CeleryApp.task_args.SEGMENT_TRACK_EVENT)
    # def track_event_in_segment_async(event_request: SegmentEventTrackRequest) -> Tuple[Optional[bool], Optional[str]]:
    #     return SegmentEventsRegistry.prepare_event(
    #         event_name=event_request.event_name,
    #         custom_properties=event_request.custom_properties,
    #         headers=event_request.headers,
    #         user=event_request.user
    #     )

    @classmethod
    def group_signatures(cls, request_list: List[SegmentEventTrackRequest]) -> group:
        task_list = []
        for r in request_list:
            task_list.append(TaskExecutorRequest(
                task_request=r,
                task=track_event
            ))
        return cls.executor.group_signatures(task_list)

    @classmethod
    def wait_on_results(cls, request_list: List[SegmentEventTrackRequest], timeout=120) -> List[TaskResponse]:
        res = cls.group_signatures(request_list).apply_async().get(timeout)
        return [TaskResponse(task_uuid=r["task_uuid"], response=r["response"]) for r in res]


# Want to test with a dummy task first to reduce complexity of testing
def dummy_prepare_event(**kwargs):
    return True, None


# task results should be json serializable.
@shared_task
def track_event(**kwargs) -> Dict:
    return asdict(TaskResponse(
        task_uuid=kwargs.pop("task_uuid", uuid.uuid4().hex),
        response=dummy_prepare_event(**kwargs)))


def tasks_in_group():
    request = [
        SegmentEventTrackRequest(
            task_uuid="123",
            event_name="Pharmacy Mismatch",
            custom_properties={},
            headers=None
        ), SegmentEventTrackRequest(
            task_uuid="456",
            event_name="Pharmacy Mismatch",
            custom_properties={},
            headers=None
        )]

    a = AsyncSegmentEventExecutor.wait_on_results(request)
    print(a)
    print(type(a))
    for each in a:
        if each.task_uuid == "456":
            print(f'I was interested in the result of task {each.task_uuid}; results: {each.response}')
    return a
