
from django.shortcuts import render
from rest_framework.views import APIView
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password ,check_password 
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.decorators import api_view ,permission_classes
from rest_framework.response import Response
from .serializers import CustomUserSerializer ,QuestionSerializer , AnswersSerializer, CategorySerializer
from rest_framework.permissions import IsAuthenticated ,AllowAny
from .models import CustomUser , Question , Answers, Category
from django.contrib.auth import authenticate
from .token_utils import get_user_id_from_token
from rest_framework import generics, permissions
# Create your views here.

#-----view for showing all available api end points-----
@api_view(['GET'])
def apiOverview(request):
	api_urls = {
		'List of Users'         :    '/users-list/',
		'User Details'          :    'get_user/<uuid:uid>/',
		'Create User'           :    '/signup/',
		'Update User'           :    '/user-update/',
        'Update User By Admin'  :    '',
		'Delete All User'       :    '/alluser-delete/<str:pk>/',
        'Delete Specific User'  :    '/specific_user-delete/',
        'Create Questions'      :    '/create-question/',
        'View all Ques'         :    '/question-list/',
        'View the Ans'          :    '/answersForQueston/<str:pk>',
        'Delete Ques'           :    '/question-delete/',
        'Write Ans'             :    '/write-answer/',
        'Delete Ans'            :    '/answer-delete/',
        'Referesh Token'        :    '/refresh-token/'

		}

	return Response(api_urls)



#-----view to get user details-----
@api_view(['GET'])
def getUsers_details(request):
	user_details = CustomUser.objects.all()
	serializer = CustomUserSerializer(user_details, many=True) #serialize the data from django model format to JSON
	return Response(serializer.data)





@api_view(['GET'])
def get_user(request, uid):
    try:
        user = CustomUser.objects.get(U_id=uid)
    except CustomUser.DoesNotExist:
        return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    serializer = CustomUserSerializer(user)
    return Response(serializer.data, status=status.HTTP_200_OK)





@api_view(['PATCH'])
def update_user_by_Admin(request, uid):
    user_id = get_user_id_from_token(request)
    ins = CustomUser.objects.get(U_id=user_id)
    if ins.userType == 'admin':
        try:
            user = CustomUser.objects.get(U_id=uid)
        
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        
        deserializer = CustomUserSerializer(user)
        if deserializer.is_valid():
            deserializer.save()
            return Response(deserializer.data, status=status.HTTP_200_OK)
        else:
            return Response(deserializer.errors, status=400)
    
    else:
        return  Response({'error' : "you are not allowed to edit user deatails"}, status=401)









#-----view to POST user details (registration)-----
@api_view(['POST'])
def user_create(request):
    deserializer = CustomUserSerializer(data=request.data)
    print(deserializer)
    utype = request.data.get('age')
    print(utype)
    
    if deserializer.is_valid():
        print('flag3')
        user = deserializer.save()  # Save the user instance
        refresh = RefreshToken.for_user(user)
        data2= deserializer.data
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user':data2
        }
        return Response(data, status=status.HTTP_201_CREATED)
    else:
        print(deserializer.errors)

    return Response(deserializer.errors, status=status.HTTP_400_BAD_REQUEST)




#-----view to post username and password (login)-----
@api_view(['POST'])
@permission_classes([AllowAny])
def custom_user_login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    # Ensure both username and password are provided
    if not username or not password:
        return Response({'error': 'Both username and password are required'}, status=status.HTTP_400_BAD_REQUEST)

    # Retrieve the user by username
    user = CustomUser.objects.filter(userName__iexact=username).first()
    
    if user and (str(password) == str(user.password)):
        # Password is correct
        # deserialize the user data(converting JSON into django models )
        
        deserializer = CustomUserSerializer(user)
        refresh = RefreshToken.for_user(user)
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
      
        return Response({
            'Token':data,
            'user': deserializer.data,
            'api_status':True
        })
    else:
        # Invalid username or password
        return Response({'error': 'Invalid username or password'}, status=status.HTTP_401_UNAUTHORIZED)




