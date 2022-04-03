# asyn_task_demo


make build-up


Just a Proof of concept that this should work. Need to check the variation between our repo and this to see why GroupResult stays in Pending in Plushcare repo


// test:

>>> from app.tasks import tasks_in_group
>>> tasks_in_group()
[TaskResponse(task_uuid='123', response=[True, None]), TaskResponse(task_uuid='456', response=[True, None])]
<class 'list'>
I was interested in the result of task 456; results: [True, None]
[TaskResponse(task_uuid='123', response=[True, None]), TaskResponse(task_uuid='456', response=[True, None])]
