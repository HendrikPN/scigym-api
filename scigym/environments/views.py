import logging
import re
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action

from rest_framework import viewsets, status

from scigym.repositories.models import Repository
from .models import Environment, Topic, Image
from .serializers import (
    EnvironmentSerializer,
    EnvironmentWriteSerializer,
    EnvironmentFormSerializer,
    TopicSerializer
)

from scigym.config.permissions import IsAdminOrReadOnly
from .permissions import IsOwnerOrReadOnly
from scigym.utils.helper import is_valid_uuid

logger = logging.getLogger('django')

WRITE_VERBS = ['POST', 'PUT']


class EnvironmentViewSet(viewsets.ModelViewSet):
    """
    View to create environments
    """
    queryset = Environment.objects.all()
    serializer_class = EnvironmentSerializer
    permission_classes = (IsOwnerOrReadOnly,)

    def get_serializer_class(self):
        return EnvironmentWriteSerializer if self.request.method in WRITE_VERBS else self.serializer_class

    def create(self, request):

        # get image
        if is_valid_uuid(request.data['avatar']):
            avatar = Image.objects.get(id=request.data['avatar'])
        else:
            avatar = None
        env_name = request.data['name']
        env_url = re.sub(' {1,}', '-', env_name)

        repo = get_object_or_404(Repository, pk=request.data['repository'])

        env_data = {
            'name': env_name,
            'url': env_url,
            'description': request.data['description'],
            'tags': request.data['tags'],
            'current_avatar': avatar,
            'repository': repo
        }

        env = Environment.objects.create(
            name=env_data['name'],
            url=env_data['url'],
            description=env_data['description'],
            repository=repo,
            tags=env_data['tags'],
            current_avatar=env_data['current_avatar']
        )

        serializer = EnvironmentWriteSerializer(env, data=env_data)

        if serializer.is_valid(raise_exception=True):
            if is_valid_uuid(request.data['topic']):
                logger.info('valid UUID for topic')
                env.topic= Topic.objects.get(id=request.data['topic'])
            env.save()

            return Response(serializer.data, status=201)
    
    def update(self, request, pk):
        env = get_object_or_404(Environment, pk=pk)
        env_name = request.data['name']
        env_url = re.sub(' {1,}', '-', env_name)

        env_data = {
            'name': env_name,
            'url': env_url,
            'description': request.data['description'],
            'tags': request.data['tags'],
        }

        if is_valid_uuid(request.data['topic']):
            logger.info('valid UUID for topic')
            env_data['topic'] = Topic.objects.get(id=request.data['topic'])
        else:
            env_data['topic'] = None

        serializer = EnvironmentFormSerializer(env, data=env_data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()

            # TODO I don't know why we have to do this outside the serializer
            if request.data['avatar'] is not None and is_valid_uuid(request.data['avatar']['id']):
                env.current_avatar = Image.objects.get(id=request.data['avatar']['id'])
            else:
                env.current_avatar = None

            env.save()

            return Response(serializer.data, status=200)

    @action(['GET'], detail=False)
    def filter(self, request):

        from django.db.models import Q

        search_terms = request.GET.get('search', '').split(',')
        if len(search_terms) == 0:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        for i, term in enumerate(search_terms):
            if i == 0:
                search_query = Q(name__icontains=term) | Q(tags__icontains=term) | Q(topic__name__icontains=term)
            else:
                search_query |= Q(name__icontains=term)
                search_query |= Q(tags__icontains=term)
                search_query |= Q(topic__name__icontains=term)
        logger.debug(search_query)

        environments = Environment.objects.filter(search_query).select_related('repository')

        serializer = EnvironmentSerializer(environments, many=True)
        data = serializer.data

        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(['GET'], detail=False)
    def filter_topic(self, request):
        from django.db.models import Q

        search_term = request.GET.get('topic', '')

        if len(search_term) == 0:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # here we look for both the parent topic and the child topic (UUID)
        search_query = Q(topic__exact=search_term) | Q(topic__parent_topic__exact=search_term)
        logger.debug(search_query)

        environments = Environment.objects.filter(search_query).select_related('repository')
        serializer = EnvironmentSerializer(environments, many=True)
        data = serializer.data

        return Response(serializer.data, status=status.HTTP_200_OK)
        
class TopicViewSet(viewsets.ModelViewSet):
    """
    View to create topics
    """

    queryset = Topic.objects.all()
    serializer_class = TopicSerializer
    permission_classes = (IsAdminOrReadOnly,)

    def create(self, request) -> Response:

        try:
            parent=Topic.objects.filter(name=request.data['parent_topic'])[0]
            topic = Topic.objects.create(
                name=request.data['name'],
                parent_topic=parent
            )
            topic.save()
            serializer = TopicSerializer(topic)
            return Response(serializer.data, status=201)
        except:
            response = super(TopicViewSet, self).create(request)
            return response
