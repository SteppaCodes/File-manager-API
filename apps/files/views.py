from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import File, Comment
from .serializers import FileSerializer, CommentSerializer, FileWithCommentsSerialzer
from utils.permissions import ISOwner

from django.utils.translation import gettext_lazy as _
from django.http import FileResponse
from django.shortcuts import get_object_or_404


class FileListCreateView(APIView):
    serializer_class = FileSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print(request.scheme, "scheme")
        user = request.user
        files = File.objects.filter(owner=user)
       
        if files:
            serializer = self.serializer_class(files, many=True, context={"request":request})
            return Response({"data":serializer.data}, status=status.HTTP_200_OK)
        else:
            return Response(_("You do not have any files"))
    
    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request":request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        serializer.save(owner=user)
        return Response({"data":serializer.data}, status=status.HTTP_201_CREATED)
        

class FileUpdateDestroyView(APIView):
    serializer_class = FileSerializer
    permission_classes = [IsAuthenticated]
    
    def put(self, request, id):
        file = File.objects.get(id=id)
        serializer = self.serializer_class(file, data=request.data, context={"request":request})
        serializer.is_valid()
        serializer.save()
        return Response({"Success":"file update succesflly",
                        "data":serializer.data})

    def delete(self, request, id):
        file = File.objects.get(id=id)
        file.delete()

        return Response({"success":"file deleted succesfully"})


class DownloadFileAPIView(APIView):
    
    def get(self, request, file_id):
        try:
            file = File.objects.get(id=file_id)
        except File.DoesNotExist:
            return Response({"error": "File not found"}, status=status.HTTP_404_NOT_FOUND)
        
        file_path = file.file.path

        # Use FileResponse to handle the file download
        response = FileResponse(open(file_path, 'rb'))
        response['Content-Disposition'] = f'attachment; filename="{file.file.name}"'
        return response


class CommentOnFile(APIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        owner=request.user
        file = get_object_or_404(File, id=id)

        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(file=file, owner=owner)

        return Response({"data":serializer.data}, status=status.HTTP_201_CREATED)


class GetFileComments(APIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, ISOwner]

    def get(self, request, id):
        file = File.objects.prefetch_related('comments').get(id=id)

        serializer = FileWithCommentsSerialzer(file)
        return Response({"data":serializer.data})
    
    def put(self, request, id):
        comment = Comment.objects.get(id=id)
        serializer = self.serializer_class(comment, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"data":serializer.data})
    
    def delete(self, request, id):
        comment = Comment.objects.get(id=id)
        if request.user == comment.owner or request.user == comment.file.owner:
            comment.delete()
            return Response({"success":"comment deleted succesfully"})
        return Response({"eroor":"you do not have the permission to delete this comment"})
    


