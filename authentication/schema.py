"""
GraphQL API Schema Documentation

Types:
- CoachingSessionType: Represents a coaching session (fields: id, prompt, response, user, tags, createdAt).
- TagType: Represents a tag (fields: id, name).
- UserType: Represents a user (fields: id, username, email).

Queries:
- coachingSessions: List all coaching sessions (admin/global, supports filters: past, tag, search, dateGte, dateLte, pagination).
- mySessions: List all sessions for the logged-in user (fields: id, prompt, response, createdAt, tags).
- session(id: ID!): View a single session by ID (must belong to the user).
- sessionsByTag(tagName: String!): List all sessions for the user filtered by tag name.
- tags: List all tags.
- user(id: Int!): Get a user by ID.
- me: Get the currently authenticated user.

Mutations:
- tokenAuth(username, password): Obtain a JWT token.
- verifyToken(token): Verify a JWT token.
- askCoach(question, tagNames): Ask a question, get an AI response, and save the session (returns response and sessionId).
- askOpenrouter(prompt, tagNames): Same as askCoach, but with a generic prompt field.
- registerUser(username, password, email, firstName, lastName): Register a new user.

Example Queries:

# List your sessions
query {
  mySessions {
    id
    prompt
    response
    createdAt
    tags { name }
  }
}

# View a single session
query {
  session(id: "1") {
    prompt
    response
    createdAt
    tags { name }
  }
}

# Filter sessions by tag
query {
  sessionsByTag(tagName: "productivity") {
    prompt
    response
    tags { name }
  }
}

# List all tags
query {
  tags {
    id
    name
  }
}

Example Mutations:

# Ask a question and save the session
mutation {
  askCoach(question: "How do I improve focus?", tagNames: ["productivity"]) {
    response
    sessionId
  }
}

# Ask Openrouter
mutation {
  askOpenrouter(prompt: "What is AI?", tagNames: ["technology"]) {
    response
    sessionId
  }
}

# Register a new user
mutation {
  registerUser(username: "newuser", password: "securepassword", email: "user@example.com", firstName: "New", lastName: "User") {
    user {
      id
      username
      email
    }
    success
    errors
  }
}
"""

import graphene
from graphene_django import DjangoObjectType
from coaching.models import CoachingSession, Tag
from .models import User
from graphql_jwt.shortcuts import get_token
import graphql_jwt
import django_filters
from graphene_django.filter import DjangoFilterConnectionField
from .service import ask_openrouter



class CoachingSessionFilter(django_filters.FilterSet):
    past = django_filters.BooleanFilter(method='filter_past')
    tag = django_filters.CharFilter(field_name='tags__name', lookup_expr='iexact')
    search = django_filters.CharFilter(method='filter_search')
    date_gte = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_lte = django_filters.DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = CoachingSession
        fields = ['past', 'tag', 'search', 'date_gte', 'date_lte']

    def filter_past(self, queryset, name, value):
        from django.utils import timezone
        now = timezone.now()
        if value:
            return queryset.filter(date__lt=now)
        else:
            return queryset.filter(date__gte=now)

    def filter_search(self, queryset, name, value):
        return queryset.filter(title__icontains=value)
class CoachingSessionNode(DjangoObjectType):
    class Meta:
        model = CoachingSession
        filterset_class = CoachingSessionFilter
        interfaces = (graphene.relay.Node,)

# Types
class CoachingSessionType(DjangoObjectType):
    class Meta:
        model = CoachingSession
        fields = "__all__"

class TagType(DjangoObjectType):
    class Meta:
        model = Tag
        fields = "__all__"

class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = "__all__"