#-----view to PATCH, amend the user details-----
@api_view(['PATCH'])
def userDetail_Update(request):
        user_id = get_user_id_from_token(request)
        
        if user_id is not None:
                try:
                    task = CustomUser.objects.get(U_id=user_id)
                except CustomUser.DoesNotExist:
                      return Response({"error": "Task not found for the current user"}, status=404)
                deserializer = CustomUserSerializer(instance=task, data=request.data, partial=True)

                if deserializer.is_valid():
                    deserializer.save()
                    return Response(deserializer.data)
                else:
                    return Response(deserializer.errors, status=400)

        else:
            return  Response({"error": "Authorization token not valid"}, status=401) 



#-----view to DELETE all custom user-----
@api_view(['DELETE'])
def delete_all_custom_users(request):
    try:
        CustomUser.objects.all().delete()
        return Response({'message': 'All CustomUser rows deleted successfully'})
    except Exception as e:
        return Response({'error': f'An error occurred: {str(e)}'}, status=500)







#------view to DELETE users using user_id-------
@api_view(['DELETE'])
def delete_specific_users(request):
    user_id = get_user_id_from_token(request)
    if user_id is not None:
        # Retrieve user instance based on user ID
        try:
            user = CustomUser.objects.get(U_id=user_id)
            user.delete()

            return Response({"status": True, "message": f"User with id {user_id} deleted successfully"
            }, status=status.HTTP_204_NO_CONTENT)

        except CustomUser.DoesNotExist:
            return Response({"error": "user not found"}, status=status.HTTP_404_NOT_FOUND)

    else:
        return Response({"error": "Authentication token not valid"}, status=status.HTTP_401_UNAUTHORIZED)
    



