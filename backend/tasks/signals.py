from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils import timezone
from django.db import models
from .models import Task


@receiver(pre_save, sender=Task)
def calculate_task_hours_on_complete(sender, instance, **kwargs):
    """Calculate `hours_consumed` for a Task when its status becomes COMPLETED.

    Uses the task `start_date` and the date when it was marked COMPLETED
    (today) to compute hours as (completion_date - start_date).days * 24.
    """
    # Only act when status is being set to COMPLETED
    if instance.status != 'COMPLETED':
        return

    # If creating new instance or status changed to COMPLETED, compute hours
    completion_date = timezone.localdate()

    # Ensure start_date exists
    if not instance.start_date:
        return

    days = (completion_date - instance.start_date).days
    if days < 0:
        days = 0
    hours = days * 24
    instance.hours_consumed = hours


@receiver(post_save, sender=Task)
def update_project_hours_on_task_change(sender, instance, **kwargs):
    """Whenever a Task is saved, recalculate its project's total hours_consumed."""
    project = instance.project
    if project is None:
        return

    total = project.tasks.aggregate(total=models.Sum('hours_consumed'))['total'] or 0
    # Only save if different to avoid unnecessary writes
    if project.hours_consumed != total:
        project.hours_consumed = total
        project.save(update_fields=['hours_consumed'])
