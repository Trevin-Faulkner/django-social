from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    ROLE_CLIENT = 'client'
    ROLE_DEVELOPER = 'developer'
    ROLE_CHOICES = [
        (ROLE_CLIENT, 'Client'),
        (ROLE_DEVELOPER, 'Developer'),
    ]

    PLAN_FREE = 'free'
    PLAN_PLUS = 'plus'
    PLAN_PRO = 'pro'
    PLAN_CHOICES = [
        (PLAN_FREE, 'Free'),
        (PLAN_PLUS, 'Plus'),
        (PLAN_PRO, 'Pro'),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    headline = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    skills = models.TextField(blank=True, help_text="Comma-separated list of skills")
    goals = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    membership_plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default=PLAN_FREE)
    profile_views = models.PositiveIntegerField(default=0)
    REQUIRED_FIELDS = ['email', 'role']

    @property
    def connection_limit(self):
        limits = {
            self.PLAN_FREE: 2,
            self.PLAN_PLUS: 5,
            self.PLAN_PRO: None,
        }
        return limits.get(self.membership_plan)

    @property
    def remaining_connections_today(self):
        limit = self.connection_limit
        if limit is None:
            return None
        today = timezone.now().date()
        used = Connection.objects.filter(requester=self, created_at__date=today).count()
        return max(limit - used, 0)

    def active_connections_count(self):
        return Connection.objects.filter(
            (models.Q(requester=self) | models.Q(receiver=self)),
            status=Connection.STATUS_ACCEPTED,
        ).count()

    def skills_list(self):
        return [skill.strip() for skill in self.skills.split(',') if skill.strip()]


class Experience(models.Model):
    user = models.ForeignKey(User, related_name='experiences', on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    company = models.CharField(max_length=255)
    start_year = models.PositiveIntegerField()
    end_year = models.PositiveIntegerField(null=True, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['-start_year']

    def __str__(self):
        end = self.end_year or 'Present'
        return f"{self.title} at {self.company} ({self.start_year} - {end})"


class Connection(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_ACCEPTED = 'accepted'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
    ]

    requester = models.ForeignKey(User, related_name='sent_connections', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_connections', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    accepted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('requester', 'receiver')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.requester} -> {self.receiver} ({self.status})"


class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation #{self.pk}"

    def other_participant(self, user):
        return self.participants.exclude(id=user.id).first()


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, related_name='messages', on_delete=models.CASCADE)
    sender = models.ForeignKey(User, related_name='messages_sent', on_delete=models.CASCADE)
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message from {self.sender} in conversation {self.conversation_id}"
