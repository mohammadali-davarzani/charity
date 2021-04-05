from rest_framework import status, generics
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsCharityOwner, IsBenefactor
from charities.models import Task
from charities.serializers import (
    TaskSerializer, CharitySerializer, BenefactorSerializer
)


class BenefactorRegistration(APIView):
    serializer_class = (BenefactorSerializer, )


    def post(self, request):

        benefactor_serializer = BenefactorSerializer(data=request.data)
        if benefactor_serializer.is_valid():
            benefactor_serializer.save(user=request.user)
            return Response({
                "message" : "user is benefactor saved :)"
            })


        return Response({'message': benefactor_serializer.errors})



class CharityRegistration(APIView):
    serializer_class = (CharitySerializer, )


    def post(self, request):

        charity_serializer = CharitySerializer(data=request.data)
        if charity_serializer.is_valid():
            charity_serializer.save(user=request.user)
            return Response({
                "message" : "user is charity saved :)"
            })


        return Response({'message': charity_serializer.errors})



class Tasks(generics.ListCreateAPIView):
    serializer_class = TaskSerializer

    def get_queryset(self):
        return Task.objects.all_related_tasks_to_user(self.request.user)

    def post(self, request, *args, **kwargs):
        data = {
            **request.data,
            "charity_id": request.user.charity.id
        }
        serializer = self.serializer_class(data = data)
        serializer.is_valid(raise_exception = True)
        serializer.save()
        return Response(serializer.data, status = status.HTTP_201_CREATED)

    def get_permissions(self):
        if self.request.method in SAFE_METHODS:
            self.permission_classes = [IsAuthenticated, ]
        else:
            self.permission_classes = [IsCharityOwner, ]

        return [permission() for permission in self.permission_classes]

    def filter_queryset(self, queryset):
        filter_lookups = {}
        for name, value in Task.filtering_lookups:
            param = self.request.GET.get(value)
            if param:
                filter_lookups[name] = param
        exclude_lookups = {}
        for name, value in Task.excluding_lookups:
            param = self.request.GET.get(value)
            if param:
                exclude_lookups[name] = param

        return queryset.filter(**filter_lookups).exclude(**exclude_lookups)




class TaskRequest(APIView):
    permission_classes = (IsAuthenticated, IsBenefactor)

    def get(self, request, *args, **kwargs):
        task_id = kwargs["task_id"]
        task = get_object_or_404(Task, id=task_id)
        if task:
            if task.state != 'P':
                return Response(data={'detail': 'This task is not pending.'}, status=status.HTTP_404_NOT_FOUND)
            else:
                task.assign_to_benefactor(request.user.benefactor)
                return Response(data={'detail': 'Request sent.'}, status=status.HTTP_200_OK)

        return Response(data={"task":task.title})



class TaskResponse(APIView):
    def post(self, request, task_id):
        if request.data["response"] != "A" and request.data["response"] != "R":
            return Response({
                'detail': 'Required field ("A" for accepted / "R" for rejected)'
            }, status=400)

        else:
            task = Task.objects.get(id = task_id)
            if task.state != "W":
                return Response({
                    'detail': 'This task is not waiting.'
                },status=404 )

            elif request.data["response"] == "A":
                task.state = "A"
                task.save()
                return Response({
                    'detail': 'Response sent.'
                }, status=200)

            elif request.data["response"] == "R":
                task.state = "P"
                task.assigned_benefactor = None
                task.save()
                return Response({
                    'detail': 'Response sent.'
                }, status=200)


class DoneTask(APIView):
    def post(self, request, task_id):
        task = get_object_or_404(Task, id=task_id)
        if task.state != "A":
            return Response({
                'detail': 'Task is not assigned yet.'
            }, status=404)

        else:
            task.state = "D"
            task.save()
            return Response ({
                'detail': 'Task has been done successfully.'
            }, status=200)
