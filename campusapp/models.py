from django.db import models


class PageVisit(models.Model):
    page = models.CharField(max_length=50, unique=True)
    count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"{self.page}: {self.count}"