#----------view to referesh token-----------
@api_view(['POST'])
def refresh_token(request):
    refresh_token = request.data.get('refresh_token')

    if not refresh_token:
        return Response({'error': 'Refresh token not provided'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        refresh_token = RefreshToken(refresh_token)
        access_token = str(refresh_token.access_token)

        return Response({'access_token': access_token}, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'Unable to refresh token: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)    








#-----view to create questions-----
@api_view(['POST'])
def create_question(request):
    # Get user ID from token
    user_id = get_user_id_from_token(request)
    print(user_id)

    if user_id is not None:
        # Retrieve user instance based on user ID
        try:
            user = CustomUser.objects.get(U_id=user_id)
            print(user)

        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # Create a new question with user association
        request.data['U_id'] = user_id
        print("flag1")
        deserializer = QuestionSerializer(data=request.data)
        print("flag2")
        if deserializer.is_valid():
            print("flag3")
            # serializer.validated_data['user'] = user  # Associate the question with the user
            deserializer.save()
            print("flag4")
            return Response(deserializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(deserializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"error": "Authentication token not valid"}, status=status.HTTP_401_UNAUTHORIZED)




#-----view to GET all questions available-----
# get all questions 
@api_view(['GET'])
def getQuestion(request):
    question = Question.objects.all()
    print(question.query)
    serializer = QuestionSerializer(question, many=True)
    print(serializer)

    return Response(serializer.data)




#-----view to POST answer of the existing question----- 
@api_view(['POST'])
def answer_question(request):
    # Get user ID from token
    user_id = get_user_id_from_token(request)

    if user_id is not None:
        # Retrieve user instance based on user ID
        try:
            user = CustomUser.objects.get(U_id=user_id)
            # print(user,"jdnsdnsdk")
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        # Create a new question with user association
        request.data['U_id'] = user_id
        deserializer = AnswersSerializer(data=request.data)
        if deserializer.is_valid():
            # serializer.validated_data['user'] = user  # Associate the question with the user
            deserializer.save()

            return Response(deserializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(deserializer.errors, status=status.HTTP_400_BAD_REQUEST)
    else:
        return Response({"error": "Authentication token not valid"}, status=status.HTTP_401_UNAUTHORIZED)
    



#-----view to GET the anwers of the questions----- 
@api_view(['GET'])
def getAnswersForQuestion(request):

    # Assuming Q_id is present in the request data
    q_id = request.data.get('Q_id')

    if q_id is not None:
        # Use filter to get answers for a specific question
        answers = Answers.objects.filter(Q_id=q_id)
        count_of_ans = answers.count()
        serializer = AnswersSerializer(answers, many=True)
        data = {
            'count_of_anser' :  count_of_ans,
            'data': serializer.data ,
            'message' : 'answers for question',
            'api_status' : 200
        }
        return Response(data)
    else:
        return Response({"error": "Q_id is required in the request data"}, status=status.HTTP_400_BAD_REQUEST)
    



# --------------view to DELETE question-------------------
@api_view(['DELETE'])
def deleteQuestion(request):
    user_id = get_user_id_from_token(request)
    if user_id is not None:
        # Retrieve user instance based on user ID
        Q_id = request.data.get('Q_id')
        try:
            question = Question.objects.get(Q_id=Q_id)
            if str(user_id) == str(question.U_id):    # note  convert  <class 'restAPI.models.CustomUser'> = question.user_id  in to string 
                return Response({"error": "You do not have permission to delete this question.",
                "userids" :f"user->{type(user_id)} questio {type(question.U_id)}"
                }, status=status.HTTP_403_FORBIDDEN)

            # Delete the question
            question.delete()

            return Response({"message": f"Question with id {Q_id} deleted successfully"
            "userids"
            }, status=status.HTTP_204_NO_CONTENT)

        except Question.DoesNotExist:
            return Response({"error": "Question not found"}, status=status.HTTP_404_NOT_FOUND)

    else:
        return Response({"error": "Authentication token not valid"}, status=status.HTTP_401_UNAUTHORIZED)




#--------------------view to DELETE answer-------------------
@api_view(['DELETE'])
def deleteAnswer(request):
    user_id = get_user_id_from_token(request)
    if user_id is not None:
        # Retrieve user instance based on user ID
        A_id = request.data.get('A_id')
        try:
            answer = Answers.objects.get(A_id=A_id)
            if str(user_id) == str(answer.U_id):    # note  convert  <class 'restAPI.models.CustomUser'> = question.user_id  in to string 
                return Response({"error": "You do not have permission to delete this question.",
                "userids" :f"user->{type(user_id)} questio {type(answer.U_id)}"
                }, status=status.HTTP_403_FORBIDDEN)

            # Delete the answer
            answer.delete()

            return Response({"message": f"Answer with id {A_id} deleted successfully"
            "userids"
            }, status=status.HTTP_204_NO_CONTENT)

        except Answers.DoesNotExist:
            return Response({"error": "Answer not found"}, status=status.HTTP_404_NOT_FOUND)

    else:
        return Response({"error": "Authentication token not valid"}, status=status.HTTP_401_UNAUTHORIZED)




@api_view(['POST'])
# @permission_classes([permissions.IsAuthenticated])  # Adjust permissions as needed
def create_category_from_json(request):
    user_id = get_user_id_from_token(request)
    if user_id is not None:
        data = request.data
        
        # Ensure the JSON data is a list of dictionaries
        if not isinstance(data, list):
            return Response({'error': 'Invalid JSON data. Expecting a list of dictionaries.'}, status=status.HTTP_400_BAD_REQUEST)
        
        created_categories = []
        for category_data in data:
            serializer = CategorySerializer(data=category_data)
            if serializer.is_valid():
                serializer.save()
                created_categories.append(serializer.data)
            else:
                return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    

    return Response({'message': 'Categories created successfully', 'categories': created_categories}, status=status.HTTP_201_CREATED)