from django.db import models

class Image(models.Model):
    image = models.ImageField(upload_to='images/')    
    uploaded_at = models.DateTimeField(auto_now_add=True)
    embedding = models.JSONField(null=True, blank=True)
    is_generated = models.BooleanField(default=False)
    likes = models.PositiveIntegerField(default=0)


class Comment(models.Model):
    image = models.ForeignKey(Image, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)