# Queries
class Query(graphene.ObjectType):
    coaching_sessions = DjangoFilterConnectionField(CoachingSessionNode)
    tags = graphene.List(TagType)
    user = graphene.Field(UserType, id=graphene.Int(required=True))
    me = graphene.Field(UserType)
    my_sessions = graphene.List(CoachingSessionType)
    session = graphene.Field(CoachingSessionType, id=graphene.ID(required=True))
    sessions_by_tag = graphene.List(CoachingSessionType, tag_name=graphene.String(required=True))

    def resolve_tags(root, info):
        return Tag.objects.all()

    def resolve_user(root, info, id):
        return User.objects.get(pk=id)

    def resolve_me(root, info):
        user: User = info.context.user

        print(f"Resolving 'me' for user: {user.first_name} {user.last_name} (ID: {user.id})")
        if user.is_authenticated:
            return user
        return None

    # Fetch sessions for the logged-in user
    def resolve_coaching_sessions(self, info, **kwargs):
        user = info.context.user
        qs = CoachingSession.objects.all()
        if kwargs.get('me_only') and user.is_authenticated:
            qs = qs.filter(user=user)
        return qs

    def resolve_my_sessions(self, info):
        user = info.context.user
        if not user.is_authenticated:
            return CoachingSession.objects.none()
        return CoachingSession.objects.filter(user=user).order_by('-created_at')

    def resolve_session(self, info, id):
        user = info.context.user
        try:
            session = CoachingSession.objects.get(id=id, user=user)
            return session
        except CoachingSession.DoesNotExist:
            return None

    def resolve_sessions_by_tag(self, info, tag_name):
        user = info.context.user
        if not user.is_authenticated:
            return CoachingSession.objects.none()
        return CoachingSession.objects.filter(user=user, tags__name__iexact=tag_name).order_by('-created_at')

# Custom Mutation Example
class AskCoach(graphene.Mutation):
    class Arguments:
        question = graphene.String(required=True)
        tag_names = graphene.List(graphene.String, required=False)

    response = graphene.String()
    session_id = graphene.ID()

    def mutate(self, info, question, tag_names=None):
        user = info.context.user
        from .service import ask_openrouter
        from coaching.models import CoachingSession, Tag
        # Call AI service
        ai_response = ask_openrouter(question)
        # Create or get tags
        tags = []
        if tag_names:
            for name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=name)
                tags.append(tag)
        # Save CoachingSession
        session = CoachingSession.objects.create(
            user=user if user.is_authenticated else None,
            prompt=question,
            response=ai_response
        )
        if tags:
            session.tags.set(tags)
        return AskCoach(response=ai_response, session_id=session.id)

class AskOpenrouter(graphene.Mutation):
    class Arguments:
        prompt = graphene.String(required=True)
        tag_names = graphene.List(graphene.String, required=False)

    response = graphene.String()
    session_id = graphene.ID()

    def mutate(self, info, prompt, tag_names=None):
        user = info.context.user
        from .service import ask_openrouter
        from coaching.models import CoachingSession, Tag
        # Call AI service
        ai_response = ask_openrouter(prompt)
        # Create or get tags
        tags = []
        if tag_names:
            for name in tag_names:
                tag, _ = Tag.objects.get_or_create(name=name)
                tags.append(tag)
        # Save CoachingSession
        session = CoachingSession.objects.create(
            user=user if user.is_authenticated else None,
            prompt=prompt,
            response=ai_response
        )
        if tags:
            session.tags.set(tags)
        return AskOpenrouter(response=ai_response, session_id=session.id)

class RegisterUser(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)
        email = graphene.String(required=True)
        first_name = graphene.String(required=False)
        last_name = graphene.String(required=False)

    user = graphene.Field(UserType)
    success = graphene.Boolean()
    errors = graphene.List(graphene.String)

    def mutate(self, info, username, password, email, first_name=None, last_name=None):
        from .models import User
        errors = []
        if User.objects.filter(username=username).exists():
            errors.append("Username already exists.")
        if User.objects.filter(email=email).exists():
            errors.append("Email already exists.")
        if errors:
            return RegisterUser(success=False, errors=errors)
        user = User(
            username=username,
            email=email,
            first_name=first_name or "",
            last_name=last_name or ""
        )

        

        user.set_password(password)
        user.save()
        return RegisterUser(user=user, success=True, errors=None)

# Mutations
class Mutation(graphene.ObjectType):
    token_auth: graphene.Field = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token: graphene.Field = graphql_jwt.Verify.Field()
    ask_coach: graphene.Field = AskCoach.Field()
    ask_openrouter: graphene.Field = AskOpenrouter.Field()
    register_user: graphene.Field = RegisterUser.Field()

schema: graphene.Schema = graphene.Schema(query=Query, mutation=Mutation)
